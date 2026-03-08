"""
Skeleton & Rigging System
===========================
Automatic skeleton creation and rigging for pet meshes.
Supports quadruped (dog, cat) and custom skeleton templates.

Inspired by GMR (General Motion Retargeting) from video2robot.
"""

from pathlib import Path
from typing import Optional

import numpy as np
from rich.console import Console

console = Console()

# ─── Skeleton Templates ─────────────────────────────────────────────

QUADRUPED_SKELETON = {
    "name": "quadruped",
    "joints": [
        {"name": "root", "parent": -1, "position": [0, 0, 0]},
        {"name": "spine_base", "parent": 0, "position": [0, 0.1, 0]},
        {"name": "spine_mid", "parent": 1, "position": [0, 0.2, 0]},
        {"name": "spine_chest", "parent": 2, "position": [0, 0.3, 0]},
        {"name": "neck", "parent": 3, "position": [0, 0.35, 0.05]},
        {"name": "head", "parent": 4, "position": [0, 0.4, 0.1]},
        {"name": "jaw", "parent": 5, "position": [0, 0.38, 0.15]},
        {"name": "left_ear", "parent": 5, "position": [0.03, 0.43, 0.1]},
        {"name": "right_ear", "parent": 5, "position": [-0.03, 0.43, 0.1]},
        # Front legs
        {"name": "left_front_shoulder", "parent": 3, "position": [0.06, 0.28, 0]},
        {"name": "left_front_elbow", "parent": 9, "position": [0.06, 0.15, 0]},
        {"name": "left_front_wrist", "parent": 10, "position": [0.06, 0.05, 0]},
        {"name": "left_front_paw", "parent": 11, "position": [0.06, 0, 0.02]},
        {"name": "right_front_shoulder", "parent": 3, "position": [-0.06, 0.28, 0]},
        {"name": "right_front_elbow", "parent": 13, "position": [-0.06, 0.15, 0]},
        {"name": "right_front_wrist", "parent": 14, "position": [-0.06, 0.05, 0]},
        {"name": "right_front_paw", "parent": 15, "position": [-0.06, 0, 0.02]},
        # Back legs
        {"name": "left_back_hip", "parent": 1, "position": [0.05, 0.08, -0.02]},
        {"name": "left_back_knee", "parent": 17, "position": [0.05, 0.04, -0.04]},
        {"name": "left_back_ankle", "parent": 18, "position": [0.05, 0.02, 0]},
        {"name": "left_back_paw", "parent": 19, "position": [0.05, 0, 0.02]},
        {"name": "right_back_hip", "parent": 1, "position": [-0.05, 0.08, -0.02]},
        {"name": "right_back_knee", "parent": 21, "position": [-0.05, 0.04, -0.04]},
        {"name": "right_back_ankle", "parent": 22, "position": [-0.05, 0.02, 0]},
        {"name": "right_back_paw", "parent": 23, "position": [-0.05, 0, 0.02]},
        # Tail
        {"name": "tail_base", "parent": 0, "position": [0, 0.05, -0.08]},
        {"name": "tail_mid", "parent": 25, "position": [0, 0.08, -0.15]},
        {"name": "tail_tip", "parent": 26, "position": [0, 0.12, -0.22]},
    ],
}

# Breed-specific scale adjustments
BREED_SCALES = {
    "generic": {"body_length": 1.0, "leg_length": 1.0, "head_size": 1.0},
    "golden_retriever": {"body_length": 1.1, "leg_length": 1.05, "head_size": 1.05},
    "corgi": {"body_length": 1.2, "leg_length": 0.6, "head_size": 1.1},
    "german_shepherd": {"body_length": 1.15, "leg_length": 1.1, "head_size": 1.0},
    "chihuahua": {"body_length": 0.7, "leg_length": 0.6, "head_size": 1.3},
    "cat_generic": {"body_length": 0.85, "leg_length": 0.9, "head_size": 1.1},
    "persian_cat": {"body_length": 0.8, "leg_length": 0.85, "head_size": 1.2},
    "siamese_cat": {"body_length": 0.9, "leg_length": 1.0, "head_size": 0.95},
}


