# Video2Pet — 从视频到宠物数字孪生

> 基于 [video2robot](https://github.com/AIM-Intelligence/video2robot) 的端到端技术路径，创新性地应用于宠物3D数字化领域。
> 从一段宠物视频出发，自动完成姿态提取、3D重建、骨骼绑定与动画生成，输出可用于AR/VR、游戏引擎、元宇宙的高精度宠物数字孪生资产。

---

## 项目概览

Video2Pet 是一个端到端的宠物3D数字化流水线，将 video2robot 的核心思路——"视频 → 姿态提取 → 3D重建 → 动作重定向"——从机器人领域迁移到宠物数字孪生场景。整个流水线包含 11 个阶段，从视频输入到最终的 GLB/USDZ/FBX 资产导出，全部自动化完成。

### 技术架构

```
┌──────────────────────────────────────────────────────────────────┐
│                     Video2Pet Pipeline                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────┐  │
│  │  Video   │──▶│  Pose    │──▶│   3D     │──▶│  Rigging &   │  │
│  │  Input   │   │  Estim.  │   │  Recon.  │   │  Animation   │  │
│  └─────────┘   └──────────┘   └──────────┘   └──────────────┘  │
│       │              │              │                │           │
│  ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────┐  │
│  │ Upload  │   │ ViTPose  │   │ Gaussian │   │  Quadruped   │  │
│  │ or Veo/ │   │ + SMAL   │   │ Splatting│   │  Skeleton    │  │
│  │ Sora AI │   │ 3D Lift  │   │ + Mesh   │   │  + Skinning  │  │
│  └─────────┘   └──────────┘   └──────────┘   └──────────────┘  │
│                                                      │           │
│                                              ┌──────────────┐   │
│                                              │   Export      │   │
│                                              │ GLB/USDZ/FBX │   │
│                                              └──────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 核心特性

| 特性 | 说明 |
|------|------|
| **端到端自动化** | 视频输入 → 数字孪生资产，全流程无需人工干预 |
| **Apple Silicon 优化** | 原生支持 MPS 后端，充分利用 M2 Max 的 GPU 和统一内存 |
| **AI 视频生成** | 可选接入 Google Veo 2.0 / OpenAI Sora 生成宠物视频 |
| **多品种支持** | 内置犬类、猫类多品种骨骼比例预设 |
| **3D Gaussian Splatting** | 基于最新 3DGS 技术进行高质量3D重建 |
| **自动骨骼绑定** | 四足动物骨骼模板 + 自动蒙皮权重计算 |
| **多格式导出** | GLB、USDZ（Apple AR）、FBX（游戏引擎）、OBJ |
| **Web UI** | Gradio 可视化界面，支持拖拽上传和实时预览 |
| **CLI 工具** | 完整命令行接口，支持批处理和脚本集成 |

---

## 系统要求

### 硬件要求

| 配置 | 最低要求 | 推荐配置 |
|------|---------|---------|
| **处理器** | Apple M1 / Intel i7 | Apple M2 Max / M3 Pro |
| **内存** | 16 GB | 64 GB |
| **存储** | 20 GB 可用空间 | 50 GB SSD |
| **GPU** | MPS / CUDA 可选 | M2 Max GPU (38核) |

### 软件要求

| 软件 | 版本 | 必需 |
|------|------|------|
| macOS | 13.0+ (Ventura) | 是 |
| Python | 3.10 - 3.12 | 是 |
| Homebrew | 最新版 | 推荐 |
| COLMAP | 3.8+ | 可选（有轻量替代） |
| Blender | 3.6+ | 可选（FBX导出） |

---

## 快速安装

### 方式一：一键安装脚本（推荐）

```bash
# 克隆项目
git clone https://github.com/your-org/video2pet.git
cd video2pet

# 运行安装脚本
chmod +x scripts/install_mac.sh
./scripts/install_mac.sh
```

安装脚本会自动完成以下操作：
1. 检测系统环境和 Apple Silicon 支持
2. 创建 Python 虚拟环境
3. 安装 PyTorch（MPS 加速版）
4. 安装所有核心依赖和可选依赖
5. 验证安装结果

### 方式二：手动安装

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装 PyTorch（Apple Silicon）
pip install torch torchvision torchaudio

# 安装项目
pip install -e .

# 安装可选依赖
pip install open3d viser gradio
```

### 方式三：使用 Makefile

```bash
make install      # 安装核心依赖
make install-dev  # 安装开发依赖
make setup        # 完整安装（含模型下载提示）
```

### 可选：安装 COLMAP

COLMAP 用于 Structure from Motion（SfM），提供更精确的相机位姿估计。如果不安装，系统会使用内置的轻量级 SfM 替代方案。

```bash
brew install colmap
```

### 可选：下载 SMAL 模型

SMAL 是四足动物的参数化3D模型，类似于人体的 SMPL。下载后放入 `models/smal/` 目录：

1. 访问 [SMAL 官网](https://smal.is.tue.mpg.de/) 注册并下载
2. 将 `smal_CVPR2018.pkl` 放入 `models/smal/`

> 注意：不下载 SMAL 模型也可以运行，系统会使用简化的参数化模型。

---

## 快速开始

### 1. 检查系统信息

```bash
source .venv/bin/activate
video2pet info
```

输出示例：
```
Video2Pet System Information

  Platform: Darwin (arm64)
  Python: 3.11.7
  Apple Silicon: Yes
  Compute Device: mps

Dependencies:
  ✓ PyTorch: 2.2.0
  ✓ TorchVision: 0.17.0
  ✓ OpenCV: 4.9.0
  ✓ Trimesh: 4.1.0
  ✓ Gradio: 4.15.0
```

### 2. 从视频生成数字孪生

```bash
# 基础用法
video2pet run --video my_dog.mp4

# 指定宠物类型和品种
video2pet run --video my_corgi.mp4 --pet-type dog --breed corgi

# 快速模式（减少迭代次数，适合预览）
video2pet run --video my_cat.mp4 --pet-type cat --fast

# 指定输出目录
video2pet run --video my_pet.mp4 --output my_pet_3d/
```

### 3. 使用 AI 生成视频（需要 API Key）

```bash
# 使用文字描述生成视频并处理
video2pet run --prompt "A golden retriever playing fetch in a sunny park" \
              --pet-type dog --breed golden_retriever
```

### 4. 分步执行

```bash
# 仅提取帧
video2pet extract-frames --video my_pet.mp4 --output frames/ --fps 15

# 仅检测姿态
video2pet detect-pose --frames frames/ --output poses/

# 可视化结果
video2pet visualize --mesh output/mesh/pet_mesh.obj
```

### 5. 启动 Web 界面

```bash
video2pet serve --port 8000
# 打开浏览器访问 http://localhost:8000
```

### 6. Python API 调用

```python
from video2pet import Video2PetPipeline, Video2PetConfig

# 创建配置
config = Video2PetConfig()
config.device = "mps"  # Apple Silicon
config.reconstruction.gs_iterations = 10000  # 快速模式

# 创建流水线
pipeline = Video2PetPipeline(config)

# 运行
results = pipeline.run(
    video_path="my_dog.mp4",
    pet_type="dog",
    breed="golden_retriever",
)

# 查看结果
print(f"导出文件: {results['exports']}")
print(f"网格顶点数: {results['mesh']['n_vertices']}")
```

---

## 流水线详解

### 阶段 1-2：视频输入与帧提取

支持两种输入方式：直接上传视频文件，或通过 AI（Veo/Sora）从文字描述生成视频。视频经过稳定化处理后，按目标帧率提取关键帧。

```python
# 视频处理配置
config.video.max_frames = 300      # 最大帧数
config.video.target_fps = 15       # 目标帧率
config.video.target_resolution = [1280, 720]  # 目标分辨率
config.video.stabilize = True      # 视频稳定
```

### 阶段 3-5：姿态估计（2D → 3D）

采用两阶段姿态估计：首先使用 ViTPose-Animal 检测2D关键点，然后通过 SMAL 参数化模型将2D关键点提升到3D空间。这一步借鉴了 video2robot 中 PromptHMR 的思路，但针对四足动物进行了适配。

| 模型 | 用途 | 精度 | 速度 |
|------|------|------|------|
| ViTPose-Animal | 2D 关键点检测 | 高 | 快 |
| Apple Vision (macOS) | 2D 检测备选 | 中 | 快 |
| SMAL Fitting | 2D→3D 提升 | 高 | 中 |

### 阶段 6-8：3D 重建

采用 Structure from Motion + 3D Gaussian Splatting 的组合方案。SfM 提供相机位姿和稀疏点云，3DGS 在此基础上训练高质量的3D表示，最后通过 Marching Cubes 提取三角网格。

```python
# 重建配置
config.reconstruction.gs_iterations = 30000   # GS 训练迭代
config.reconstruction.mesh_resolution = 256   # 网格分辨率
config.reconstruction.texture_resolution = 2048  # 纹理分辨率
```

### 阶段 9-10：骨骼绑定与动画

使用内置的四足动物骨骼模板（28个关节），根据宠物品种自动调整比例。通过距离加权法计算蒙皮权重，然后将估计的3D姿态序列重定向到骨骼动画。

### 阶段 11：资产导出

支持多种3D格式导出：

| 格式 | 用途 | 特点 |
|------|------|------|
| **GLB** | Web / 通用 | 二进制 GLTF，广泛支持 |
| **USDZ** | Apple AR | Quick Look 直接预览 |
| **FBX** | 游戏引擎 | Unity / Unreal 导入 |
| **OBJ** | 通用 | 最广泛兼容 |
| **PLY** | 点云 | 科研 / 可视化 |

---

## 项目结构

```
video2pet-app/
├── video2pet/                    # 核心包
│   ├── __init__.py
│   ├── config.py                 # 配置管理
│   ├── pipeline.py               # 主流水线编排
│   ├── cli.py                    # CLI 命令行接口
│   ├── video/
│   │   ├── processor.py          # 视频处理（帧提取、稳定化）
│   │   └── veo_client.py         # AI 视频生成（Veo/Sora）
│   ├── pose/
│   │   ├── detector.py           # 2D 姿态检测
│   │   └── estimator_3d.py       # 3D 姿态估计（SMAL）
│   ├── reconstruction/
│   │   ├── gaussian.py           # SfM + 3D Gaussian Splatting
│   │   └── mesh.py               # 网格提取与重建
│   ├── rigging/
│   │   └── skeleton.py           # 骨骼、蒙皮、动作重定向
│   └── export/
│       └── glb.py                # GLB/USDZ/FBX 导出
├── web/
│   └── app.py                    # Gradio Web UI
├── configs/
│   ├── default.yaml              # 默认配置
│   └── pets/
│       ├── dog.yaml              # 犬类品种配置
│       └── cat.yaml              # 猫类品种配置
├── scripts/
│   ├── install_mac.sh            # macOS 安装脚本
│   └── run_pipeline.py           # 独立运行脚本
├── tests/
│   ├── test_config.py
│   └── test_skeleton.py
├── models/                       # 模型权重（需下载）
│   └── smal/
├── pyproject.toml                # Python 项目配置
├── Makefile                      # 快捷命令
└── README.md                     # 本文档
```

---

## 配置说明

### 配置文件

默认配置位于 `configs/default.yaml`，可通过 `--config` 参数指定自定义配置：

```bash
video2pet run --video my_pet.mp4 --config configs/my_config.yaml
```

### 环境变量

API 密钥通过环境变量配置。将 `env_example.txt` 复制为 `.env` 并填入你的密钥：

```bash
cp env_example.txt .env
# 编辑 .env 填入 API keys
```

| 变量 | 用途 | 必需 |
|------|------|------|
| `GOOGLE_API_KEY` | Google Veo 视频生成 | 仅 AI 生成 |
| `OPENAI_API_KEY` | OpenAI Sora 视频生成 | 仅 AI 生成 |

---

## 性能参考

以下数据基于 Mac M2 Max 64GB 测试：

| 阶段 | 300帧视频 | 100帧（快速模式） |
|------|-----------|-------------------|
| 帧提取 | ~5s | ~2s |
| 2D 姿态检测 | ~30s | ~10s |
| 3D 姿态估计 | ~60s | ~20s |
| SfM | ~120s | ~40s |
| Gaussian Splatting | ~600s | ~100s |
| 网格提取 | ~30s | ~30s |
| 骨骼绑定 | ~10s | ~10s |
| 导出 | ~5s | ~5s |
| **总计** | **~15 min** | **~4 min** |

---

## 致谢

本项目基于以下开源工作：

- [video2robot](https://github.com/AIM-Intelligence/video2robot) — 端到端视频到机器人流水线
- [SMAL](https://smal.is.tue.mpg.de/) — 四足动物参数化3D模型
- [3D Gaussian Splatting](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/) — 实时辐射场渲染
- [ViTPose](https://github.com/ViTAE-Transformer/ViTPose) — 基于 Vision Transformer 的姿态估计
- [COLMAP](https://colmap.github.io/) — Structure from Motion

---

## License

MIT License

Copyright (c) 2024 Video2Pet Team
