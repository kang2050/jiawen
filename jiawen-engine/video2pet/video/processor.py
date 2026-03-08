"""
Video Processor
================
Handles video input: loading, frame extraction, stabilization, preprocessing.
Optimized for Apple Silicon (M2 Max) with VideoToolbox hardware acceleration.
"""

import subprocess
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()


class VideoProcessor:
    """Process pet videos for the reconstruction pipeline."""

    def __init__(self, config):
        self.config = config.video
        self.device = config.device
        self.output_dir = Path(config.project_dir)

    def load_video(self, video_path: str) -> dict:
        """Load video and extract metadata."""
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        metadata = {
            "path": str(video_path),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "duration": cap.get(cv2.CAP_PROP_FRAME_COUNT) / max(cap.get(cv2.CAP_PROP_FPS), 1),
            "codec": int(cap.get(cv2.CAP_PROP_FOURCC)),
        }
        cap.release()

        console.print(f"[green]Loaded video:[/green] {video_path.name}")
        console.print(
            f"  Resolution: {metadata['width']}x{metadata['height']}, "
            f"FPS: {metadata['fps']:.1f}, "
            f"Duration: {metadata['duration']:.1f}s, "
            f"Frames: {metadata['frame_count']}"
        )
        return metadata

    def extract_frames(
        self,
        video_path: str,
        output_dir: Optional[str] = None,
        max_frames: Optional[int] = None,
        target_fps: Optional[int] = None,
    ) -> list[Path]:
        """Extract frames from video at target FPS."""
        video_path = Path(video_path)
        max_frames = max_frames or self.config.max_frames
        target_fps = target_fps or self.config.target_fps

        if output_dir is None:
            output_dir = self.output_dir / "frames"
        else:
            output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(str(video_path))
        source_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Calculate frame sampling interval
        if target_fps and target_fps < source_fps:
            interval = source_fps / target_fps
        else:
            interval = 1.0

        extracted_frames = []
        frame_idx = 0
        sample_idx = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task("Extracting frames...", total=min(max_frames, total_frames))

            while cap.isOpened() and len(extracted_frames) < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx >= sample_idx * interval:
                    # Resize if needed
                    if self.config.target_resolution:
                        tw, th = self.config.target_resolution
                        h, w = frame.shape[:2]
                        if w != tw or h != th:
                            # Maintain aspect ratio
                            scale = min(tw / w, th / h)
                            new_w, new_h = int(w * scale), int(h * scale)
                            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

                    # Save frame
                    frame_path = output_dir / f"frame_{len(extracted_frames):06d}.png"
                    cv2.imwrite(str(frame_path), frame)
                    extracted_frames.append(frame_path)
                    sample_idx += 1
                    progress.update(task, advance=1)

                frame_idx += 1

        cap.release()
        console.print(f"[green]Extracted {len(extracted_frames)} frames[/green] to {output_dir}")
        return extracted_frames

    def stabilize_video(self, video_path: str, output_path: Optional[str] = None) -> str:
        """Stabilize shaky video using OpenCV."""
        video_path = Path(video_path)
        if output_path is None:
            output_path = str(self.output_dir / f"{video_path.stem}_stabilized.mp4")

        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Read all frames
        frames = []
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()

        if len(frames) < 2:
            console.print("[yellow]Video too short for stabilization[/yellow]")
            return str(video_path)

        # Calculate optical flow between consecutive frames
        transforms = []
        prev_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)

        for i in range(1, len(frames)):
            curr_gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)

            # Detect feature points
            prev_pts = cv2.goodFeaturesToTrack(
                prev_gray, maxCorners=200, qualityLevel=0.01, minDistance=30
            )

            if prev_pts is not None and len(prev_pts) > 0:
                curr_pts, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, curr_gray, prev_pts, None)
                valid = status.ravel() == 1

                if np.sum(valid) >= 3:
                    prev_valid = prev_pts[valid]
                    curr_valid = curr_pts[valid]
                    m, _ = cv2.estimateAffinePartial2D(prev_valid, curr_valid)
                    if m is not None:
                        dx = m[0, 2]
                        dy = m[1, 2]
                        da = np.arctan2(m[1, 0], m[0, 0])
                        transforms.append([dx, dy, da])
                    else:
                        transforms.append([0, 0, 0])
                else:
                    transforms.append([0, 0, 0])
            else:
                transforms.append([0, 0, 0])

            prev_gray = curr_gray

        transforms = np.array(transforms)

        # Compute cumulative trajectory
        trajectory = np.cumsum(transforms, axis=0)

        # Smooth trajectory using moving average
        window = min(30, len(trajectory) // 2)
        if window > 0:
            smoothed = np.copy(trajectory)
            for i in range(3):
                smoothed[:, i] = self._moving_average(trajectory[:, i], window)
            difference = smoothed - trajectory
        else:
            difference = np.zeros_like(transforms)

        # Apply smoothed transforms
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

        out.write(frames[0])
        for i in range(len(transforms)):
            dx = transforms[i, 0] + difference[i, 0]
            dy = transforms[i, 1] + difference[i, 1]
            da = transforms[i, 2] + difference[i, 2]

            m = np.array([
                [np.cos(da), -np.sin(da), dx],
                [np.sin(da), np.cos(da), dy],
            ], dtype=np.float64)

            stabilized = cv2.warpAffine(frames[i + 1], m, (w, h))
            out.write(stabilized)

        out.release()
        console.print(f"[green]Stabilized video saved:[/green] {output_path}")
        return output_path

    @staticmethod
    def _moving_average(data: np.ndarray, window: int) -> np.ndarray:
        """Simple moving average filter."""
        cumsum = np.cumsum(np.insert(data, 0, 0))
        result = np.copy(data)
        for i in range(len(data)):
            start = max(0, i - window)
            end = min(len(data), i + window + 1)
            result[i] = (cumsum[end] - cumsum[start]) / (end - start)
        return result

    def detect_pet_segments(self, frames: list[Path]) -> list[dict]:
        """Detect pet bounding boxes in frames using a lightweight detector."""
        try:
            from torchvision.models.detection import fasterrcnn_mobilenet_v3_large_fpn
            from torchvision import transforms as T
            import torch
        except ImportError:
            console.print("[yellow]torchvision not available, skipping pet detection[/yellow]")
            return [{"bbox": None, "frame": str(f)} for f in frames]

        # Load model
        model = fasterrcnn_mobilenet_v3_large_fpn(pretrained=True)
        model.eval()

        device = self.device
        if device == "mps":
            # FasterRCNN may not fully support MPS, fallback to CPU
            device = "cpu"
        model = model.to(device)

        transform = T.Compose([T.ToTensor()])

        # COCO class IDs for animals
        ANIMAL_CLASSES = {16: "bird", 17: "cat", 18: "dog", 19: "horse", 20: "sheep", 21: "cow"}

        detections = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
        ) as progress:
            task = progress.add_task("Detecting pets...", total=len(frames))

            for frame_path in frames:
                img = cv2.imread(str(frame_path))
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                tensor = transform(img_rgb).unsqueeze(0).to(device)

                with torch.no_grad():
                    outputs = model(tensor)[0]

                best_detection = None
                best_score = 0

                for idx in range(len(outputs["boxes"])):
                    label = outputs["labels"][idx].item()
                    score = outputs["scores"][idx].item()

                    if label in ANIMAL_CLASSES and score > best_score and score > 0.5:
                        best_score = score
                        box = outputs["boxes"][idx].cpu().numpy()
                        best_detection = {
                            "bbox": box.tolist(),
                            "label": ANIMAL_CLASSES[label],
                            "score": score,
                            "frame": str(frame_path),
                        }

                detections.append(best_detection or {"bbox": None, "frame": str(frame_path)})
                progress.update(task, advance=1)

        detected_count = sum(1 for d in detections if d.get("bbox") is not None)
        console.print(f"[green]Pet detected in {detected_count}/{len(frames)} frames[/green]")
        return detections

    def create_video_from_frames(
        self, frames_dir: str, output_path: str, fps: int = 30
    ) -> str:
        """Create video from a directory of frame images."""
        frames_dir = Path(frames_dir)
        frame_files = sorted(frames_dir.glob("*.png"))

        if not frame_files:
            raise FileNotFoundError(f"No PNG frames found in {frames_dir}")

        first_frame = cv2.imread(str(frame_files[0]))
        h, w = first_frame.shape[:2]

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

        for frame_file in frame_files:
            frame = cv2.imread(str(frame_file))
            out.write(frame)

        out.release()
        console.print(f"[green]Video created:[/green] {output_path}")
        return output_path
