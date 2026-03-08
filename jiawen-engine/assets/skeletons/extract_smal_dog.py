"""
从 SMAL 模型提取狗骨骼 (canidae, index=1) 并导出为 GLB
用法: python extract_smal_dog.py
输出: smal_dog_skeleton.glb  smal_dog_joints.json
"""
import sys
import pickle
import numpy as np
import json
from pathlib import Path

# ─── chumpy stub：让 pickle 能读 SMAL pkl ──────────────────────
import types

class _Ch:
    """最小化 chumpy.Ch 替代，支持 pickle 反序列化。"""
    def __init__(self, *args, **kwargs):
        if args:
            self._arr = np.array(args[0])
        else:
            self._arr = np.array([])
    def __array__(self, dtype=None):
        return self._arr if dtype is None else self._arr.astype(dtype)
    def __getattr__(self, name):
        return getattr(self._arr, name)
    def __setstate__(self, state):
        self.__dict__.update(state)
        if hasattr(self, 'x') and self.x is not None:
            self._arr = np.array(self.x)
    def __reduce__(self):
        return (self.__class__, (self._arr,))

_chumpy = types.ModuleType("chumpy")
_chumpy.Ch = _Ch
_chumpy.array = lambda x, *a, **kw: _Ch(x)

import types as _types
_chumpy_reordered = types.ModuleType("chumpy.reordering")
_chumpy_reordered.ch_ops = lambda *a, **kw: _Ch()

sys.modules["chumpy"] = _chumpy
sys.modules["chumpy.ch"] = _chumpy
sys.modules["chumpy.reordering"] = _chumpy_reordered

# scipy.sparse 的 deprecated 路径兼容
try:
    import scipy.sparse.csc
    import scipy.sparse.csr
except Exception:
    pass
# ───────────────────────────────────────────────────────────────

HERE = Path(__file__).parent
SMAL_PKL  = HERE / "smal" / "smal_CVPR2017.pkl"
DATA_PKL  = HERE / "smal" / "smal_CVPR2017_data.pkl"
OUT_JSON  = HERE / "smal_dog_joints.json"
OUT_GLB   = HERE / "smal_dog_skeleton.glb"

print("加载 SMAL 模型...")
with open(SMAL_PKL, "rb") as f:
    model = pickle.load(f, encoding="latin1")

with open(DATA_PKL, "rb") as f:
    data = pickle.load(f, encoding="latin1")

# ─── 提取骨骼结构 ────────────────────────────────────────────
# kintree_table[0] = 父节点索引, kintree_table[1] = 子节点索引
kintree = model["kintree_table"]   # shape (2, n_joints)
# J_regressor: 从顶点回归关节位置 (n_joints, n_verts)
J_regressor = model["J_regressor"]  # sparse matrix
v_template  = model["v_template"]   # (n_verts, 3)
faces       = model["f"]            # (n_faces, 3)

print(f"顶点数: {v_template.shape[0]}, 面数: {faces.shape[0]}")
print(f"关节数: {kintree.shape[1]}")

# 用犬科 (canidae=1) 平均形态
dog_betas = data["cluster_means"][1]
n_betas = len(dog_betas)

# 计算形态混合 (shape blend shapes)
shapedirs = model["shapedirs"]  # (n_verts, 3, n_betas) or (n_verts*3, n_betas)
dog_v = v_template.copy()
try:
    sd = np.array(shapedirs)
    n_use = min(n_betas, sd.shape[-1])
    if sd.ndim == 3:
        # (n_verts, 3, n_betas)
        dog_v += sd[:, :, :n_use] @ dog_betas[:n_use]
    elif sd.ndim == 2:
        # (n_verts*3, n_betas)
        n_v = v_template.shape[0]
        sd2 = sd[:n_v * 3, :n_use].reshape(n_v, 3, n_use)
        dog_v += np.einsum("ijk,k->ij", sd2, dog_betas[:n_use])
    print(f"  形态混合完成 (使用 {n_use} 个形态系数)")
