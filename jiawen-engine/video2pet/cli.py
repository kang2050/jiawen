"""
Video2Pet CLI
==============
Command-line interface for the Video2Pet pipeline.

Usage:
    video2pet run --video path/to/video.mp4 --pet-type dog --breed golden_retriever
    video2pet run --prompt "A corgi playing in the park" --pet-type dog --breed corgi
    video2pet extract-frames --video path/to/video.mp4 --output frames/
    video2pet detect-pose --frames frames/ --output poses/
    video2pet serve --port 8000
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="video2pet",
    help="Video2Pet: End-to-end pipeline from pet video to 3D digital twin",
    add_completion=False,
)
console = Console()


@app.command()
def run(
    video: Optional[str] = typer.Option(None, "--video", "-v", help="Path to input pet video"),
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Text prompt for AI video generation"),
    pet_type: str = typer.Option("dog", "--pet-type", "-t", help="Pet type: dog, cat, rabbit, bird"),
    breed: str = typer.Option("generic", "--breed", "-b", help="Pet breed for proportional adjustments"),
    output: str = typer.Option("output", "--output", "-o", help="Output directory"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to config YAML file"),
    device: Optional[str] = typer.Option(None, "--device", "-d", help="Compute device: cuda, mps, cpu"),
    skip_reconstruction: bool = typer.Option(False, "--skip-reconstruction", help="Skip 3D reconstruction"),
    skip_rigging: bool = typer.Option(False, "--skip-rigging", help="Skip rigging and animation"),
    fast: bool = typer.Option(False, "--fast", help="Fast mode: reduced iterations"),
):
    """Run the complete Video2Pet pipeline."""
    from video2pet.config import load_config
    from video2pet.pipeline import Video2PetPipeline

    # Load config
    cfg = load_config(config)
    cfg.project_dir = output

    if device:
        cfg.device = device

    if fast:
        cfg.reconstruction.gs_iterations = 5000
        cfg.video.max_frames = 100

    # Validate input
    if not video and not prompt:
        console.print("[red]Error: Either --video or --prompt must be provided[/red]")
        raise typer.Exit(1)

    if video and not Path(video).exists():
        console.print(f"[red]Error: Video file not found: {video}[/red]")
        raise typer.Exit(1)

    # Run pipeline
    pipeline = Video2PetPipeline(cfg)
    results = pipeline.run(
        video_path=video,
        prompt=prompt,
        pet_type=pet_type,
        breed=breed,
        skip_reconstruction=skip_reconstruction,
        skip_rigging=skip_rigging,
    )

    if "exports" in results:
        console.print("\n[bold green]Pipeline completed successfully![/bold green]")
    else:
        console.print("\n[yellow]Pipeline completed with warnings. Check output for details.[/yellow]")


@app.command("extract-frames")
def extract_frames(
    video: str = typer.Option(..., "--video", "-v", help="Path to input video"),
    output: str = typer.Option("frames", "--output", "-o", help="Output directory for frames"),
    max_frames: int = typer.Option(300, "--max-frames", "-n", help="Maximum number of frames"),
    fps: int = typer.Option(15, "--fps", help="Target frames per second"),
):
    """Extract frames from a video file."""
    from video2pet.config import Video2PetConfig
    from video2pet.video.processor import VideoProcessor

    cfg = Video2PetConfig()
    cfg.video.max_frames = max_frames
    cfg.video.target_fps = fps

    processor = VideoProcessor(cfg)
    frames = processor.extract_frames(video, output_dir=output, max_frames=max_frames, target_fps=fps)
    console.print(f"\n[green]Extracted {len(frames)} frames to {output}[/green]")


@app.command("detect-pose")
def detect_pose(
    frames_dir: str = typer.Option(..., "--frames", "-f", help="Directory containing frame images"),
    output: str = typer.Option("poses", "--output", "-o", help="Output directory for pose data"),
    model: str = typer.Option("vitpose_animal", "--model", "-m", help="Pose model: vitpose_animal, apple_vision"),
):
    """Detect 2D animal poses from frame images."""
    import json

    from video2pet.config import Video2PetConfig
    from video2pet.pose.detector import PoseDetector

    cfg = Video2PetConfig()
    cfg.pose.model_name = model

    detector = PoseDetector(cfg)

    frames_dir = Path(frames_dir)
    frame_files = sorted(frames_dir.glob("*.png")) + sorted(frames_dir.glob("*.jpg"))

    if not frame_files:
        console.print(f"[red]No image files found in {frames_dir}[/red]")
        raise typer.Exit(1)

    results = detector.detect_batch(frame_files)

    # Save results
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "pose_detections.json"
    serializable = []
    for r in results:
        entry = {"frame": r["frame"], "score": r["score"], "bbox": r["bbox"]}
        if r["keypoints"] is not None:
            entry["keypoints"] = r["keypoints"].tolist()
        serializable.append(entry)

    with open(output_file, "w") as f:
        json.dump(serializable, f, indent=2)

    console.print(f"\n[green]Pose detections saved to {output_file}[/green]")


@app.command("visualize")
def visualize(
    mesh: Optional[str] = typer.Option(None, "--mesh", "-m", help="Path to mesh file (OBJ/PLY/GLB)"),
    point_cloud: Optional[str] = typer.Option(None, "--point-cloud", "-p", help="Path to point cloud (PLY)"),
    port: int = typer.Option(8080, "--port", help="Visualization server port"),
):
    """Visualize 3D reconstruction results."""
    if not mesh and not point_cloud:
        console.print("[red]Provide --mesh or --point-cloud[/red]")
        raise typer.Exit(1)

    try:
        import viser

        server = viser.ViserServer(host="0.0.0.0", port=port)
        console.print(f"[green]Visualization server running at http://localhost:{port}[/green]")

        if mesh:
            import trimesh
            m = trimesh.load(mesh)
            server.scene.add_mesh_trimesh("pet_mesh", m)

        if point_cloud:
            import trimesh
            pc = trimesh.load(point_cloud)
            if hasattr(pc, "vertices"):
                import numpy as np
                server.scene.add_point_cloud(
                    "point_cloud",
                    points=np.array(pc.vertices),
                    colors=np.array(pc.colors[:, :3]) if hasattr(pc, "colors") else None,
                    point_size=0.005,
                )

        console.print("[yellow]Press Ctrl+C to stop[/yellow]")
        import time
        while True:
            time.sleep(1)

    except ImportError:
        console.print("[yellow]viser not installed. Install with: pip install viser[/yellow]")
        console.print("[yellow]Alternatively, open the mesh file in MeshLab or Blender[/yellow]")


@app.command("serve")
def serve(
    port: int = typer.Option(8000, "--port", "-p", help="Server port"),
    host: str = typer.Option("0.0.0.0", "--host", help="Server host"),
    share: bool = typer.Option(False, "--share", help="Create public Gradio link"),
):
    """Start the Video2Pet web interface."""
    from video2pet.config import Video2PetConfig

    cfg = Video2PetConfig()
    cfg.web.port = port
    cfg.web.host = host
    cfg.web.share = share

    try:
        from web.app import create_app
        app = create_app(cfg)
        app.launch(server_name=host, server_port=port, share=share)
    except ImportError:
        console.print("[yellow]Web UI dependencies not installed.[/yellow]")
        console.print("[yellow]Install with: pip install gradio[/yellow]")

        # Fallback: simple FastAPI server
        console.print("[cyan]Starting minimal API server...[/cyan]")
        import uvicorn
        from video2pet.web_api import create_api
        api = create_api(cfg)
        uvicorn.run(api, host=host, port=port)


@app.command("info")
def info():
    """Show system information and configuration."""
    from video2pet.config import detect_device, detect_platform

    platform_info = detect_platform()
    device = detect_device()

    console.print("\n[bold]Video2Pet System Information[/bold]\n")
    console.print(f"  Platform: {platform_info['system']} ({platform_info['machine']})")
    console.print(f"  Python: {platform_info['python_version']}")
    console.print(f"  Apple Silicon: {'Yes' if platform_info['is_apple_silicon'] else 'No'}")
    console.print(f"  Compute Device: {device}")

    # Check dependencies
    console.print("\n[bold]Dependencies:[/bold]")
    deps = [
        ("torch", "PyTorch"),
        ("torchvision", "TorchVision"),
        ("cv2", "OpenCV"),
        ("trimesh", "Trimesh"),
        ("open3d", "Open3D"),
        ("gradio", "Gradio"),
        ("viser", "Viser"),
    ]

    for module, name in deps:
        try:
            __import__(module)
            version = getattr(__import__(module), "__version__", "installed")
            console.print(f"  [green]✓[/green] {name}: {version}")
        except ImportError:
            console.print(f"  [red]✗[/red] {name}: not installed")

    console.print()


if __name__ == "__main__":
    app()
