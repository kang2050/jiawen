"""
SMAL → 带骨骼 GLB 导出
========================
从每个动物 PKL (pose+betas) + SMAL 基础模型 (weights+kintree)
用 LBS 正向传播，导出有真实骨架的 GLB 文件。

用法:
  python export_smal_rigged.py
输出:
  outputs/smal_dogs/<name>_rigged.glb
"""

import sys, types, pickle, json
from pathlib import Path
import numpy as np

# ─── chumpy stub ────────────────────────────────────────────────
class _Ch:
    def __init__(self, *a, **kw):
        self._arr = np.array(a[0]) if a else np.array([])
    def __array__(self, dtype=None):
        return self._arr if dtype is None else self._arr.astype(dtype)
    def __getattr__(self, n):
        return getattr(self._arr, n)
    def __setstate__(self, s):
        self.__dict__.update(s)
        if hasattr(self, 'x') and self.x is not None:
            self._arr = np.array(self.x)

_ch = types.ModuleType('chumpy')
_ch.Ch = _Ch
_ch.array = lambda x, *a, **kw: _Ch(x)
sys.modules['chumpy'] = _ch
sys.modules['chumpy.ch'] = _ch
sys.modules['chumpy.reordering'] = types.ModuleType('chumpy.reordering')
# ────────────────────────────────────────────────────────────────

HERE       = Path(__file__).parent
SMAL_PKL   = HERE / "smal" / "smal_CVPR2017.pkl"
ANIMALS_DIR = HERE.parent.parent.parent / "动物模型仓库" / "extracted" / "dogs"
OUT_DIR    = HERE.parent.parent / "outputs" / "smal_dogs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── 加载 SMAL 基础模型 ──────────────────────────────────────────
print("加载 SMAL 基础模型...")
with open(SMAL_PKL, "rb") as f:
    smal = pickle.load(f, encoding="latin1")

v_template  = np.array(smal["v_template"])      # (3889, 3)
faces       = np.array(smal["f"], dtype=np.int32)  # (7774, 3)
shapedirs   = np.array(smal["shapedirs"])        # (3889, 3, n_betas)
J_regressor = smal["J_regressor"]               # sparse (35, 3889)
kintree     = smal["kintree_table"]              # (2, 35)
weights     = np.array(smal["weights"])          # (3889, 35) LBS weights
n_joints    = kintree.shape[1]
_raw_p      = np.array(kintree[0], dtype=np.int64)
_raw_p[_raw_p > 10000] = -1                      # uint32 overflow of -1 (root)
parents     = _raw_p                              # parent[i] = parent joint of i

print(f"  顶点: {v_template.shape[0]}, 面: {faces.shape[0]}, 关节: {n_joints}")
print(f"  LBS weights shape: {weights.shape}")

# 关节名（SMAL 35 关节）
JOINT_NAMES = [
    "root", "pelvis", "spine1", "spine2", "spine3",
    "neck", "head", "l_eye", "r_eye", "mouth",
    "l_front_hip", "l_front_knee", "l_front_ankle", "l_front_toe",
    "r_front_hip", "r_front_knee", "r_front_ankle", "r_front_toe",
    "l_back_hip",  "l_back_knee",  "l_back_ankle",  "l_back_toe",
    "r_back_hip",  "r_back_knee",  "r_back_ankle",  "r_back_toe",
    "tail1", "tail2", "tail3", "tail4", "tail5", "tail6", "tail7",
    "nose", "chin",
]
while len(JOINT_NAMES) < n_joints:
    JOINT_NAMES.append(f"joint_{len(JOINT_NAMES)}")


def rodrigues(r):
    """axis-angle (3,) → 旋转矩阵 (3,3)"""
    theta = np.linalg.norm(r)
    if theta < 1e-8:
        return np.eye(3)
    k = r / theta
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(theta) * K + (1 - np.cos(theta)) * (K @ K)


