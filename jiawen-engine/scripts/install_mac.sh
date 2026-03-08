#!/bin/bash
# ============================================================
# Video2Pet - macOS (Apple Silicon) Installation Script
# ============================================================
# Tested on: Mac M2 Max 64GB, macOS Sonoma/Sequoia
# 
# Usage:
#   chmod +x scripts/install_mac.sh
#   ./scripts/install_mac.sh
# ============================================================

set -e

echo "╔══════════════════════════════════════════════════╗"
echo "║   Video2Pet - macOS Apple Silicon Installer      ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ─── Check Prerequisites ────────────────────────────────────────────

echo "▶ Checking prerequisites..."

# Check macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "❌ This script is for macOS only."
    exit 1
fi

# Check Apple Silicon
if [[ "$(uname -m)" != "arm64" ]]; then
    echo "⚠️  Warning: Not running on Apple Silicon. Some features may be slower."
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Install with: brew install python@3.11"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Python: $PYTHON_VERSION"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Install with: python3 -m ensurepip"
    exit 1
fi

# ─── Create Virtual Environment ─────────────────────────────────────

echo ""
echo "▶ Creating virtual environment..."

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "  Created .venv"
else
    echo "  .venv already exists"
fi

source .venv/bin/activate
echo "  Activated virtual environment"

# Upgrade pip
pip install --upgrade pip setuptools wheel

# ─── Install PyTorch (Apple Silicon Optimized) ──────────────────────

echo ""
echo "▶ Installing PyTorch with MPS support..."

pip install torch torchvision torchaudio

# Verify MPS
python3 -c "
import torch
print(f'  PyTorch: {torch.__version__}')
print(f'  MPS available: {torch.backends.mps.is_available()}')
print(f'  MPS built: {torch.backends.mps.is_built()}')
" || echo "  ⚠️ MPS verification failed, will fall back to CPU"

# ─── Install Core Dependencies ──────────────────────────────────────

echo ""
echo "▶ Installing core dependencies..."

pip install \
    numpy>=1.24 \
    scipy>=1.11 \
    opencv-python-headless>=4.8 \
    Pillow>=10.0 \
    rich>=13.0 \
    typer>=0.9 \
    pyyaml>=6.0 \
    python-dotenv>=1.0

# ─── Install ML Dependencies ────────────────────────────────────────

echo ""
echo "▶ Installing ML dependencies..."

pip install \
    transformers>=4.35 \
    timm>=0.9 \
    mmcv-lite>=2.0 2>/dev/null || pip install mmcv>=2.0 2>/dev/null || echo "  ⚠️ mmcv optional, skipping"

# ─── Install 3D Dependencies ────────────────────────────────────────

echo ""
echo "▶ Installing 3D dependencies..."

pip install \
    trimesh>=4.0 \
    scikit-image>=0.21 \
    open3d>=0.17 2>/dev/null || echo "  ⚠️ Open3D install failed (optional, Poisson reconstruction)"

# ─── Install Visualization ──────────────────────────────────────────

echo ""
echo "▶ Installing visualization tools..."

pip install \
    viser>=0.1 2>/dev/null || echo "  ⚠️ viser install failed (optional, 3D viewer)"

pip install \
    matplotlib>=3.7 \
    plotly>=5.15

# ─── Install Web UI ─────────────────────────────────────────────────

echo ""
echo "▶ Installing web UI..."

pip install \
    gradio>=4.0 \
    fastapi>=0.100 \
    uvicorn>=0.23

# ─── Install Video2Pet Package ──────────────────────────────────────

echo ""
echo "▶ Installing Video2Pet..."

pip install -e .

# ─── Install COLMAP (Optional) ──────────────────────────────────────

echo ""
echo "▶ Checking COLMAP..."

if command -v colmap &> /dev/null; then
    echo "  COLMAP found: $(colmap --version 2>/dev/null || echo 'installed')"
else
    echo "  COLMAP not found. For best SfM results, install with:"
    echo "    brew install colmap"
    echo "  (Optional: lightweight SfM will be used as fallback)"
fi

# ─── Create Model Directories ───────────────────────────────────────

echo ""
echo "▶ Creating model directories..."

mkdir -p models/smal
mkdir -p models/pose
mkdir -p output

# ─── Verify Installation ────────────────────────────────────────────

echo ""
echo "▶ Verifying installation..."

python3 -c "
import sys
print(f'Python: {sys.version}')

import torch
print(f'PyTorch: {torch.__version__} (MPS: {torch.backends.mps.is_available()})')

import cv2
print(f'OpenCV: {cv2.__version__}')

import numpy
print(f'NumPy: {numpy.__version__}')

import trimesh
print(f'Trimesh: {trimesh.__version__}')

try:
    import gradio
    print(f'Gradio: {gradio.__version__}')
except:
    print('Gradio: not installed')

print()
print('✅ All core dependencies installed successfully!')
"

# ─── Done ────────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   ✅ Installation Complete!                      ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║                                                  ║"
echo "║   Activate environment:                          ║"
echo "║     source .venv/bin/activate                    ║"
echo "║                                                  ║"
echo "║   Quick start:                                   ║"
echo "║     video2pet info                               ║"
echo "║     video2pet run -v my_pet.mp4                  ║"
echo "║     video2pet serve                              ║"
echo "║                                                  ║"
echo "║   Optional: Install COLMAP for better SfM        ║"
echo "║     brew install colmap                          ║"
echo "║                                                  ║"
echo "║   Optional: Download SMAL model                  ║"
echo "║     See README.md for instructions               ║"
echo "║                                                  ║"
echo "╚══════════════════════════════════════════════════╝"