class SkeletonBuilder:
    """Build and adapt skeleton for pet meshes."""

    def __init__(self, config):
        self.config = config.rigging
        self.project_dir = Path(config.project_dir)

    def create_skeleton(
        self,
        pet_type: str = "dog",
        breed: str = "generic",
        mesh_data: Optional[dict] = None,
    ) -> dict:
        """Create a skeleton adapted to the pet type and mesh.
        优先使用 SMAL 官方动物骨骼模型；若不可用则回退到内置模板。
        """
        console.print(f"[cyan]Creating skeleton for {pet_type} ({breed})...[/cyan]")

        # 优先使用 SMAL 骨骼（更精确的动物骨骼）
        smal_skeleton = self._load_smal_skeleton(pet_type)
        if smal_skeleton:
            console.print("[green]使用 SMAL 官方动物骨骼模型[/green]")
            skeleton = smal_skeleton
        else:
            console.print("[yellow]SMAL 不可用，使用内置骨骼模板[/yellow]")
            skeleton = self._copy_skeleton(QUADRUPED_SKELETON)

        # Apply breed-specific adjustments
        breed_key = breed if breed in BREED_SCALES else "generic"
        if pet_type == "cat" and breed_key == "generic":
            breed_key = "cat_generic"
        scales = BREED_SCALES[breed_key]
        skeleton = self._apply_breed_scales(skeleton, scales)

        # Fit to mesh if available
        if mesh_data and "vertices" in mesh_data:
            skeleton = self._fit_to_mesh(skeleton, mesh_data)

        # Compute bind matrices
        skeleton["bind_matrices"] = self._compute_bind_matrices(skeleton)

        # Save skeleton
        output_path = self.project_dir / "skeleton" / "skeleton.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._save_skeleton(skeleton, output_path)

        console.print(f"[green]Skeleton created: {len(skeleton['joints'])} joints[/green]")
        return skeleton

    def _load_smal_skeleton(self, pet_type: str = "dog") -> Optional[dict]:
        """从 SMAL 模型提取骨骼，返回标准 skeleton dict；失败返回 None。"""
        # 先查 JSON 缓存
        smal_json = Path(__file__).parent.parent.parent / "assets" / "skeletons" / "smal_dog_joints.json"
        if smal_json.exists():
            try:
                import json
                with open(smal_json) as f:
                    data = json.load(f)
                return {"name": "smal_dog", "joints": data["joints"]}
            except Exception:
                pass

        # 尝试从 pkl 实时提取
        smal_pkl = Path(__file__).parent.parent.parent / "assets" / "skeletons" / "smal" / "smal_CVPR2017.pkl"
        data_pkl = Path(__file__).parent.parent.parent / "assets" / "skeletons" / "smal" / "smal_CVPR2017_data.pkl"
        if not (smal_pkl.exists() and data_pkl.exists()):
            return None
        try:
            import sys, types, pickle, numpy as np
            # chumpy stub
            if "chumpy" not in sys.modules:
                class _Ch:
                    def __init__(self, *a, **kw): self._arr = np.array(a[0]) if a else np.array([])
                    def __array__(self, d=None): return self._arr if d is None else self._arr.astype(d)
                    def __setstate__(self, s): self.__dict__.update(s)
                _m = types.ModuleType("chumpy"); _m.Ch = _Ch; _m.array = lambda x, *a, **kw: _Ch(x)
                sys.modules["chumpy"] = _m; sys.modules["chumpy.ch"] = _m
            with open(smal_pkl, "rb") as f:
                model = pickle.load(f, encoding="latin1")
            with open(data_pkl, "rb") as f:
                extra = pickle.load(f, encoding="latin1")
            kintree = model["kintree_table"]
            J_reg = model["J_regressor"]
            v_tmpl = model["v_template"]
            # 犬科 betas
            dog_betas = extra["cluster_means"][1]
            sd = np.array(model["shapedirs"])
            dog_v = v_tmpl.copy()
            n_use = min(len(dog_betas), sd.shape[-1])
            if sd.ndim == 3:
                dog_v += sd[:, :, :n_use] @ dog_betas[:n_use]
            J = J_reg.dot(dog_v) if hasattr(J_reg, "dot") else J_reg @ dog_v
            n_joints = J.shape[0]
            joints = []
            for i in range(n_joints):
                parent = int(kintree[0, i]) if kintree[0, i] != 4294967295 else -1
                joints.append({"name": f"smal_j{i}", "parent": parent, "position": J[i].tolist()})
            return {"name": "smal_dog", "joints": joints}
        except Exception as e:
            console.print(f"[yellow]SMAL 加载失败: {e}[/yellow]")
            return None

    def _copy_skeleton(self, template: dict) -> dict:
        """Deep copy a skeleton template."""
        import copy
        return copy.deepcopy(template)

    def _apply_breed_scales(self, skeleton: dict, scales: dict) -> dict:
        """Apply breed-specific proportional scaling."""
        body_scale = scales["body_length"]
        leg_scale = scales["leg_length"]
        head_scale = scales["head_size"]

        for joint in skeleton["joints"]:
            pos = joint["position"]
            name = joint["name"]

            # Scale body joints
            if "spine" in name or "tail" in name:
                pos[2] *= body_scale

            # Scale leg joints
            if any(x in name for x in ["shoulder", "elbow", "wrist", "paw", "hip", "knee", "ankle"]):
                pos[1] *= leg_scale

            # Scale head joints
            if any(x in name for x in ["head", "jaw", "ear", "neck"]):
                for i in range(3):
                    pos[i] *= head_scale

            joint["position"] = pos

        return skeleton

    def _fit_to_mesh(self, skeleton: dict, mesh_data: dict) -> dict:
        """Fit skeleton to the actual mesh dimensions."""
        vertices = np.array(mesh_data["vertices"])

        # Compute mesh bounding box
        bbox_min = vertices.min(axis=0)
        bbox_max = vertices.max(axis=0)
        bbox_size = bbox_max - bbox_min
        bbox_center = (bbox_min + bbox_max) / 2

        # Compute skeleton bounding box
        joint_positions = np.array([j["position"] for j in skeleton["joints"]])
        skel_min = joint_positions.min(axis=0)
        skel_max = joint_positions.max(axis=0)
        skel_size = skel_max - skel_min + 1e-6

        # Scale skeleton to match mesh
        scale = bbox_size / skel_size
        skel_center = (skel_min + skel_max) / 2

        for joint in skeleton["joints"]:
            pos = np.array(joint["position"])
            pos = (pos - skel_center) * scale + bbox_center
            joint["position"] = pos.tolist()

        console.print("  Skeleton fitted to mesh dimensions")
        return skeleton

    def _compute_bind_matrices(self, skeleton: dict) -> list:
        """Compute inverse bind matrices for skinning."""
        n_joints = len(skeleton["joints"])
        bind_matrices = []

        for i, joint in enumerate(skeleton["joints"]):
            pos = np.array(joint["position"])
            # Simple translation matrix (no rotation in bind pose)
            mat = np.eye(4)
            mat[:3, 3] = pos
            # Inverse for bind matrix
            inv_mat = np.eye(4)
            inv_mat[:3, 3] = -pos
            bind_matrices.append(inv_mat.tolist())

        return bind_matrices

    def _save_skeleton(self, skeleton: dict, path: Path):
        """Save skeleton to JSON."""
        import json
        with open(path, "w") as f:
            json.dump(skeleton, f, indent=2)
        console.print(f"  Saved to {path}")