def lbs_forward(v_tpl, shapedirs, J_reg, kintree, weights, betas, poses):
    """
    SMAL LBS 正向传播
    betas: (n_betas,)  shape 参数
    poses: (n_joints*3,) or (n_joints, 3)  axis-angle 姿态
    Returns: (n_verts, 3) posed vertices, (n_joints, 3) joint world positions
    """
    n_v = v_tpl.shape[0]
    n_j = kintree.shape[1]
    raw_parents = np.array(kintree[0], dtype=np.int64)
    raw_parents[raw_parents > 10000] = -1  # uint32 overflow of -1 (root node)
    parents_local = raw_parents

    # 1. 形态混合
    sd = np.array(shapedirs)
    n_use = min(len(betas), sd.shape[-1] if sd.ndim == 3 else sd.shape[1])
    v_shaped = v_tpl.copy()
    if sd.ndim == 3:
        v_shaped += sd[:, :, :n_use] @ betas[:n_use]
    else:
        sd2 = sd[:n_v*3, :n_use].reshape(n_v, 3, n_use)
        v_shaped += np.einsum("ijk,k->ij", sd2, betas[:n_use])

    # 2. 关节位置（静止姿态）
    if hasattr(J_reg, 'dot'):
        J = J_reg.dot(v_shaped)
    else:
        J = J_reg @ v_shaped    # (n_j, 3)

    # 3. 全局变换（forward kinematics）
    poses = np.array(poses).reshape(n_j, 3)
    G = np.zeros((n_j, 4, 4))  # global transforms

    def make_T(R, t):
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = t
        return T

    for i in range(n_j):
        R_i = rodrigues(poses[i])
        local_T = make_T(R_i, J[i])
        if parents_local[i] < 0 or parents_local[i] == i:
            G[i] = local_T
        else:
            p = parents_local[i]
            # local joint position relative to parent
            local_T[:3, 3] = J[i] - J[p]
            G[i] = G[p] @ local_T

    # 4. Inverse bind matrices (remove rest pose joint offset)
    # G_rest * IBM = I  =>  IBM = inv(G_rest)
    G_rest = np.zeros_like(G)
    for i in range(n_j):
        local_rest = make_T(np.eye(3), J[i] if parents_local[i] < 0 or parents_local[i] == i else J[i] - J[parents_local[i]])
        if parents_local[i] < 0 or parents_local[i] == i:
            G_rest[i] = local_rest
        else:
            G_rest[i] = G_rest[parents_local[i]] @ local_rest

    # Corrected pose transform: G @ inv(G_rest)
    G_final = np.zeros_like(G)
    for i in range(n_j):
        G_final[i] = G[i] @ np.linalg.inv(G_rest[i])

    # 5. LBS
    v_h = np.ones((n_v, 4))
    v_h[:, :3] = v_shaped
    v_posed = np.zeros((n_v, 3))
    for i in range(n_j):
        v_posed += weights[:, i:i+1] * (v_h @ G_final[i].T)[:, :3]

    # 6. 关节世界坐标（用于 GLB export）
    J_world = G[:, :3, 3]

    return v_posed.astype(np.float32), J_world.astype(np.float32), G_final, G_rest, J


