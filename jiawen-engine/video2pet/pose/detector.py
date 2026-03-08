"""
Pet Pose Detector
==================
2D keypoint detection for animals using multiple backends:
- ViTPose (recommended for accuracy)
- Apple Vision Framework (macOS native, fast)
- Lightweight fallback (torchvision keypoint RCNN)

Outputs standardized 2D keypoints for downstream 3D lifting.
"""

import platform
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import torch
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()

# Standard animal keypoint definition (24 points)
# Based on SMAL model joint ordering
ANIMAL_KEYPOINTS = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "throat", "withers", "tail_base",
    "left_front_paw", "right_front_paw", "left_back_paw", "right_back_paw",
    "left_front_elbow", "right_front_elbow", "left_back_knee", "right_back_knee",
    "left_front_shoulder", "right_front_shoulder", "left_back_hip", "right_back_hip",
    "spine_mid", "spine_front", "spine_back", "chin",
]


class PoseDetector:
    """Detect 2D animal keypoints from images/frames."""

    def __init__(self, config):
        self.config = config.pose
        self.device = config.device
        self.model = None
        self._backend = self.config.model_name

    def _load_model(self):
        """Lazy-load the detection model."""
        if self.model is not None:
            return

        if self._backend == "apple_vision" and platform.system() == "Darwin":
            console.print("[cyan]Using Apple Vision Framework for pose detection[/cyan]")
            self.model = "apple_vision"
            return

        # Default: use torchvision KeypointRCNN as a starting point
        console.print("[cyan]Loading pose detection model...[/cyan]")
        try:
            from torchvision.models.detection import keypointrcnn_resnet50_fpn
            self.model = keypointrcnn_resnet50_fpn(pretrained=True)
            self.model.eval()

            # For MPS, some ops may not be supported; fallback to CPU
            device = self.device if self.device != "mps" else "cpu"
            self.model = self.model.to(device)
            self._device_actual = device
            console.print(f"[green]Pose model loaded on {device}[/green]")
        except Exception as e:
            console.print(f"[yellow]Failed to load keypoint model: {e}[/yellow]")
            console.print("[yellow]Falling back to basic detection[/yellow]")
            self.model = "basic"

    def detect_batch(self, frame_paths: list[Path]) -> list[dict]:
        """Detect keypoints in a batch of frames.

        Returns:
            List of detection results, each containing:
            - keypoints: np.ndarray of shape (N, 3) where N is num_keypoints, cols are [x, y, confidence]
            - bbox: [x1, y1, x2, y2] bounding box
            - score: detection confidence
        """
        self._load_model()

        results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
        ) as progress:
            task = progress.add_task("Detecting poses...", total=len(frame_paths))

            for frame_path in frame_paths:
                result = self._detect_single(frame_path)
                results.append(result)
                progress.update(task, advance=1)

        valid_count = sum(1 for r in results if r["keypoints"] is not None)
        console.print(f"[green]Pose detected in {valid_count}/{len(results)} frames[/green]")
        return results

    def _detect_single(self, frame_path: Path) -> dict:
        """Detect keypoints in a single frame."""
        img = cv2.imread(str(frame_path))
        if img is None:
            return {"keypoints": None, "bbox": None, "score": 0.0, "frame": str(frame_path)}

        if self.model == "apple_vision":
            return self._detect_apple_vision(img, frame_path)
        elif self.model == "basic":
            return self._detect_basic(img, frame_path)
        else:
            return self._detect_torchvision(img, frame_path)

    def _detect_torchvision(self, img: np.ndarray, frame_path: Path) -> dict:
        """Detect using torchvision KeypointRCNN."""
        from torchvision import transforms as T

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        tensor = T.ToTensor()(img_rgb).unsqueeze(0).to(self._device_actual)

        with torch.no_grad():
            outputs = self.model(tensor)[0]

        # Find best person/animal detection
        # KeypointRCNN is trained on COCO persons, but we can use it as a starting point
        # and map to animal keypoints
        if len(outputs["boxes"]) == 0:
            return {"keypoints": None, "bbox": None, "score": 0.0, "frame": str(frame_path)}

        best_idx = outputs["scores"].argmax().item()
        score = outputs["scores"][best_idx].item()

        if score < self.config.confidence_threshold:
            return {"keypoints": None, "bbox": None, "score": score, "frame": str(frame_path)}

        keypoints = outputs["keypoints"][best_idx].cpu().numpy()  # (17, 3) for COCO
        bbox = outputs["boxes"][best_idx].cpu().numpy().tolist()

        # Map COCO person keypoints to animal keypoints (approximate)
        animal_kps = self._map_to_animal_keypoints(keypoints, img.shape)

        return {
            "keypoints": animal_kps,
            "bbox": bbox,
            "score": score,
            "frame": str(frame_path),
        }

    def _detect_apple_vision(self, img: np.ndarray, frame_path: Path) -> dict:
        """Detect using Apple Vision Framework (macOS only).

        Uses VNDetectAnimalBodyPoseRequest which natively supports cats and dogs.
        """
        try:
            import objc
            from Foundation import NSData
            from Vision import (
                VNDetectAnimalBodyPoseRequest,
                VNImageRequestHandler,
            )

            # Convert image to NSData
            _, buffer = cv2.imencode(".jpg", img)
            ns_data = NSData.dataWithBytes_length_(buffer.tobytes(), len(buffer))

            # Create request handler
            handler = VNImageRequestHandler.alloc().initWithData_options_(ns_data, None)
            request = VNDetectAnimalBodyPoseRequest.alloc().init()

            # Perform detection
            success, error = handler.performRequests_error_([request], None)

            if not success or not request.results():
                return {"keypoints": None, "bbox": None, "score": 0.0, "frame": str(frame_path)}

            # Get first result
            observation = request.results()[0]
            h, w = img.shape[:2]

            # Extract keypoints
            recognized_points = observation.recognizedPoints()
            animal_kps = np.zeros((len(ANIMAL_KEYPOINTS), 3))

            # Map Vision framework joint names to our standard
            vision_to_standard = {
                "nose": 0, "leftEye": 1, "rightEye": 2,
                "leftEar": 3, "rightEar": 4,
                "neck": 5, "tailBase": 7,
                "leftFrontPaw": 8, "rightFrontPaw": 9,
                "leftBackPaw": 10, "rightBackPaw": 11,
                "leftFrontElbow": 12, "rightFrontElbow": 13,
                "leftBackKnee": 14, "rightBackKnee": 15,
                "leftFrontShoulder": 16, "rightFrontShoulder": 17,
                "leftBackHip": 18, "rightBackHip": 19,
            }

            for joint_name, std_idx in vision_to_standard.items():
                if joint_name in recognized_points:
                    point = recognized_points[joint_name]
                    x = point.x() * w
                    y = (1.0 - point.y()) * h  # Vision uses bottom-left origin
                    conf = point.confidence()
                    animal_kps[std_idx] = [x, y, conf]

            # Compute bounding box from keypoints
            valid_kps = animal_kps[animal_kps[:, 2] > 0.1]
            if len(valid_kps) > 0:
                x1, y1 = valid_kps[:, :2].min(axis=0)
                x2, y2 = valid_kps[:, :2].max(axis=0)
                # Add padding
                pad = max(x2 - x1, y2 - y1) * 0.1
                bbox = [x1 - pad, y1 - pad, x2 + pad, y2 + pad]
            else:
                bbox = None

            return {
                "keypoints": animal_kps,
                "bbox": bbox,
                "score": float(observation.confidence()),
                "frame": str(frame_path),
            }

        except ImportError:
            console.print("[yellow]Apple Vision not available, falling back[/yellow]")
            self.model = "basic"
            return self._detect_basic(img, frame_path)

    def _detect_basic(self, img: np.ndarray, frame_path: Path) -> dict:
        """Basic detection fallback using contour analysis."""
        h, w = img.shape[:2]

        # Simple approach: detect largest moving object
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (21, 21), 0)

        # Use adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return {"keypoints": None, "bbox": None, "score": 0.0, "frame": str(frame_path)}

        # Get largest contour
        largest = max(contours, key=cv2.contourArea)
        x, y, cw, ch = cv2.boundingRect(largest)

        # Generate approximate keypoints from bounding box
        animal_kps = np.zeros((len(ANIMAL_KEYPOINTS), 3))
        # Place approximate keypoints based on typical quadruped proportions
        cx, cy = x + cw / 2, y + ch / 2
        animal_kps[0] = [x + cw * 0.85, y + ch * 0.2, 0.3]  # nose
        animal_kps[5] = [x + cw * 0.7, y + ch * 0.3, 0.3]   # throat
        animal_kps[7] = [x + cw * 0.1, y + ch * 0.4, 0.3]    # tail_base
        animal_kps[8] = [x + cw * 0.7, y + ch * 0.9, 0.3]    # left_front_paw
        animal_kps[9] = [x + cw * 0.6, y + ch * 0.9, 0.3]    # right_front_paw
        animal_kps[10] = [x + cw * 0.2, y + ch * 0.9, 0.3]   # left_back_paw
        animal_kps[11] = [x + cw * 0.3, y + ch * 0.9, 0.3]   # right_back_paw

        return {
            "keypoints": animal_kps,
            "bbox": [x, y, x + cw, y + ch],
            "score": 0.3,
            "frame": str(frame_path),
        }

    @staticmethod
    def _map_to_animal_keypoints(coco_kps: np.ndarray, img_shape: tuple) -> np.ndarray:
        """Map COCO person keypoints to animal keypoint format.

        This is an approximate mapping for initialization purposes.
        The 3D fitting stage will refine these.
        """
        animal_kps = np.zeros((len(ANIMAL_KEYPOINTS), 3))

        # COCO person: nose(0), left_eye(1), right_eye(2), left_ear(3), right_ear(4),
        # left_shoulder(5), right_shoulder(6), left_elbow(7), right_elbow(8),
        # left_wrist(9), right_wrist(10), left_hip(11), right_hip(12),
        # left_knee(13), right_knee(14), left_ankle(15), right_ankle(16)

        mapping = {
            0: 0,   # nose -> nose
            1: 1,   # left_eye -> left_eye
            2: 2,   # right_eye -> right_eye
            3: 3,   # left_ear -> left_ear
            4: 4,   # right_ear -> right_ear
            5: 16,  # left_shoulder -> left_front_shoulder
            6: 17,  # right_shoulder -> right_front_shoulder
            7: 12,  # left_elbow -> left_front_elbow
            8: 13,  # right_elbow -> right_front_elbow
            9: 8,   # left_wrist -> left_front_paw
            10: 9,  # right_wrist -> right_front_paw
            11: 18, # left_hip -> left_back_hip
            12: 19, # right_hip -> right_back_hip
            13: 14, # left_knee -> left_back_knee
            14: 15, # right_knee -> right_back_knee
            15: 10, # left_ankle -> left_back_paw
            16: 11, # right_ankle -> right_back_paw
        }

        for coco_idx, animal_idx in mapping.items():
            if coco_idx < len(coco_kps):
                animal_kps[animal_idx] = coco_kps[coco_idx]

        return animal_kps
