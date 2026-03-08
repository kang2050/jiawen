"""
佳文 AI Engine — GPU 服务器重建模块
=====================================
统一接口：本地模式 / 远程 GPU 模式 自动切换

用法：
  - 本地：GPU_SERVER_URL 不配置，使用本地 pipeline
  - 远程：export GPU_SERVER_URL=http://your-gpu-server:8001
          然后重启 api.py，自动走远程模式
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import httpx

# ─── 配置 ────────────────────────────────────────────────────
GPU_SERVER_URL = os.getenv("GPU_SERVER_URL", "").rstrip("/")
USE_NERFSTUDIO  = os.getenv("USE_NERFSTUDIO", "1") == "1"   # 默认用 Nerfstudio
USE_ORIGINAL_3DGS = os.getenv("USE_ORIGINAL_3DGS", "0") == "1"

# 原版 3DGS 代码路径（本机克隆位置）
GAUSSIAN_SPLATTING_DIR = Path(__file__).parent.parent.parent / "gaussian-splatting"

# Nerfstudio venv
NERFSTUDIO_PYTHON = Path(__file__).parent.parent.parent / "nerfstudio-env" / "bin" / "python"
NS_TRAIN = Path(__file__).parent.parent.parent / "nerfstudio-env" / "bin" / "ns-train"
NS_EXPORT = Path(__file__).parent.parent.parent / "nerfstudio-env" / "bin" / "ns-export"


# ─── 远程 GPU 模式 ────────────────────────────────────────────

def reconstruct_remote(images_dir: str, job_id: str, jobs: dict) -> str | None:
    """把照片发给远程 GPU 服务器处理，拉回 GLB。"""
    images_path = Path(images_dir)
    photos = list(images_path.glob("*.jpg")) + list(images_path.glob("*.png")) + list(images_path.glob("*.jpeg"))

    jobs[job_id].update({"progress": 5, "phase": f"上传 {len(photos)} 张照片到 GPU 服务器..."})

    with httpx.Client(timeout=3600) as client:
        files = [("files", (p.name, open(p, "rb"), "image/jpeg")) for p in photos]
        res = client.post(
            f"{GPU_SERVER_URL}/api/process-local",
            files=files,
            data={"pet_type": "dog", "breed": "generic"},
        )
        res.raise_for_status()
        remote_job_id = res.json()["job_id"]

    jobs[job_id].update({"progress": 10, "phase": "GPU 服务器重建中，等待结果..."})

    # 轮询远程状态
    import time
    while True:
        time.sleep(10)
        status_res = httpx.get(f"{GPU_SERVER_URL}/api/status/{remote_job_id}", timeout=30)
        data = status_res.json()
        jobs[job_id].update({
            "progress": data.get("progress", 0),
            "phase": f"[GPU] {data.get('phase', '')}",
        })
        if data["status"] == "done":
            break
        if data["status"] == "error":
            raise RuntimeError(f"远程 GPU 处理失败: {data.get('phase')}")

    # 下载 GLB
    jobs[job_id].update({"progress": 95, "phase": "下载 GLB 文件..."})
    glb_res = httpx.get(f"{GPU_SERVER_URL}{data['glb_url']}", timeout=120)
    glb_res.raise_for_status()

    out_path = Path(tempfile.mkdtemp()) / "jiawen_gpu.glb"
    out_path.write_bytes(glb_res.content)
    return str(out_path)


# ─── Nerfstudio 本地/GPU 模式 ────────────────────────────────

def reconstruct_nerfstudio(images_dir: str, job_id: str, jobs: dict, output_dir: str) -> str | None:
    """
    用 Nerfstudio splatfacto 重建。
    本地: MPS (M2 Mac)
    GPU 服务器: CUDA，速度快 10x

    流程：
      1. ns-process-data images  → COLMAP + transforms.json
      2. ns-train splatfacto     → 训练 Gaussian Splat 模型
      3. ns-export gaussian-splat → 导出 PLY
      4. ply → GLB
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    processed_dir = output_path / "ns_processed"
    ns_output     = output_path / "ns_output"
    ns_env = {**os.environ, "CUDA_VISIBLE_DEVICES": "0"}  # GPU 模式时生效

    # Step 1: ns-process-data（COLMAP 位姿估计，生成 transforms.json）
    jobs[job_id].update({"progress": 8, "phase": "Nerfstudio COLMAP 位姿估计..."})
    process_data_bin = NS_TRAIN.parent / "ns-process-data"
    process_cmd = [
        str(process_data_bin), "images",
        "--data", images_dir,
        "--output-dir", str(processed_dir),
    ]
    result = subprocess.run(process_cmd, capture_output=True, text=True, timeout=1800, env=ns_env)
    if result.returncode != 0:
        raise RuntimeError(f"ns-process-data 失败:\n{result.stderr[-2000:]}")

    # Step 2: ns-train splatfacto
    jobs[job_id].update({"progress": 20, "phase": "Nerfstudio splatfacto 训练中..."})
    train_cmd = [
        str(NS_TRAIN), "splatfacto",
        "--data", str(processed_dir),
        "--output-dir", str(ns_output),
        "--max-num-iterations", "10000",
        "--pipeline.model.cull-alpha-thresh", "0.005",
        "--pipeline.model.use-scale-regularization", "True",
    ]
    result = subprocess.run(train_cmd, capture_output=True, text=True, timeout=7200, env=ns_env)
    if result.returncode != 0:
        raise RuntimeError(f"Nerfstudio 训练失败:\n{result.stderr[-2000:]}")

    # Step 3: ns-export gaussian-splat
    jobs[job_id].update({"progress": 80, "phase": "导出 PLY 点云..."})
    config_files = list(ns_output.rglob("config.yml"))
    if not config_files:
        raise RuntimeError("未找到 Nerfstudio 训练输出 config.yml")
    config_file = config_files[-1]

    export_dir = output_path / "export"
    export_cmd = [
        str(NS_EXPORT), "gaussian-splat",
        "--load-config", str(config_file),
        "--output-dir", str(export_dir),
    ]
    subprocess.run(export_cmd, capture_output=True, timeout=600, env=ns_env)

    # Step 4: PLY → GLB
    ply_files = list(export_dir.glob("*.ply"))
    if ply_files:
        jobs[job_id].update({"progress": 90, "phase": "转换 PLY → GLB..."})
        glb_path = ply_to_glb(str(ply_files[0]), str(export_dir / "jiawen.glb"))
        return glb_path

    return None


