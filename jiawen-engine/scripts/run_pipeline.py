#!/usr/bin/env python3
"""
Video2Pet Pipeline Runner
==========================
Standalone script to run the complete pipeline.

Usage:
    python scripts/run_pipeline.py --video path/to/video.mp4
    python scripts/run_pipeline.py --video path/to/video.mp4 --pet-type dog --breed golden_retriever
    python scripts/run_pipeline.py --prompt "A corgi running in a park" --fast
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from video2pet.config import Video2PetConfig, load_config, detect_device, detect_platform
from video2pet.pipeline import Video2PetPipeline


def main():
    parser = argparse.ArgumentParser(description="Video2Pet Pipeline")
    parser.add_argument("--video", "-v", type=str, help="Path to input pet video")
    parser.add_argument("--prompt", "-p", type=str, help="Text prompt for AI video generation")
    parser.add_argument("--pet-type", "-t", type=str, default="dog", help="Pet type (dog/cat)")
    parser.add_argument("--breed", "-b", type=str, default="generic", help="Pet breed")
    parser.add_argument("--output", "-o", type=str, default="output", help="Output directory")
    parser.add_argument("--config", "-c", type=str, help="Config YAML file")
    parser.add_argument("--device", "-d", type=str, help="Device (cuda/mps/cpu)")
    parser.add_argument("--fast", action="store_true", help="Fast mode (fewer iterations)")
    parser.add_argument("--skip-reconstruction", action="store_true", help="Skip 3D reconstruction")
    parser.add_argument("--skip-rigging", action="store_true", help="Skip rigging")
    parser.add_argument("--info", action="store_true", help="Show system info and exit")

    args = parser.parse_args()

    if args.info:
        platform_info = detect_platform()
        device = detect_device()
        print(f"\nVideo2Pet System Info")
        print(f"  Platform: {platform_info['system']} ({platform_info['machine']})")
        print(f"  Apple Silicon: {platform_info['is_apple_silicon']}")
        print(f"  Device: {device}")
        print(f"  Python: {platform_info['python_version']}")
        return

    if not args.video and not args.prompt:
        parser.error("Either --video or --prompt is required")

    # Load config
    config = load_config(args.config)
    config.project_dir = args.output

    if args.device:
        config.device = args.device

    if args.fast:
        config.reconstruction.gs_iterations = 5000
        config.video.max_frames = 100

    # Run pipeline
    pipeline = Video2PetPipeline(config)
    results = pipeline.run(
        video_path=args.video,
        prompt=args.prompt,
        pet_type=args.pet_type,
        breed=args.breed,
        skip_reconstruction=args.skip_reconstruction,
        skip_rigging=args.skip_rigging,
    )

    print("\nDone! Check the output directory for results.")


if __name__ == "__main__":
    main()
