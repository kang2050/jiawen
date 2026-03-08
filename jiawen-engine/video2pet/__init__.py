"""
Video2Pet
==========
End-to-end pipeline: Pet Video → 3D Pose Extraction → Digital Twin Asset Generation

Based on video2robot (https://github.com/AIM-Intelligence/video2robot)
Adapted for pet 3D digitization and digital twin creation.

Quick Start:
    from video2pet.pipeline import Video2PetPipeline
    
    pipeline = Video2PetPipeline()
    results = pipeline.run(video_path="my_pet.mp4", pet_type="dog")
"""

__version__ = "0.1.0"
__author__ = "Video2Pet Team"