# ─── 原版 3DGS 模式（需要 CUDA）────────────────────────────────

def reconstruct_3dgs(images_dir: str, job_id: str, jobs: dict, output_dir: str) -> str | None:
    """
    原版 3D Gaussian Splatting（需要 CUDA GPU）。
    本地 M2 Mac 无法运行，远程 GPU 可用。
    """
    if not GAUSSIAN_SPLATTING_DIR.exists():
        raise RuntimeError(f"原版 3DGS 未克隆: {GAUSSIAN_SPLATTING_DIR}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    jobs[job_id].update({"progress": 8, "phase": "原版 3DGS COLMAP 处理..."})

    train_cmd = [
        "python", str(GAUSSIAN_SPLATTING_DIR / "train.py"),
        "-s", images_dir,
        "-m", str(output_path / "3dgs_output"),
        "--iterations", "30000",
        "--save_iterations", "30000",
        "--quiet",
    ]

    jobs[job_id].update({"progress": 15, "phase": "原版 3DGS 训练中（30,000 次迭代）..."})

    result = subprocess.run(
        train_cmd,
        capture_output=True, text=True, timeout=7200,
        cwd=str(GAUSSIAN_SPLATTING_DIR),
    )
    if result.returncode != 0:
        raise RuntimeError(f"3DGS 训练失败:\n{result.stderr[-2000:]}")

    jobs[job_id].update({"progress": 85, "phase": "导出 PLY..."})

    ply_files = list((output_path / "3dgs_output").rglob("point_cloud.ply"))
    if ply_files:
        glb_path = ply_to_glb(str(sorted(ply_files)[-1]), str(output_path / "jiawen_3dgs.glb"))
        return glb_path

    return None


# ─── PLY → GLB 转换 ──────────────────────────────────────────

def ply_to_glb(ply_path: str, glb_path: str) -> str:
    """将 PLY 点云/网格转换为 GLB（带顶点色）。"""
    try:
        import pygltflib
        import numpy as np

        # 用 trimesh 读 PLY，导出 GLB
        import trimesh
        mesh = trimesh.load(ply_path)
        mesh.export(glb_path, file_type="glb")
        return glb_path
    except Exception as e:
        raise RuntimeError(f"PLY→GLB 转换失败: {e}")


# ─── 主入口：自动选择模式 ─────────────────────────────────────

def run_reconstruction(images_dir: str, job_id: str, jobs: dict, output_dir: str) -> str | None:
    """
    自动选择重建方式：
    1. GPU_SERVER_URL 配置了 → 远程 GPU 模式
    2. USE_ORIGINAL_3DGS=1    → 本地原版 3DGS（需要 CUDA）
    3. 默认                   → Nerfstudio splatfacto（支持 MPS/CUDA）
    """
    if GPU_SERVER_URL:
        jobs[job_id].update({"phase": f"远程 GPU 模式: {GPU_SERVER_URL}"})
        return reconstruct_remote(images_dir, job_id, jobs)

    if USE_ORIGINAL_3DGS:
        return reconstruct_3dgs(images_dir, job_id, jobs, output_dir)

    return reconstruct_nerfstudio(images_dir, job_id, jobs, output_dir)
