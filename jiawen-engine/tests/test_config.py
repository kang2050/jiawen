"""Tests for Video2Pet configuration."""

import pytest
from video2pet.config import Video2PetConfig, detect_device, detect_platform


def test_default_config():
    """Test default configuration creation."""
    config = Video2PetConfig()
    assert config.project_dir == "output"
    assert config.video.max_frames == 300
    assert config.video.target_fps == 15
    assert config.pose.confidence_threshold == 0.5
    assert config.reconstruction.gs_iterations == 30000


def test_device_detection():
    """Test device auto-detection."""
    device = detect_device()
    assert device in ("cuda", "mps", "cpu")


def test_platform_detection():
    """Test platform detection."""
    info = detect_platform()
    assert "system" in info
    assert "machine" in info
    assert "python_version" in info
    assert "is_apple_silicon" in info


def test_config_modification():
    """Test config modification."""
    config = Video2PetConfig()
    config.video.max_frames = 100
    config.reconstruction.gs_iterations = 5000
    assert config.video.max_frames == 100
    assert config.reconstruction.gs_iterations == 5000
