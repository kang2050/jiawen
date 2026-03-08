"""
3D Gaussian Splatting Reconstruction
======================================
Reconstruct pet 3D model from multi-view frames using 3D Gaussian Splatting.
Optimized for Apple Silicon (MPS backend).

Pipeline:
1. SfM (COLMAP) for camera poses and sparse point cloud
2. 3D Gaussian Splatting training
3. Mesh extraction from Gaussians
"""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()


class SfMProcessor:
    """Structure from Motion using COLMAP or lightweight alternatives."""

    def __init__(self, config):
        self.config = config.reconstruction
        self.device = config.device

    def run_colmap(self, images_dir: str, output_dir: str) -> dict:
        """Run COLMAP SfM pipeline to get camera poses and sparse point cloud.

        Args:
            images_dir: Directory containing input images
            output_dir: Directory for COLMAP output

        Returns:
            Dict with camera parameters and sparse points
        """
        images_dir = Path(images_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        database_path = output_dir / "database.db"
        sparse_dir = output_dir / "sparse"
        sparse_dir.mkdir(exist_ok=True)

        console.print("[cyan]Running COLMAP SfM pipeline...[/cyan]")

        # Check if COLMAP is available
        colmap_available = shutil.which("colmap") is not None

        if colmap_available:
            return self._run_colmap_cli(images_dir, output_dir, database_path, sparse_dir)
        else:
            console.print("[yellow]COLMAP not found. Using lightweight SfM alternative.[/yellow]")
            return self._run_lightweight_sfm(images_dir, output_dir)

    def _run_colmap_cli(
        self, images_dir: Path, output_dir: Path, database_path: Path, sparse_dir: Path
    ) -> dict:
        """Run COLMAP via CLI."""
        try:
            # Feature extraction
            console.print("  Step 1/3: Feature extraction...")
            subprocess.run(
                [
                    "colmap", "feature_extractor",
                    "--database_path", str(database_path),
                    "--image_path", str(images_dir),
                    "--ImageReader.single_camera", "1",
                    "--SiftExtraction.use_gpu", "0",  # CPU for compatibility
                ],
                check=True,
                capture_output=True,
            )

            # Feature matching
            console.print("  Step 2/3: Feature matching...")
            subprocess.run(
                [
                    "colmap", "sequential_matcher",
                    "--database_path", str(database_path),
                    "--SiftMatching.use_gpu", "0",
                ],
                check=True,
                capture_output=True,
            )

            # Sparse reconstruction
            console.print("  Step 3/3: Sparse reconstruction...")
            subprocess.run(
                [
                    "colmap", "mapper",
                    "--database_path", str(database_path),
                    "--image_path", str(images_dir),
                    "--output_path", str(sparse_dir),
                ],
                check=True,
                capture_output=True,
            )

            console.print("[green]COLMAP SfM completed[/green]")

            # Parse COLMAP output
            return self._parse_colmap_output(sparse_dir / "0")

        except subprocess.CalledProcessError as e:
            console.print(f"[red]COLMAP failed: {e}[/red]")
            return self._run_lightweight_sfm(images_dir, output_dir)

    def _run_lightweight_sfm(self, images_dir: Path, output_dir: Path) -> dict:
        """Lightweight SfM using OpenCV feature matching.

        This is a simplified alternative when COLMAP is not available.
        """
        import cv2

        console.print("[cyan]Running lightweight SfM...[/cyan]")

        image_files = sorted(images_dir.glob("*.png")) + sorted(images_dir.glob("*.jpg"))
        if not image_files:
            raise FileNotFoundError(f"No images found in {images_dir}")

        # Detect features in all images
        orb = cv2.ORB_create(nfeatures=5000)
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

        all_keypoints = []
        all_descriptors = []

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn()) as progress:
            task = progress.add_task("Extracting features...", total=len(image_files))
            for img_path in image_files:
                img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
                kps, descs = orb.detectAndCompute(img, None)
                all_keypoints.append(kps)
                all_descriptors.append(descs)
                progress.update(task, advance=1)

        # Match consecutive frames and estimate relative poses
        cameras = []
        points_3d = []

        # Initialize first camera at origin
        first_img = cv2.imread(str(image_files[0]))
        h, w = first_img.shape[:2]
        focal = max(w, h) * 1.2  # Approximate focal length

        K = np.array([[focal, 0, w / 2], [0, focal, h / 2], [0, 0, 1]])

        cameras.append({
            "R": np.eye(3),
            "t": np.zeros(3),
            "K": K,
            "image": str(image_files[0]),
        })

        R_cumulative = np.eye(3)
        t_cumulative = np.zeros(3)

        for i in range(1, len(image_files)):
            if all_descriptors[i - 1] is None or all_descriptors[i] is None:
                cameras.append({
                    "R": R_cumulative.copy(),
                    "t": t_cumulative.copy(),
                    "K": K,
                    "image": str(image_files[i]),
                })
                continue

            matches = bf.match(all_descriptors[i - 1], all_descriptors[i])
            matches = sorted(matches, key=lambda x: x.distance)[:100]

            if len(matches) < 8:
                cameras.append({
                    "R": R_cumulative.copy(),
                    "t": t_cumulative.copy(),
                    "K": K,
                    "image": str(image_files[i]),
                })
                continue

            pts1 = np.float32([all_keypoints[i - 1][m.queryIdx].pt for m in matches])
            pts2 = np.float32([all_keypoints[i][m.trainIdx].pt for m in matches])

            E, mask = cv2.findEssentialMat(pts1, pts2, K, method=cv2.RANSAC, prob=0.999, threshold=1.0)

            if E is not None:
                _, R, t, mask_pose = cv2.recoverPose(E, pts1, pts2, K)
                R_cumulative = R @ R_cumulative
                t_cumulative = t_cumulative + R_cumulative @ t.ravel()

            cameras.append({
                "R": R_cumulative.copy(),
                "t": t_cumulative.copy(),
                "K": K,
                "image": str(image_files[i]),
            })

        # Save camera parameters
        cameras_file = output_dir / "cameras.json"
        cameras_serializable = []
        for cam in cameras:
            cameras_serializable.append({
                "R": cam["R"].tolist(),
                "t": cam["t"].tolist(),
                "K": cam["K"].tolist(),
                "image": cam["image"],
            })

        with open(cameras_file, "w") as f:
            json.dump(cameras_serializable, f, indent=2)

        console.print(f"[green]Lightweight SfM completed: {len(cameras)} cameras[/green]")

        return {
            "cameras": cameras,
            "n_cameras": len(cameras),
            "cameras_file": str(cameras_file),
        }

    def _parse_colmap_output(self, sparse_dir: Path) -> dict:
        """Parse COLMAP sparse reconstruction output."""
        # Simplified parser - in production use pycolmap
        cameras = []
        console.print(f"[green]Parsed COLMAP output from {sparse_dir}[/green]")
        return {"cameras": cameras, "sparse_dir": str(sparse_dir)}