except Exception as e:
    print(f"  形态混合跳过: {e}，使用模板顶点")

# 关节位置 = J_regressor @ vertices
if hasattr(J_regressor, 'dot'):
    J = J_regressor.dot(dog_v)   # (n_joints, 3)
else:
    J = J_regressor @ dog_v

print(f"\n犬科 (canidae) 关节位置:")
print(f"  关节数: {J.shape[0]}")

# SMAL 关节名称 (35关节，参考 SMAL 论文)
SMAL_JOINT_NAMES = [
    "root",           # 0
    "pelvis",         # 1
    "spine1",         # 2
    "spine2",         # 3
    "spine3",         # 4
    "neck",           # 5
    "head",           # 6
    "l_eye",          # 7
    "r_eye",          # 8
    "mouth",          # 9
    "l_front_hip",    # 10
    "l_front_knee",   # 11
    "l_front_ankle",  # 12
    "l_front_toe",    # 13
    "r_front_hip",    # 14
    "r_front_knee",   # 15
    "r_front_ankle",  # 16
    "r_front_toe",    # 17
    "l_back_hip",     # 18
    "l_back_knee",    # 19
    "l_back_ankle",   # 20
    "l_back_toe",     # 21
    "r_back_hip",     # 22
    "r_back_knee",    # 23
    "r_back_ankle",   # 24
    "r_back_toe",     # 25
    "tail_base",      # 26
    "tail_mid",       # 27
    "tail_tip",       # 28
    "l_ear",          # 29
    "r_ear",          # 30
    "l_front_paw",    # 31 (some versions)
    "r_front_paw",    # 32
    "l_back_paw",     # 33
    "r_back_paw",     # 34
]
n_joints = J.shape[0]
joint_names = SMAL_JOINT_NAMES[:n_joints] + [f"joint_{i}" for i in range(len(SMAL_JOINT_NAMES), n_joints)]

# 构建关节数据
joints_data = []
for i in range(n_joints):
    parent = int(kintree[0, i]) if kintree[0, i] != 4294967295 else -1  # 0xFFFFFFFF = root
    joints_data.append({
        "name": joint_names[i],
        "parent": parent,
        "position": J[i].tolist(),
    })
    print(f"  [{i:2d}] {joint_names[i]:20s} pos={J[i].round(3).tolist()}  parent={parent}")

# ─── 导出 JSON ───────────────────────────────────────────────
skeleton_json = {
    "name": "smal_dog_canidae",
    "source": "SMAL CVPR2017",
    "n_joints": n_joints,
    "joints": joints_data,
    "n_verts": int(v_template.shape[0]),
    "n_faces": int(faces.shape[0]),
}
with open(OUT_JSON, "w") as f:
    json.dump(skeleton_json, f, indent=2)
print(f"\n骨骼 JSON 已保存: {OUT_JSON}")