class SkinningEngine:
    """Compute skinning weights for mesh vertices."""

    def __init__(self, config):
        self.config = config.rigging

    def compute_weights(self, mesh_data: dict, skeleton: dict) -> np.ndarray:
        """Compute linear blend skinning weights.

        Uses heat diffusion / distance-based weight assignment.

        Args:
            mesh_data: Mesh with vertices and faces
            skeleton: Skeleton with joint positions

        Returns:
            Weight matrix of shape (n_vertices, n_joints)
        """
        console.print("[cyan]Computing skinning weights...[/cyan]")

        vertices = np.array(mesh_data["vertices"])
        joint_positions = np.array([j["position"] for j in skeleton["joints"]])

        n_verts = len(vertices)
        n_joints = len(joint_positions)

        # Distance-based weight computation
        weights = np.zeros((n_verts, n_joints))

        for j in range(n_joints):
            distances = np.linalg.norm(vertices - joint_positions[j], axis=1)
            # Inverse distance weighting with falloff
            sigma = np.median(distances) * 0.5
            weights[:, j] = np.exp(-distances ** 2 / (2 * sigma ** 2))

        # Normalize weights per vertex (each vertex's weights sum to 1)
        row_sums = weights.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        weights = weights / row_sums

        # Enforce max influences per vertex (typically 4)
        max_influences = 4
        for i in range(n_verts):
            sorted_indices = np.argsort(weights[i])[::-1]
            weights[i, sorted_indices[max_influences:]] = 0
            # Renormalize
            total = weights[i].sum()
            if total > 0:
                weights[i] /= total

        console.print(
            f"[green]Skinning weights computed: "
            f"{n_verts} vertices, {n_joints} joints, "
            f"max {max_influences} influences/vertex[/green]"
        )
        return weights


