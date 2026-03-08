"""Tests for skeleton and rigging system."""

import numpy as np
import pytest
from video2pet.config import Video2PetConfig
from video2pet.rigging.skeleton import (
    BREED_SCALES,
    QUADRUPED_SKELETON,
    SkeletonBuilder,
    SkinningEngine,
)


def test_quadruped_skeleton_structure():
    """Test quadruped skeleton has correct structure."""
    skeleton = QUADRUPED_SKELETON
    assert "joints" in skeleton
    assert len(skeleton["joints"]) == 28  # 28 joints for quadruped

    # Check root joint
    root = skeleton["joints"][0]
    assert root["name"] == "root"
    assert root["parent"] == -1

    # Check all joints have required fields
    for joint in skeleton["joints"]:
        assert "name" in joint
        assert "parent" in joint
        assert "position" in joint
        assert len(joint["position"]) == 3


def test_breed_scales():
    """Test breed scale presets."""
    assert "generic" in BREED_SCALES
    assert "golden_retriever" in BREED_SCALES
    assert "corgi" in BREED_SCALES

    # Corgi should have short legs
    assert BREED_SCALES["corgi"]["leg_length"] < BREED_SCALES["generic"]["leg_length"]


def test_skeleton_builder():
    """Test skeleton creation."""
    config = Video2PetConfig()
    builder = SkeletonBuilder(config)

    skeleton = builder.create_skeleton(pet_type="dog", breed="generic")
    assert "joints" in skeleton
    assert "bind_matrices" in skeleton
    assert len(skeleton["bind_matrices"]) == len(skeleton["joints"])


def test_skinning_weights():
    """Test skinning weight computation."""
    config = Video2PetConfig()
    engine = SkinningEngine(config)

    # Create dummy mesh and skeleton
    mesh_data = {
        "vertices": np.random.randn(100, 3).tolist(),
    }
    skeleton = {
        "joints": [
            {"name": "root", "parent": -1, "position": [0, 0, 0]},
            {"name": "spine", "parent": 0, "position": [0, 0.2, 0]},
            {"name": "head", "parent": 1, "position": [0, 0.4, 0]},
        ]
    }

    weights = engine.compute_weights(mesh_data, skeleton)
    assert weights.shape == (100, 3)

    # Weights should sum to 1 per vertex
    np.testing.assert_allclose(weights.sum(axis=1), 1.0, atol=1e-6)