# ─── 导出 GLB (网格 + 骨骼) ──────────────────────────────────
try:
    import pygltflib

    vertices = dog_v.astype(np.float32)
    faces_arr = faces.astype(np.uint32)

    # 蒙皮权重 (LBS weights: n_verts x n_joints)
    lbs_weights = np.array(model["weights"])  # (n_verts, n_joints)

    # Top-4 per vertex
    top4_idx = np.argsort(-lbs_weights, axis=1)[:, :4].astype(np.uint8)
    top4_w   = np.take_along_axis(lbs_weights, top4_idx.astype(int), axis=1).astype(np.float32)
    row_sums = top4_w.sum(axis=1, keepdims=True)
    top4_w  /= np.where(row_sums == 0, 1, row_sums)

    # 逆绑定矩阵
    ibm = []
    for j in joints_data:
        pos = np.array(j["position"], dtype=np.float32)
        m = np.eye(4, dtype=np.float32)
        m[3, :3] = -pos
        ibm.append(m)
    ibm_arr = np.array(ibm, dtype=np.float32)

    def align4(b): return b + b"\x00" * ((4 - len(b) % 4) % 4)

    chunks = [vertices.tobytes(), faces_arr.flatten().tobytes(),
              top4_idx.tobytes(), top4_w.tobytes(), ibm_arr.tobytes()]
    offsets, cur = [], 0
    for c in chunks:
        offsets.append(cur)
        cur += len(align4(c))
    blob = b"".join(align4(c) for c in chunks)

    g = pygltflib.GLTF2()
    g.asset = pygltflib.Asset(version="2.0", generator="佳文-SMAL")
    g.scene = 0
    g.buffers.append(pygltflib.Buffer(byteLength=len(blob)))

    def add_bv(off, length, target=None):
        g.bufferViews.append(pygltflib.BufferView(buffer=0, byteOffset=off, byteLength=length, target=target))
        return len(g.bufferViews) - 1

    def add_acc(bv, ct, count, typ, mn=None, mx=None):
        a = pygltflib.Accessor(bufferView=bv, componentType=ct, count=count, type=typ)
        if mn: a.min = [float(x) for x in mn]
        if mx: a.max = [float(x) for x in mx]
        g.accessors.append(a)
        return len(g.accessors) - 1

    bv_pos = add_bv(offsets[0], len(chunks[0]), pygltflib.ARRAY_BUFFER)
    bv_idx = add_bv(offsets[1], len(chunks[1]), pygltflib.ELEMENT_ARRAY_BUFFER)
    bv_jnt = add_bv(offsets[2], len(chunks[2]), pygltflib.ARRAY_BUFFER)
    bv_wgt = add_bv(offsets[3], len(chunks[3]), pygltflib.ARRAY_BUFFER)
    bv_ibm = add_bv(offsets[4], len(chunks[4]))

    n_v = len(vertices)
    acc_pos = add_acc(bv_pos, pygltflib.FLOAT, n_v, "VEC3",
                      vertices.min(0).tolist(), vertices.max(0).tolist())
    acc_idx = add_acc(bv_idx, pygltflib.UNSIGNED_INT, faces_arr.size, "SCALAR",
                      [int(faces_arr.min())], [int(faces_arr.max())])
    acc_jnt = add_acc(bv_jnt, pygltflib.UNSIGNED_BYTE, n_v, "VEC4")
    acc_wgt = add_acc(bv_wgt, pygltflib.FLOAT, n_v, "VEC4")
    acc_ibm = add_acc(bv_ibm, pygltflib.FLOAT, n_joints, "MAT4")

    prim = pygltflib.Primitive(
        attributes=pygltflib.Attributes(POSITION=acc_pos, JOINTS_0=acc_jnt, WEIGHTS_0=acc_wgt),
        indices=acc_idx, mode=pygltflib.TRIANGLES,
    )
    g.meshes.append(pygltflib.Mesh(name="SMALDog", primitives=[prim]))

    joint_node_start = 0
    for j in joints_data:
        pos = j["position"]
        g.nodes.append(pygltflib.Node(name=j["name"],
                                       translation=[float(p) for p in pos]))
    for idx, j in enumerate(joints_data):
        par = j.get("parent", -1)
        if par >= 0:
            node = g.nodes[par]
            node.children = (node.children or []) + [idx]

    g.skins.append(pygltflib.Skin(name="SMALSkin", inverseBindMatrices=acc_ibm,
                                    joints=list(range(n_joints)), skeleton=0))
    mesh_node = len(g.nodes)
    g.nodes.append(pygltflib.Node(name="DogBody", mesh=0, skin=0))
    g.scenes.append(pygltflib.Scene(nodes=[0, mesh_node]))
    g.set_binary_blob(blob)
    g.save(str(OUT_GLB))
    size_mb = OUT_GLB.stat().st_size / (1024 * 1024)
    print(f"GLB 已保存: {OUT_GLB} ({size_mb:.1f} MB)")
    print(f"  顶点: {n_v:,}  面: {faces_arr.shape[0]:,}  关节: {n_joints}")

except Exception as e:
    print(f"GLB 导出失败: {e}")

print("\nSMAL 狗骨骼提取完成！")
