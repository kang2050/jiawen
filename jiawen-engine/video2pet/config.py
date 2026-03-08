"""
Video2Pet Configuration Management
===================================
Central configuration for the entire pipeline.
Supports YAML config files and environment variables.
"""

import os
import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

load_dotenv()

# ─── Device Detection ───────────────────────────────────────────────
def detect_device() -> str:
    """Auto-detect the best available compute device."""
    import torch

    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"  # Apple Silicon
    else:
        return "cpu"


def detect_platform() -> dict:
    """Detect platform info for optimization hints."""
    info = {
        "system": platform.system(),
        "machine": platform.machine(),
        "is_apple_silicon": (
            platform.system() == "Darwin" and platform.machine() == "arm64"
        ),
        "python_version": platform.python_version(),
    }
    return info


# ─── Data Classes ────────────────────────────────────────────────────
@dataclass
class VideoConfig:
    """Video processing configuration."""
    max_frames: int = 300
    target_fps: int = 15
    target_resolution: tuple = (1280, 720)
    stabilize: bool = True
    auto_crop: bool = True


@dataclass
class PoseConfig:
    """Pose estimation configuration."""
    model_name: str = "vitpose_animal"  # vitpose_animal | deeplabcut | apple_vision
    confidence_threshold: float = 0.5
    num_keypoints: int = 24  # Standard animal keypoints
    use_tracking: bool = True
    batch_size: int = 16
    # SMAL model params
    smal_model_path: str = "models/smal/smal_CVPR2018.pkl"
    smal_data_path: str = "models/smal/"


@dataclass
class ReconstructionConfig:
    """3D reconstruction configuration."""
    method: str = "gaussian_splatting"  # gaussian_splatting | nerf | colmap_mesh
    # Gaussian Splatting params
    gs_iterations: int = 30000
    gs_sh_degree: int = 3
    gs_densify_until_iter: int = 15000
    gs_position_lr_init: float = 0.00016
    gs_position_lr_final: float = 0.0000016
    # SfM params
    sfm_method: str = "colmap"  # colmap | hloc
    # Mesh extraction
    mesh_resolution: int = 256
    texture_resolution: int = 2048


@dataclass
class RiggingConfig:
    """Rigging and animation configuration."""
    skeleton_type: str = "quadruped"  # quadruped | biped
    auto_rig: bool = True
    # Animal-specific templates
    pet_type: str = "dog"  # dog | cat | rabbit | bird
    breed: str = "generic"
    # Animation
    smooth_motion: bool = True
    motion_fps: int = 30


@dataclass
class ExportConfig:
    """Export configuration."""
    formats: list = field(default_factory=lambda: ["glb", "usdz", "fbx"])
    include_animation: bool = True
    include_texture: bool = True
    include_fur: bool = False  # Experimental
    compress: bool = True
    # GLB specific
    glb_draco_compression: bool = True
    # Texture
    texture_format: str = "png"  # png | jpg | webp


@dataclass
class APIConfig:
    """External API configuration."""
    # Google Veo
    google_api_key: str = ""
    veo_model: str = "veo-2.0-generate-001"
    # OpenAI Sora
    openai_api_key: str = ""
    sora_model: str = "sora"
    # Video generation
    video_duration: int = 5  # seconds
    video_resolution: str = "720p"


@dataclass
class WebConfig:
    """Web UI configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    share: bool = False  # Gradio share
    max_upload_size_mb: int = 500


@dataclass
class Video2PetConfig:
    """Master configuration."""
    # Project
    project_dir: str = "output"
    device: str = ""  # auto-detect if empty
    num_workers: int = 4
    verbose: bool = True

    # Sub-configs
    video: VideoConfig = field(default_factory=VideoConfig)
    pose: PoseConfig = field(default_factory=PoseConfig)
    reconstruction: ReconstructionConfig = field(default_factory=ReconstructionConfig)
    rigging: RiggingConfig = field(default_factory=RiggingConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    api: APIConfig = field(default_factory=APIConfig)
    web: WebConfig = field(default_factory=WebConfig)

    def __post_init__(self):
        if not self.device:
            self.device = detect_device()

        # Load API keys from environment
        self.api.google_api_key = os.getenv("GOOGLE_API_KEY", self.api.google_api_key)
        self.api.openai_api_key = os.getenv("OPENAI_API_KEY", self.api.openai_api_key)

        # Ensure project dir exists
        Path(self.project_dir).mkdir(parents=True, exist_ok=True)


def load_config(config_path: Optional[str] = None) -> Video2PetConfig:
    """Load configuration from YAML file, with defaults."""
    config = Video2PetConfig()

    if config_path and Path(config_path).exists():
        with open(config_path, "r") as f:
            yaml_config = yaml.safe_load(f)

        if yaml_config:
            # Update config from YAML
            for key, value in yaml_config.items():
                if hasattr(config, key):
                    attr = getattr(config, key)
                    if hasattr(attr, "__dataclass_fields__"):
                        for k, v in value.items():
                            if hasattr(attr, k):
                                setattr(attr, k, v)
                    else:
                        setattr(config, key, value)

    return config
