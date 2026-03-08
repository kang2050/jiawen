"""
3D Pose Estimator for Animals
===============================
Lifts 2D keypoints to 3D using SMAL parametric model fitting.
Inspired by SMALify and adapted for the Video2Pet pipeline.

The SMAL (Skinned Multi-Animal Linear) model is a parametric 3D model
for quadruped animals, similar to SMPL for humans.
"""

from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()


class SMALModel(nn.Module):
    """Simplified SMAL parametric animal model.

    Parameters:
        - pose: (N_joints, 3) axis-angle rotations for each joint
        - shape: (N_betas,) shape coefficients
        - trans: (3,) global translation

    This is a simplified version. For full SMAL support,
    use the third_party/SMALify submodule.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        n_betas: int = 20,
        n_joints: int = 35,
        device: str = "cpu",
    ):
        super().__init__()
        self.n_betas = n_betas
        self.n_joints = n_joints
        self.device = device

        # Initialize parameters
        self.pose = nn.Parameter(torch.zeros(1, n_joints, 3, device=device))
        self.betas = nn.Parameter(torch.zeros(1, n_betas, device=device))
        self.trans = nn.Parameter(torch.zeros(1, 3, device=device))
        self.scale = nn.Parameter(torch.ones(1, device=device))

        # Load pre-trained model if available
        if model_path and Path(model_path).exists():
            self._load_model(model_path)
        else:
            console.print(
                "[yellow]SMAL model not found. Using simplified parametric model.[/yellow]"
            )
            self._init_default_template()

    def _init_default_template(self):
        """Initialize a default quadruped template."""
        # Default vertex template for a generic quadruped
        # In practice, this would be loaded from the SMAL model file
        n_verts = 3889  # SMAL default
        self.register_buffer(
            "v_template", torch.zeros(1, n_verts, 3, device=self.device)
        )
        self.register_buffer(
            "shapedirs", torch.zeros(n_verts, 3, self.n_betas, device=self.device)
        )
        self.register_buffer(
            "J_regressor", torch.zeros(self.n_joints, n_verts, device=self.device)
        )

    def _load_model(self, model_path: str):
        """Load SMAL model from pickle file."""
        import pickle

        console.print(f"[cyan]Loading SMAL model from {model_path}[/cyan]")
        with open(model_path, "rb") as f:
            model_data = pickle.load(f, encoding="latin1")

        # Extract model components
        v_template = torch.tensor(model_data["v_template"], dtype=torch.float32, device=self.device)
        self.register_buffer("v_template", v_template.unsqueeze(0))

        if "shapedirs" in model_data:
            shapedirs = torch.tensor(
                np.array(model_data["shapedirs"]), dtype=torch.float32, device=self.device
            )
            self.register_buffer("shapedirs", shapedirs)

        if "J_regressor" in model_data:
            J_regressor = torch.tensor(
                np.array(model_data["J_regressor"].todense()),
                dtype=torch.float32,
                device=self.device,
            )
            self.register_buffer("J_regressor", J_regressor)

        console.print("[green]SMAL model loaded successfully[/green]")

    def forward(self):
        """Forward pass: compute vertices and joints from parameters."""
        # Shape blend shapes
        v_shaped = self.v_template
        if hasattr(self, "shapedirs") and self.shapedirs.numel() > 0:
            v_shaped = v_shaped + torch.einsum(
                "vdb,nb->nvd", self.shapedirs[:, :, : self.n_betas], self.betas
            )

        # Get joint locations
        if hasattr(self, "J_regressor") and self.J_regressor.numel() > 0:
            joints = torch.einsum("jv,nvd->njd", self.J_regressor, v_shaped)
        else:
            joints = torch.zeros(1, self.n_joints, 3, device=self.device)

        # Apply global transformation
        vertices = v_shaped * self.scale.unsqueeze(-1).unsqueeze(-1) + self.trans.unsqueeze(1)
        joints = joints * self.scale.unsqueeze(-1).unsqueeze(-1) + self.trans.unsqueeze(1)

        return vertices, joints


class PoseEstimator3D:
    """Estimate 3D animal pose from 2D keypoint detections.

    Uses optimization-based fitting of SMAL model to 2D observations.
    """

    def __init__(self, config):
        self.config = config
        self.device = config.device if config.device != "mps" else "cpu"  # SMAL ops on CPU
        self.smal_model_path = config.pose.smal_model_path

    def estimate_sequence(self, detections: list[dict]) -> list[dict]:
        """Estimate 3D pose for a sequence of 2D detections.

        Args:
            detections: List of detection dicts with 'keypoints' and 'bbox'

        Returns:
            List of 3D pose results with SMAL parameters
        """
        console.print("[cyan]Estimating 3D poses from 2D detections...[/cyan]")

        results = []
        valid_detections = [d for d in detections if d.get("keypoints") is not None]

        if not valid_detections:
            console.print("[red]No valid detections for 3D estimation[/red]")
            return results

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
        ) as progress:
            task = progress.add_task("Fitting 3D model...", total=len(valid_detections))

            # Initialize SMAL model
            smal = SMALModel(
                model_path=self.smal_model_path,
                device=self.device,
            )

            for det in valid_detections:
                result = self._fit_single_frame(smal, det)
                results.append(result)
                progress.update(task, advance=1)

        console.print(f"[green]3D pose estimated for {len(results)} frames[/green]")
        return results

    def _fit_single_frame(self, smal: SMALModel, detection: dict) -> dict:
        """Fit SMAL model to a single frame's 2D keypoints."""
        keypoints_2d = torch.tensor(
            detection["keypoints"], dtype=torch.float32, device=self.device
        )

        # Reset parameters for this frame
        smal.pose.data.zero_()
        smal.betas.data.zero_()
        smal.trans.data.zero_()
        smal.scale.data.fill_(1.0)

        # Optimization
        optimizer = optim.Adam(
            [smal.pose, smal.betas, smal.trans, smal.scale],
            lr=0.01,
        )

        n_iters = 200
        best_loss = float("inf")
        best_params = None

        for i in range(n_iters):
            optimizer.zero_grad()

            vertices, joints_3d = smal()

            # Project 3D joints to 2D (orthographic projection)
            joints_2d_proj = joints_3d[0, :, :2]  # Simple orthographic

            # Keypoint reprojection loss
            valid_mask = keypoints_2d[:, 2] > 0.1  # confidence > threshold
            if valid_mask.sum() > 0:
                kp_target = keypoints_2d[valid_mask, :2]
                kp_pred = joints_2d_proj[:len(keypoints_2d)][valid_mask]

                # Normalize to same scale
                if kp_target.numel() > 0 and kp_pred.numel() > 0:
                    target_center = kp_target.mean(0)
                    pred_center = kp_pred.mean(0)
                    target_scale = (kp_target - target_center).norm(dim=1).mean() + 1e-6
                    pred_scale = (kp_pred - pred_center).norm(dim=1).mean() + 1e-6

                    kp_target_norm = (kp_target - target_center) / target_scale
                    kp_pred_norm = (kp_pred - pred_center) / pred_scale

                    loss_kp = ((kp_target_norm - kp_pred_norm) ** 2).sum()
                else:
                    loss_kp = torch.tensor(0.0, device=self.device)
            else:
                loss_kp = torch.tensor(0.0, device=self.device)

            # Regularization losses
            loss_pose = (smal.pose ** 2).sum() * 0.01
            loss_shape = (smal.betas ** 2).sum() * 0.01

            loss = loss_kp + loss_pose + loss_shape
            loss.backward()
            optimizer.step()

            if loss.item() < best_loss:
                best_loss = loss.item()
                best_params = {
                    "pose": smal.pose.data.clone().cpu().numpy(),
                    "betas": smal.betas.data.clone().cpu().numpy(),
                    "trans": smal.trans.data.clone().cpu().numpy(),
                    "scale": smal.scale.data.clone().cpu().numpy(),
                }

        # Get final 3D joints
        with torch.no_grad():
            vertices, joints_3d = smal()

        return {
            "frame": detection["frame"],
            "params": best_params,
            "joints_3d": joints_3d[0].cpu().numpy(),
            "vertices": vertices[0].cpu().numpy(),
            "loss": best_loss,
        }

    def smooth_sequence(self, results: list[dict], window: int = 5) -> list[dict]:
        """Temporal smoothing of 3D pose sequence."""
        if len(results) < window:
            return results

        console.print("[cyan]Smoothing 3D pose sequence...[/cyan]")

        # Extract joint positions
        all_joints = np.array([r["joints_3d"] for r in results])

        # Apply Gaussian smoothing
        from scipy.ndimage import gaussian_filter1d

        smoothed_joints = gaussian_filter1d(all_joints, sigma=1.0, axis=0)

        for i, result in enumerate(results):
            result["joints_3d_smooth"] = smoothed_joints[i]

        console.print("[green]Sequence smoothed[/green]")
        return results
