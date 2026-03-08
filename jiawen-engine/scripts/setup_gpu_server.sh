#!/bin/bash
# ============================================================
# 佳文数字生命 — GPU 服务器一键安装脚本
# 适用：Ubuntu 20.04/22.04 + NVIDIA GPU (RTX 3090/4090/A100)
# 运行方式：bash setup_gpu_server.sh
# ============================================================

set -e

echo "========================================"
echo "  佳文 AI Engine — GPU Server Setup"
echo "========================================"

# ─── 1. 系统依赖 ─────────────────────────────────────────────
echo "[1/7] 安装系统依赖..."
apt-get update -qq
apt-get install -y -qq \
    git curl wget unzip \
    python3.10 python3.10-venv python3-pip \
    cmake build-essential ninja-build \
    libboost-all-dev libeigen3-dev \
    libsuitesparse-dev libfreeimage-dev \
    libgoogle-glog-dev libgflags-dev \
    libglew-dev qtbase5-dev libqt5opengl5-dev \
    ffmpeg libavcodec-dev libavformat-dev \
    colmap

# ─── 2. Python 环境 ──────────────────────────────────────────
echo "[2/7] 创建 Python 3.10 虚拟环境..."
python3.10 -m venv /opt/jiawen-env
source /opt/jiawen-env/bin/activate
pip install --upgrade pip wheel setuptools

# ─── 3. PyTorch (CUDA) ───────────────────────────────────────
echo "[3/7] 安装 PyTorch CUDA 版本..."
# 自动检测 CUDA 版本
CUDA_VER=$(nvcc --version 2>/dev/null | grep -oP "release \K[0-9]+\.[0-9]+" | head -1)
echo "  检测到 CUDA: $CUDA_VER"

if [[ "$CUDA_VER" == "12"* ]]; then
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 -q
elif [[ "$CUDA_VER" == "11"* ]]; then
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 -q
else
    echo "  未检测到 CUDA，安装 CPU 版本（不推荐）"
    pip install torch torchvision torchaudio -q
fi

# ─── 4. Nerfstudio ───────────────────────────────────────────
echo "[4/7] 安装 Nerfstudio..."
pip install nerfstudio -q
# 安装 COLMAP 处理器
pip install pycolmap -q

# 验证
ns-train --help > /dev/null 2>&1 && echo "  ✓ Nerfstudio 安装成功" || echo "  ✗ Nerfstudio 安装失败"

# ─── 5. 原版 3D Gaussian Splatting ───────────────────────────
echo "[5/7] 安装原版 3DGS..."
cd /opt
git clone https://github.com/graphdeco-inria/gaussian-splatting.git --recursive --depth 1
cd gaussian-splatting

# 安装 3DGS 依赖（含 CUDA submodule）
pip install plyfile tqdm -q
pip install submodules/diff-gaussian-rasterization -q
pip install submodules/simple-knn -q
echo "  ✓ 原版 3DGS 安装成功"

# ─── 6. 骨骼绑定工具 ─────────────────────────────────────────
echo "[6/7] 安装骨骼绑定相关工具..."
pip install \
    pygltflib \       # 真正的 GLB 骨骼导出
    trimesh \
    open3d \
    scipy \
    numpy \
    opencv-python \
    Pillow \
    fastapi \
    uvicorn \
    python-multipart \
    rich \
    typer -q

# SMAL 模型（四足动物参数化模型）
echo "  ⚠ SMAL 模型需手动下载："
echo "    1. 访问 https://smal.is.tue.mpg.de/ 注册下载"
echo "    2. 将 smal_CVPR2018.pkl 放到 /opt/jiawen-smal/smal_CVPR2018.pkl"

# ─── 7. 部署佳文 API 服务 ────────────────────────────────────
echo "[7/7] 部署 jiawen-engine API..."
cd /opt
# 从本地 Mac 传过来的代码（或 git clone）
if [ -d "/opt/jiawen-engine" ]; then
    cd /opt/jiawen-engine
    pip install -e . -q
    echo "  ✓ jiawen-engine 已安装"
else
    echo "  ⚠ 请将 jiawen-engine 目录上传到 /opt/jiawen-engine"
    echo "    scp -r ./jiawen-engine user@GPU_SERVER:/opt/"
fi

# ─── 完成 ────────────────────────────────────────────────────
echo ""
echo "========================================"
echo "  安装完成！"
echo ""
echo "  启动 API 服务："
echo "    source /opt/jiawen-env/bin/activate"
echo "    cd /opt/jiawen-engine"
echo "    python web/api.py"
echo ""
echo "  端口: 8001 (API) | 8000 (Gradio)"
echo "========================================"