def export_rigged_glb(v_posed, faces, weights, J_world, parents, joint_names, G_rest, out_path):
    """导出带骨骼蒙皮的 GLB（pygltflib）"""
    try:
        import pygltflib as g
    except ImportError:
        print("  安装 pygltflib...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "pygltflib", "-q"])
        import pygltflib as g

    import struct, base64

    n_v = v_posed.shape[0]
    n_f = faces.shape[0]
    n_j = len(parents)

    # 归一化 weights 到前4个影响关节（GLB JOINTS_0 只支持4个）
    # 对每个顶点取权重最大的4个关节
    top4_idx  = np.argsort(-weights, axis=1)[:, :4].astype(np.uint8)
    top4_w    = np.take_along_axis(weights, top4_idx.astype(int), axis=1).astype(np.float32)
    row_sum   = top4_w.sum(axis=1, keepdims=True)
    row_sum   = np.where(row_sum == 0, 1.0, row_sum)
    top4_w   /= row_sum  # renormalize

    # ─── binary blob ────────────────────────────────────────────
    bufs = []
    def append_buf(arr):
        b = arr.tobytes()
        bufs.append(b)
        return len(b)

    # 0: positions
    pos = v_posed.astype(np.float32)
    pos_len = append_buf(pos)
    # 1: indices
    idx = faces.astype(np.uint32)
    idx_len = append_buf(idx)
    # 2: joints
    j0 = top4_idx.astype(np.uint8)
    j0_len = append_buf(j0)
    # 3: weights
    w0 = top4_w.astype(np.float32)
    w0_len = append_buf(w0)
    # 4: inverse bind matrices (n_j * 16 floats)
    ibm_list = []
    for i in range(n_j):
        ibm = np.linalg.inv(G_rest[i]).astype(np.float32)
        ibm_list.append(ibm.flatten(order='F'))  # column-major for GLTF
    ibm_arr = np.array(ibm_list, dtype=np.float32)
    ibm_len = append_buf(ibm_arr)

    blob = b"".join(bufs)
    offsets = [0]
    for b in bufs[:-1]:
        offsets.append(offsets[-1] + len(b))

    gltf = g.GLTF2()
    gltf.asset = g.Asset(version="2.0", generator="SMAL-Rigged-Exporter")

    # Buffer
    gltf.buffers.append(g.Buffer(byteLength=len(blob)))

    # BufferViews
    bv_pos  = g.BufferView(buffer=0, byteOffset=offsets[0], byteLength=pos_len, target=g.ARRAY_BUFFER)
    bv_idx  = g.BufferView(buffer=0, byteOffset=offsets[1], byteLength=idx_len, target=g.ELEMENT_ARRAY_BUFFER)
    bv_j0   = g.BufferView(buffer=0, byteOffset=offsets[2], byteLength=j0_len,  target=g.ARRAY_BUFFER)
    bv_w0   = g.BufferView(buffer=0, byteOffset=offsets[3], byteLength=w0_len,  target=g.ARRAY_BUFFER)
    bv_ibm  = g.BufferView(buffer=0, byteOffset=offsets[4], byteLength=ibm_len)
    gltf.bufferViews.extend([bv_pos, bv_idx, bv_j0, bv_w0, bv_ibm])

    # Accessors
    pmin = pos.min(axis=0).tolist()
    pmax = pos.max(axis=0).tolist()
    acc_pos = g.Accessor(bufferView=0, componentType=g.FLOAT, count=n_v, type=g.VEC3, min=pmin, max=pmax)
    acc_idx = g.Accessor(bufferView=1, componentType=g.UNSIGNED_INT, count=n_f*3, type=g.SCALAR)
    acc_j0  = g.Accessor(bufferView=2, componentType=g.UNSIGNED_BYTE, count=n_v, type=g.VEC4)
    acc_w0  = g.Accessor(bufferView=3, componentType=g.FLOAT, count=n_v, type=g.VEC4)
    acc_ibm = g.Accessor(bufferView=4, componentType=g.FLOAT, count=n_j, type=g.MAT4)
    gltf.accessors.extend([acc_pos, acc_idx, acc_j0, acc_w0, acc_ibm])

    # Material
    mat = g.Material(
        name="dog_body",
        pbrMetallicRoughness=g.PbrMetallicRoughness(
            baseColorFactor=[0.76, 0.68, 0.60, 1.0],
            metallicFactor=0.0,
            roughnessFactor=0.8,
        ),
        doubleSided=True,
    )
    gltf.materials.append(mat)

    # Mesh
    prim = g.Primitive(
        attributes=g.Attributes(POSITION=0, JOINTS_0=2, WEIGHTS_0=3),
        indices=1,
        material=0,
    )
    mesh = g.Mesh(name="dog_mesh", primitives=[prim])
    gltf.meshes.append(mesh)

    # Nodes: skeleton joints + mesh node
    joint_node_indices = list(range(n_j))
    mesh_node_idx = n_j

    for i in range(n_j):
        # local translation relative to parent
        if parents[i] < 0 or parents[i] == i:
            t = J_world[i].tolist()
        else:
            t = (J_world[i] - J_world[parents[i]]).tolist()
        children = [j for j in range(n_j) if parents[j] == i and j != i]
        node = g.Node(name=joint_names[i], translation=t, children=children if children else None)
        gltf.nodes.append(node)

    # Mesh node (uses skin)
    mesh_node = g.Node(name="dog_body", mesh=0, skin=0)
    gltf.nodes.append(mesh_node)

    # Root joints (no parent or parent is self)
    root_joints = [i for i in range(n_j) if parents[i] < 0 or parents[i] == i]
    scene_children = root_joints + [mesh_node_idx]

    # Skin
    skin = g.Skin(name="smal_skin", inverseBindMatrices=4, joints=joint_node_indices)
    gltf.skins.append(skin)

    # Scene
    scene_node = g.Node(name="scene_root", children=scene_children)
    gltf.nodes.append(scene_node)
    gltf.scenes.append(g.Scene(nodes=[len(gltf.nodes) - 1]))
    gltf.scene = 0

    gltf.set_binary_blob(blob)
    gltf.save(str(out_path))
    kb = out_path.stat().st_size // 1024
    print(f"  → {out_path.name}  {kb}KB  ({n_v} verts, {n_j} joints)")


# ─── 处理每个动物 ────────────────────────────────────────────────
print("\n开始处理动物 PKL 文件...")

pkl_files = sorted(ANIMALS_DIR.glob("*.pkl"))
ok_count = 0

for pkl_path in pkl_files:
    name = pkl_path.stem
    out_path = OUT_DIR / f"{name}_rigged.glb"
    try:
        with open(pkl_path, "rb") as f:
            animal = pickle.load(f, encoding="latin1")

        # 取 betas 和 poses
        betas = np.array(animal.get("betas", animal.get("beta", np.zeros(41)))).flatten()
        poses = np.array(animal.get("pose",  animal.get("poses", np.zeros(n_joints * 3)))).flatten()
        trans = np.array(animal.get("trans", np.zeros(3))).flatten()

        print(f"\n{name}")
        print(f"  betas: {betas.shape}  poses: {poses.shape}")

        # LBS 正向传播
        v_posed, J_world, G_final, G_rest, J_rest = lbs_forward(
            v_template, shapedirs, J_regressor, kintree, weights, betas, poses
        )

        # 应用 trans
        v_posed += trans[:3]
        J_world += trans[:3]

        export_rigged_glb(v_posed, faces, weights, J_world, parents, JOINT_NAMES, G_rest, out_path)
        ok_count += 1

    except Exception as e:
        import traceback
        print(f"  跳过 {name}: {e}")
        traceback.print_exc()

print(f"\n完成！共导出 {ok_count}/{len(pkl_files)} 个带骨骼 GLB")
