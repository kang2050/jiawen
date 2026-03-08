"""
Video2Pet Pipeline
===================
End-to-end pipeline: Video → Pose Extraction → 3D Reconstruction → Digital Twin Asset

This is the main orchestrator that connects all modules:
1. Video Processing (input / AI generation)
2. Pet Pose Estimation (2D detection → 3D lifting)
3. 3D Reconstruction (SfM → Gaussian Splatting → Mesh)
4. Rigging & Animation (skeleton → skinning → retargeting)
5. Export (GLB / USDZ / FBX)
"""

import json
import time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from video2pet.config import Video2PetConfig, load_config

console = Console()


class Video2PetPipeline:
    """Complete Video2Pet processing pipeline."""

    def __init__(self, config: Optional[Video2PetConfig] = None):
        self.config = config or Video2PetConfig()
        self.project_dir = Path(self.config.project_dir)
        self.project_dir.mkdir(parents=True, exist_ok=True)

        # Initialize modules lazily
        self._video_processor = None
        self._pose_detector = None
        self._pose_estimator = None
        self._sfm_processor = None
        self._gs_trainer = None
        self._mesh_extractor = None
        self._skeleton_builder = None
        self._skinning_engine = None
        self._motion_retargeter = None

    # ─── Lazy Module Initialization ──────────────────────────────────

    @property
    def video_processor(self):
        if self._video_processor is None:
            from video2pet.video.processor import VideoProcessor
            self._video_processor = VideoProcessor(self.config)
        return self._video_processor

    @property
    def pose_detector(self):
        if self._pose_detector is None:
            from video2pet.pose.detector import PoseDetector
            self._pose_detector = PoseDetector(self.config)
        return self._pose_detector

    @property
    def pose_estimator(self):
        if self._pose_estimator is None:
            from video2pet.pose.estimator_3d import PoseEstimator3D
            self._pose_estimator = PoseEstimator3D(self.config)
        return self._pose_estimator

    @property
    def sfm_processor(self):
        if self._sfm_processor is None:
            from video2pet.reconstruction.gaussian import SfMProcessor
            self._sfm_processor = SfMProcessor(self.config)
        return self._sfm_processor

    @property
    def gs_trainer(self):
        if self._gs_trainer is None:
            from video2pet.reconstruction.gaussian import GaussianSplattingTrainer
            self._gs_trainer = GaussianSplattingTrainer(self.config)
        return self._gs_trainer

    @property
    def mesh_extractor(self):
        if self._mesh_extractor is None:
            from video2pet.reconstruction.mesh import MeshExtractor
            self._mesh_extractor = MeshExtractor(self.config)
        return self._mesh_extractor

    @property
    def skeleton_builder(self):
        if self._skeleton_builder is None:
            from video2pet.rigging.skeleton import SkeletonBuilder
            self._skeleton_builder = SkeletonBuilder(self.config)
        return self._skeleton_builder

    @property
    def skinning_engine(self):
        if self._skinning_engine is None:
            from video2pet.rigging.skeleton import SkinningEngine
            self._skinning_engine = SkinningEngine(self.config)
        return self._skinning_engine

    @property
    def motion_retargeter(self):
        if self._motion_retargeter is None:
            from video2pet.rigging.skeleton import MotionRetargeter
            self._motion_retargeter = MotionRetargeter(self.config)
        return self._motion_retargeter

    # ─── Main Pipeline ───────────────────────────────────────────────

    def run(
        self,
        video_path: Optional[str] = None,
        prompt: Optional[str] = None,
        pet_type: str = "dog",
        breed: str = "generic",
        skip_reconstruction: bool = False,
        skip_rigging: bool = False,
    ) -> dict:
        """Run the complete Video2Pet pipeline.

        Args:
            video_path: Path to input pet video (mutually exclusive with prompt)
            prompt: Text prompt for AI video generation (mutually exclusive with video_path)
            pet_type: Type of pet (dog, cat, etc.)
            breed: Specific breed
            skip_reconstruction: Skip 3D reconstruction (pose only)
            skip_rigging: Skip rigging and animation

        Returns:
            Dict with all pipeline outputs
        """
        start_time = time.time()

        self._print_header()

        results = {
            "config": {
                "pet_type": pet_type,
                "breed": breed,
                "device": self.config.device,
            },
            "timing": {},
        }

        # ─── Step 1: Video Input ─────────────────────────────────────
        console.print(Panel("[bold]Step 1: Video Input[/bold]", style="cyan"))

        t0 = time.time()
        if video_path:
            metadata = self.video_processor.load_video(video_path)
            results["video_metadata"] = metadata
        elif prompt:
            video_path = self._generate_video(prompt, pet_type)
            if video_path:
                metadata = self.video_processor.load_video(video_path)
                results["video_metadata"] = metadata
            else:
                console.print("[red]Video generation failed[/red]")
                return results
        else:
            console.print("[red]Either video_path or prompt must be provided[/red]")
            return results

        results["timing"]["video_input"] = time.time() - t0

        # ─── Step 2: Frame Extraction ────────────────────────────────
        console.print(Panel("[bold]Step 2: Frame Extraction[/bold]", style="cyan"))

        t0 = time.time()
        frames_dir = str(self.project_dir / "frames")
        frames = self.video_processor.extract_frames(video_path, output_dir=frames_dir)
        results["frames"] = [str(f) for f in frames]
        results["timing"]["frame_extraction"] = time.time() - t0

        if not frames:
            console.print("[red]No frames extracted[/red]")
            return results

        # ─── Step 3: Pet Detection ───────────────────────────────────
        console.print(Panel("[bold]Step 3: Pet Detection[/bold]", style="cyan"))

        t0 = time.time()
        detections = self.video_processor.detect_pet_segments(frames)
        results["detections"] = detections
        results["timing"]["pet_detection"] = time.time() - t0

        # ─── Step 4: 2D Pose Estimation ──────────────────────────────
        console.print(Panel("[bold]Step 4: 2D Pose Estimation[/bold]", style="cyan"))

        t0 = time.time()
        pose_2d = self.pose_detector.detect_batch(frames)
        results["pose_2d"] = pose_2d
        results["timing"]["pose_2d"] = time.time() - t0

        # ─── Step 5: 3D Pose Estimation ──────────────────────────────
        console.print(Panel("[bold]Step 5: 3D Pose Estimation[/bold]", style="cyan"))

        t0 = time.time()
        pose_3d = self.pose_estimator.estimate_sequence(pose_2d)
        pose_3d = self.pose_estimator.smooth_sequence(pose_3d)
        results["pose_3d"] = pose_3d
        results["timing"]["pose_3d"] = time.time() - t0

        if skip_reconstruction:
            self._print_summary(results, time.time() - start_time)
            return results

        # ─── Step 6: Structure from Motion ───────────────────────────
        console.print(Panel("[bold]Step 6: Structure from Motion[/bold]", style="cyan"))

        t0 = time.time()
        sfm_dir = str(self.project_dir / "sfm")
        cameras = self.sfm_processor.run_colmap(frames_dir, sfm_dir)
        results["cameras"] = cameras
        results["timing"]["sfm"] = time.time() - t0

        # ─── Step 7: 3D Gaussian Splatting ───────────────────────────
        console.print(Panel("[bold]Step 7: 3D Gaussian Splatting[/bold]", style="cyan"))

        t0 = time.time()
        gs_result = self.gs_trainer.train(frames_dir, cameras)
        results["gaussian_splatting"] = gs_result
        results["timing"]["gaussian_splatting"] = time.time() - t0

        # ─── Step 8: Mesh Extraction ─────────────────────────────────
        console.print(Panel("[bold]Step 8: Mesh Extraction[/bold]", style="cyan"))

        t0 = time.time()
        mesh_data = self.mesh_extractor.from_gaussians(gs_result["model_path"])
        results["mesh"] = mesh_data
        results["timing"]["mesh_extraction"] = time.time() - t0

        if skip_rigging or "error" in mesh_data:
            self._print_summary(results, time.time() - start_time)
            return results

        # ─── Step 9: Skeleton & Rigging ──────────────────────────────
        console.print(Panel("[bold]Step 9: Skeleton & Rigging[/bold]", style="cyan"))

        t0 = time.time()
        skeleton = self.skeleton_builder.create_skeleton(pet_type, breed, mesh_data)
        weights = self.skinning_engine.compute_weights(mesh_data, skeleton)
        results["skeleton"] = skeleton
        results["skinning_weights_shape"] = weights.shape
        results["timing"]["rigging"] = time.time() - t0

        # ─── Step 10: Motion Retargeting ─────────────────────────────
        console.print(Panel("[bold]Step 10: Motion Retargeting[/bold]", style="cyan"))

        t0 = time.time()
        animation = self.motion_retargeter.retarget(pose_3d, skeleton)
        results["animation_frames"] = len(animation)
        results["timing"]["retargeting"] = time.time() - t0

        # ─── Step 11: Export ─────────────────────────────────────────
        console.print(Panel("[bold]Step 11: Asset Export[/bold]", style="cyan"))

        t0 = time.time()
        export_results = self._export_all(mesh_data, skeleton, animation, weights)
        results["exports"] = export_results
        results["timing"]["export"] = time.time() - t0

        # ─── Summary ─────────────────────────────────────────────────
        total_time = time.time() - start_time
        self._print_summary(results, total_time)

        # Save results
        results_path = self.project_dir / "pipeline_results.json"
        self._save_results(results, results_path)

        return results

    def _generate_video(self, prompt: str, pet_type: str) -> Optional[str]:
        """Generate video from text prompt."""
        # Try Veo first, then Sora
        if self.config.api.google_api_key:
            from video2pet.video.veo_client import VeoClient
            client = VeoClient(self.config)
            result = client.generate(prompt, pet_type=pet_type)
            if result:
                return result

        if self.config.api.openai_api_key:
            from video2pet.video.veo_client import SoraClient
            client = SoraClient(self.config)
            result = client.generate(prompt, pet_type=pet_type)
            if result:
                return result

        console.print(
            "[yellow]No API keys configured for video generation. "
            "Please provide a video file instead.[/yellow]"
        )
        return None

    def _export_all(
        self,
        mesh_data: dict,
        skeleton: dict,
        animation: list,
        weights: object,
    ) -> dict:
        """Export in all configured formats."""
        export_results = {}

        for fmt in self.config.export.formats:
            if fmt == "glb":
                from video2pet.export.glb import GLBExporter
                exporter = GLBExporter(self.config)
                path = exporter.export(mesh_data, skeleton, animation, weights)
                export_results["glb"] = path
            elif fmt == "usdz":
                from video2pet.export.glb import USDZExporter
                exporter = USDZExporter(self.config)
                path = exporter.export(mesh_data)
                export_results["usdz"] = path
            elif fmt == "fbx":
                from video2pet.export.glb import FBXExporter
                exporter = FBXExporter(self.config)
                path = exporter.export(mesh_data)
                export_results["fbx"] = path

        return export_results

    def _print_header(self):
        """Print pipeline header."""
        console.print()
        console.print(
            Panel(
                "[bold green]Video2Pet Pipeline[/bold green]\n"
                "从视频到宠物数字孪生 — 端到端处理流水线\n\n"
                f"Device: {self.config.device} | "
                f"Output: {self.project_dir}",
                title="🐾 Video2Pet",
                border_style="green",
            )
        )
        console.print()

    def _print_summary(self, results: dict, total_time: float):
        """Print pipeline execution summary."""
        console.print()

        table = Table(title="Pipeline Summary", show_header=True, header_style="bold cyan")
        table.add_column("Stage", style="white")
        table.add_column("Time", justify="right", style="green")
        table.add_column("Status", justify="center")

        for stage, duration in results.get("timing", {}).items():
            status = "✓" if duration > 0 else "✗"
            table.add_row(stage.replace("_", " ").title(), f"{duration:.1f}s", status)

        table.add_row("─" * 20, "─" * 8, "─" * 6, style="dim")
        table.add_row("[bold]Total[/bold]", f"[bold]{total_time:.1f}s[/bold]", "")

        console.print(table)

        # Print export paths
        if "exports" in results:
            console.print("\n[bold]Exported Files:[/bold]")
            for fmt, path in results["exports"].items():
                if path:
                    console.print(f"  {fmt.upper()}: {path}")

        console.print()

    def _save_results(self, results: dict, path: Path):
        """Save pipeline results to JSON (serializable parts only)."""
        serializable = {}
        for key, value in results.items():
            if key in ("timing", "config", "video_metadata", "exports", "animation_frames"):
                serializable[key] = value
            elif key == "frames":
                serializable["n_frames"] = len(value)
            elif key == "mesh":
                serializable["mesh"] = {
                    k: v for k, v in value.items()
                    if isinstance(v, (str, int, float))
                }

        with open(path, "w") as f:
            json.dump(serializable, f, indent=2, default=str)

        console.print(f"[green]Results saved: {path}[/green]")