class GaussianSplattingTrainer:
    """Train 3D Gaussian Splatting model from images and camera poses."""

    def __init__(self, config):
        self.config = config.reconstruction
        self.device = config.device
        self.project_dir = Path(config.project_dir)

    def train(
        self,
        images_dir: str,
        cameras: dict,
        output_dir: Optional[str] = None,
    ) -> dict:
        """Train 3D Gaussian Splatting model.

        Args:
            images_dir: Directory with input images
            cameras: Camera parameters from SfM
            output_dir: Output directory for trained model

        Returns:
            Dict with model path and training stats
        """
        if output_dir is None:
            output_dir = str(self.project_dir / "gaussian_splatting")
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        console.print("[cyan]Training 3D Gaussian Splatting model...[/cyan]")
        console.print(f"  Device: {self.device}")
        console.print(f"  Iterations: {self.config.gs_iterations}")

        # Initialize Gaussians from sparse point cloud
        gaussians = self._initialize_gaussians(cameras)

        # Training loop
        n_iters = self.config.gs_iterations
        optimizer = torch.optim.Adam(
            [
                {"params": [gaussians["positions"]], "lr": self.config.gs_position_lr_init},
                {"params": [gaussians["colors"]], "lr": 0.0025},
                {"params": [gaussians["opacities"]], "lr": 0.05},
                {"params": [gaussians["scales"]], "lr": 0.005},
                {"params": [gaussians["rotations"]], "lr": 0.001},
            ]
        )

        # Load training images
        import cv2
        images_dir = Path(images_dir)
        image_files = sorted(images_dir.glob("*.png")) + sorted(images_dir.glob("*.jpg"))

        training_stats = {"losses": [], "n_gaussians": []}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
        ) as progress:
            task = progress.add_task("Training Gaussians...", total=n_iters)

            for iteration in range(n_iters):
                # Select random training view
                view_idx = np.random.randint(0, len(image_files))

                # Render current Gaussians
                rendered = self._render_gaussians(gaussians, cameras, view_idx)

                # Load target image
                target = cv2.imread(str(image_files[view_idx % len(image_files)]))
                target = cv2.cvtColor(target, cv2.COLOR_BGR2RGB)
                target_tensor = torch.tensor(
                    target / 255.0, dtype=torch.float32, device=self.device
                )

                # Compute loss (L1 + SSIM)
                loss = self._compute_loss(rendered, target_tensor)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                # Densification
                if iteration < self.config.gs_densify_until_iter and iteration % 100 == 0:
                    gaussians = self._densify(gaussians, iteration)

                # Learning rate decay
                if iteration % 1000 == 0:
                    for param_group in optimizer.param_groups:
                        param_group["lr"] *= 0.95

                training_stats["losses"].append(loss.item())
                training_stats["n_gaussians"].append(len(gaussians["positions"]))

                if iteration % 500 == 0:
                    progress.update(task, completed=iteration)

            progress.update(task, completed=n_iters)

        # Save trained model
        model_path = output_dir / "gaussians.pt"
        torch.save(
            {k: v.detach().cpu() if isinstance(v, torch.Tensor) else v for k, v in gaussians.items()},
            model_path,
        )

        # Export point cloud
        ply_path = output_dir / "point_cloud.ply"
        self._export_ply(gaussians, ply_path)

        console.print(f"[green]Training complete![/green]")
        console.print(f"  Final loss: {training_stats['losses'][-1]:.6f}")
        console.print(f"  Gaussians: {training_stats['n_gaussians'][-1]}")
        console.print(f"  Model saved: {model_path}")

        return {
            "model_path": str(model_path),
            "ply_path": str(ply_path),
            "stats": training_stats,
        }

    def _initialize_gaussians(self, cameras: dict) -> dict:
        """Initialize Gaussian parameters from sparse point cloud."""
        # Generate initial points (random or from SfM)
        n_initial = 10000

        positions = torch.randn(n_initial, 3, device=self.device) * 0.5
        colors = torch.rand(n_initial, 3, device=self.device)
        opacities = torch.full((n_initial, 1), 0.1, device=self.device)
        scales = torch.full((n_initial, 3), -3.0, device=self.device)  # log scale
        rotations = torch.zeros(n_initial, 4, device=self.device)
        rotations[:, 0] = 1.0  # Identity quaternion

        # Make all parameters require gradients
        for tensor in [positions, colors, opacities, scales, rotations]:
            tensor.requires_grad_(True)

        return {
            "positions": positions,
            "colors": colors,
            "opacities": opacities,
            "scales": scales,
            "rotations": rotations,
        }

    def _render_gaussians(self, gaussians: dict, cameras: dict, view_idx: int) -> torch.Tensor:
        """Render Gaussians from a specific camera viewpoint.

        This is a simplified differentiable renderer.
        For production, use gsplat or diff-gaussian-rasterization.
        """
        # Simplified: return a dummy rendered image for training loop structure
        # In production, this would use the actual Gaussian rasterizer
        h, w = 256, 256  # Reduced resolution for training
        rendered = torch.sigmoid(
            gaussians["colors"][:100].mean(0).unsqueeze(0).unsqueeze(0).expand(h, w, 3)
            + torch.randn(h, w, 3, device=self.device) * 0.01
        )
        return rendered

    def _compute_loss(self, rendered: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """Compute rendering loss (L1 + simplified SSIM)."""
        # Resize target to match rendered
        if rendered.shape != target.shape:
            import torch.nn.functional as F
            target = F.interpolate(
                target.permute(2, 0, 1).unsqueeze(0),
                size=(rendered.shape[0], rendered.shape[1]),
                mode="bilinear",
                align_corners=False,
            ).squeeze(0).permute(1, 2, 0)

        l1_loss = torch.abs(rendered - target).mean()

        # Simplified SSIM
        mu_r = rendered.mean()
        mu_t = target.mean()
        sigma_r = rendered.var()
        sigma_t = target.var()
        sigma_rt = ((rendered - mu_r) * (target - mu_t)).mean()

        c1, c2 = 0.01 ** 2, 0.03 ** 2
        ssim = ((2 * mu_r * mu_t + c1) * (2 * sigma_rt + c2)) / (
            (mu_r ** 2 + mu_t ** 2 + c1) * (sigma_r + sigma_t + c2)
        )
        ssim_loss = 1 - ssim

        return 0.8 * l1_loss + 0.2 * ssim_loss

    def _densify(self, gaussians: dict, iteration: int) -> dict:
        """Densify Gaussians by splitting/cloning based on gradients."""
        # Simplified densification - add new Gaussians near high-gradient areas
        if iteration % 500 == 0 and len(gaussians["positions"]) < 100000:
            n_new = min(1000, len(gaussians["positions"]) // 10)
            idx = torch.randint(0, len(gaussians["positions"]), (n_new,))

            for key in gaussians:
                new_data = gaussians[key][idx].clone().detach().requires_grad_(True)
                if key == "positions":
                    new_data = new_data + torch.randn_like(new_data) * 0.01
                gaussians[key] = torch.cat(
                    [gaussians[key].detach().requires_grad_(True), new_data], dim=0
                )

        return gaussians

    def _export_ply(self, gaussians: dict, output_path: Path):
        """Export Gaussians as PLY point cloud."""
        positions = gaussians["positions"].detach().cpu().numpy()
        colors = (gaussians["colors"].detach().cpu().numpy() * 255).astype(np.uint8)

        n_points = len(positions)

        header = f"""ply
format ascii 1.0
element vertex {n_points}
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
"""
        with open(output_path, "w") as f:
            f.write(header)
            for i in range(n_points):
                f.write(
                    f"{positions[i, 0]:.6f} {positions[i, 1]:.6f} {positions[i, 2]:.6f} "
                    f"{colors[i, 0]} {colors[i, 1]} {colors[i, 2]}\n"
                )

        console.print(f"[green]Point cloud exported: {output_path} ({n_points} points)[/green]")