class MotionRetargeter:
    """Retarget motion from pose estimation to skeleton.

    Inspired by GMR (General Motion Retargeting) from video2robot.
    """

    def __init__(self, config):
        self.config = config.rigging

    def retarget(
        self,
        pose_sequence: list[dict],
        skeleton: dict,
    ) -> list[dict]:
        """Retarget 3D pose sequence to skeleton animation.

        Args:
            pose_sequence: List of 3D pose results from PoseEstimator3D
            skeleton: Target skeleton

        Returns:
            List of animation frames with joint rotations
        """
        console.print("[cyan]Retargeting motion to skeleton...[/cyan]")

        animation_frames = []
        joint_names = [j["name"] for j in skeleton["joints"]]

        for frame_data in pose_sequence:
            joints_3d = frame_data.get("joints_3d", frame_data.get("joints_3d_smooth"))
            if joints_3d is None:
                continue

            # Map estimated joints to skeleton joints
            joint_rotations = {}
            for i, joint in enumerate(skeleton["joints"]):
                parent_idx = joint["parent"]
                if parent_idx < 0:
                    # Root joint: compute global rotation
                    joint_rotations[joint["name"]] = self._compute_root_rotation(joints_3d)
                else:
                    # Child joint: compute local rotation relative to parent
                    joint_rotations[joint["name"]] = self._compute_local_rotation(
                        joints_3d, i, parent_idx, skeleton
                    )

            animation_frames.append({
                "frame": frame_data.get("frame", ""),
                "rotations": joint_rotations,
                "root_position": joints_3d[0].tolist() if len(joints_3d) > 0 else [0, 0, 0],
            })

        console.print(f"[green]Motion retargeted: {len(animation_frames)} frames[/green]")
        return animation_frames

    def _compute_root_rotation(self, joints_3d: np.ndarray) -> list:
        """Compute root joint rotation from 3D joints."""
        # Simple: align body axis with spine direction
        if len(joints_3d) >= 2:
            forward = joints_3d[1] - joints_3d[0]
            forward = forward / (np.linalg.norm(forward) + 1e-8)
            # Convert to axis-angle (simplified)
            angle = np.arctan2(forward[0], forward[2])
            return [0, angle, 0]
        return [0, 0, 0]

    def _compute_local_rotation(
        self, joints_3d: np.ndarray, joint_idx: int, parent_idx: int, skeleton: dict
    ) -> list:
        """Compute local rotation for a joint relative to its parent."""
        # Map skeleton joint index to pose joint index (approximate)
        n_pose_joints = len(joints_3d)
        pose_idx = min(joint_idx, n_pose_joints - 1)
        parent_pose_idx = min(parent_idx, n_pose_joints - 1)

        if pose_idx < n_pose_joints and parent_pose_idx < n_pose_joints:
            bone_dir = joints_3d[pose_idx] - joints_3d[parent_pose_idx]
            bone_dir = bone_dir / (np.linalg.norm(bone_dir) + 1e-8)

            # Compute rotation from rest pose to current pose
            rest_dir = np.array(skeleton["joints"][joint_idx]["position"]) - np.array(
                skeleton["joints"][parent_idx]["position"]
            )
            rest_dir = rest_dir / (np.linalg.norm(rest_dir) + 1e-8)

            # Axis-angle from rest to current
            axis = np.cross(rest_dir, bone_dir)
            axis_norm = np.linalg.norm(axis)
            if axis_norm > 1e-6:
                axis = axis / axis_norm
                angle = np.arccos(np.clip(np.dot(rest_dir, bone_dir), -1, 1))
                return (axis * angle).tolist()

        return [0, 0, 0]
