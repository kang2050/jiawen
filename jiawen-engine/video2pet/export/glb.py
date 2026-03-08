"""
GLB/GLTF Export
================
Export pet 3D assets to GLB/GLTF format with mesh, skeleton, and animation.
Uses pygltflib for full skeleton/skin support; falls back to trimesh for mesh-only export.
"""

import json
import struct
from pathlib import Path
from typing import Optional

import numpy as np
from rich.console import Console

console = Console()


class GLBExporter:
    """Export pet digital twin as GLB file with skeleton support."""

    def __init__(self, config):
        self.config = config.export
        self.project_dir = Path(config.project_dir)

    def export(
        self,
        mesh_data: dict,
        skeleton: Optional[dict] = None,
        animation: Optional[list] = None,
        skinning_weights: Optional[np.ndarray] = None,
        texture_path: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> str:
        if output_path is None:
            output_dir = self.project_dir / "export"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / "pet_digital_twin.glb")

        console.print("[cyan]Exporting to GLB format...[/cyan]")

        # Use pygltflib when skeleton is available (real bone export)
        if skeleton is not None and skinning_weights is not None:
            try:
                return self._export_with_pygltflib(
                    mesh_data, skeleton, skinning_weights, texture_path, output_path
                )
            except Exception as e:
                console.print(f"[yellow]pygltflib export failed ({e}), falling back to trimesh[/yellow]")

        # Fallback: mesh-only export via trimesh
        try:
            return self._export_with_trimesh(mesh_data, texture_path, output_path)
        except ImportError:
            return self._export_manual(mesh_data, output_path)

    # ─── pygltflib: full skeleton + skin export ───────────────────────

    def _export_with_pygltflib(
        self,
        mesh_data: dict,
        skeleton: dict,
        skinning_weights: np.ndarray,
        texture_path: Optional[str],
        output_path: str,
    ) -> str:
        import pygltflib

        vertices = np.array(mesh_data["vertices"], dtype=np.float32)
        faces = np.array(mesh_data["faces"], dtype=np.uint32)
        joints_data = skeleton.get("joints", [])
        n_joints = len(joints_data)
        n_verts = len(vertices)

        # ── binary buffers ──────────────────────────────────────────────

        # POSITION
        pos_bytes = vertices.tobytes()

        # NORMAL
        if "normals" in mesh_data and mesh_data["normals"] is not None:
            normals = np.array(mesh_data["normals"], dtype=np.float32)
        else:
            normals = np.zeros_like(vertices)
        norm_bytes = normals.tobytes()

        # COLOR_0  (RGBA uint8)
        if "colors" in mesh_data and mesh_data["colors"] is not None:
            colors_f = np.array(mesh_data["colors"], dtype=np.float32)
            if colors_f.shape[1] == 3:
                colors_f = np.hstack([colors_f, np.ones((n_verts, 1), dtype=np.float32)])
            colors_u8 = (np.clip(colors_f, 0, 1) * 255).astype(np.uint8)
        else:
            colors_u8 = np.full((n_verts, 4), 200, dtype=np.uint8)
        color_bytes = colors_u8.tobytes()

        # JOINTS_0 and WEIGHTS_0 (top-4 influencing joints per vertex)
        weights = np.array(skinning_weights, dtype=np.float32)  # (n_verts, n_joints)
        # Clamp to actual joint count
        if weights.shape[1] > n_joints:
            weights = weights[:, :n_joints]

        # Pick top 4 joints per vertex
        top4_idx = np.argsort(-weights, axis=1)[:, :4]
        top4_w = np.take_along_axis(weights, top4_idx, axis=1)
        # Normalize weights
        row_sums = top4_w.sum(axis=1, keepdims=True)
        row_sums = np.where(row_sums == 0, 1, row_sums)
        top4_w = (top4_w / row_sums).astype(np.float32)
        top4_idx = top4_idx.astype(np.uint8)

        joints_bytes = top4_idx.tobytes()
        weights_bytes = top4_w.tobytes()

        # INDICES
        indices_bytes = faces.flatten().tobytes()

        # Inverse bind matrices (4x4 float32 per joint)
        ibm_list = []
        for j in joints_data:
            pos = np.array(j["position"], dtype=np.float32)
            ibm = np.eye(4, dtype=np.float32)
            ibm[3, :3] = -pos  # inverse translation (column-major: row 3 = translation)
            ibm_list.append(ibm)
        ibm_array = np.array(ibm_list, dtype=np.float32)  # (n_joints, 4, 4)
        ibm_bytes = ibm_array.tobytes()

        # ── pack binary blob ────────────────────────────────────────────

        def align4(b: bytes) -> bytes:
            pad = (4 - len(b) % 4) % 4
            return b + b"\x00" * pad

        chunks = [pos_bytes, norm_bytes, color_bytes, joints_bytes, weights_bytes,
                  indices_bytes, ibm_bytes]
        offsets = []
        cur = 0
        for c in chunks:
            offsets.append(cur)
            cur += len(align4(c))

        binary_blob = b"".join(align4(c) for c in chunks)

        # ── build GLTF structure ────────────────────────────────────────

        g = pygltflib.GLTF2()
        g.asset = pygltflib.Asset(version="2.0", generator="佳文AI-Engine")
        g.scene = 0

        buf = pygltflib.Buffer(byteLength=len(binary_blob))
        g.buffers.append(buf)

        def add_bv(byte_offset, byte_length, target=None):
            bv = pygltflib.BufferView(buffer=0, byteOffset=byte_offset,
                                      byteLength=byte_length, target=target)
            g.bufferViews.append(bv)
            return len(g.bufferViews) - 1

        def add_acc(bv_idx, component_type, count, type_str, min_v=None, max_v=None):
            acc = pygltflib.Accessor(
                bufferView=bv_idx,
                componentType=component_type,
                count=count,
                type=type_str,
            )
            if min_v is not None:
                acc.min = [float(x) for x in min_v]
            if max_v is not None:
                acc.max = [float(x) for x in max_v]
            g.accessors.append(acc)
            return len(g.accessors) - 1

        # Buffer views
        bv_pos   = add_bv(offsets[0], len(pos_bytes),     pygltflib.ARRAY_BUFFER)
        bv_norm  = add_bv(offsets[1], len(norm_bytes),    pygltflib.ARRAY_BUFFER)
        bv_col   = add_bv(offsets[2], len(color_bytes),   pygltflib.ARRAY_BUFFER)
        bv_jnt   = add_bv(offsets[3], len(joints_bytes),  pygltflib.ARRAY_BUFFER)
        bv_wgt   = add_bv(offsets[4], len(weights_bytes), pygltflib.ARRAY_BUFFER)
        bv_idx   = add_bv(offsets[5], len(indices_bytes), pygltflib.ELEMENT_ARRAY_BUFFER)
        bv_ibm   = add_bv(offsets[6], len(ibm_bytes))

        # Accessors
        acc_pos  = add_acc(bv_pos,  pygltflib.FLOAT,         n_verts,        "VEC3",
                           vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist())
        acc_norm = add_acc(bv_norm, pygltflib.FLOAT,         n_verts,        "VEC3")
        acc_col  = add_acc(bv_col,  pygltflib.UNSIGNED_BYTE, n_verts,        "VEC4")
        acc_jnt  = add_acc(bv_jnt,  pygltflib.UNSIGNED_BYTE, n_verts,        "VEC4")
        acc_wgt  = add_acc(bv_wgt,  pygltflib.FLOAT,         n_verts,        "VEC4")
        acc_idx  = add_acc(bv_idx,  pygltflib.UNSIGNED_INT,  faces.size,     "SCALAR",
                           [int(faces.min())], [int(faces.max())])
        acc_ibm  = add_acc(bv_ibm,  pygltflib.FLOAT,         n_joints,       "MAT4")

        # Mesh primitive
        prim = pygltflib.Primitive(
            attributes=pygltflib.Attributes(
                POSITION=acc_pos,
                NORMAL=acc_norm,
                COLOR_0=acc_col,
                JOINTS_0=acc_jnt,
                WEIGHTS_0=acc_wgt,
            ),
            indices=acc_idx,
            mode=pygltflib.TRIANGLES,
        )
        mesh = pygltflib.Mesh(name="PetMesh", primitives=[prim])
        g.meshes.append(mesh)

        # Joint nodes
        joint_node_start = len(g.nodes)
        for j in joints_data:
            pos = j["position"]
            node = pygltflib.Node(
                name=j["name"],
                translation=[float(pos[0]), float(pos[1]), float(pos[2])],
            )
            g.nodes.append(node)

        # Wire up parent-child for joints
        for idx, j in enumerate(joints_data):
            parent_idx = j.get("parent", -1)
            if parent_idx >= 0:
                g.nodes[joint_node_start + parent_idx].children = (
                    g.nodes[joint_node_start + parent_idx].children or []
                ) + [joint_node_start + idx]

        # Skin
        skin = pygltflib.Skin(
            name="PetSkin",
            inverseBindMatrices=acc_ibm,
            joints=list(range(joint_node_start, joint_node_start + n_joints)),
            skeleton=joint_node_start,  # root joint
        )
        g.skins.append(skin)

        # Skinned mesh node
        mesh_node_idx = len(g.nodes)
        mesh_node = pygltflib.Node(name="PetBody", mesh=0, skin=0)
        g.nodes.append(mesh_node)

        # Scene: root joint + skinned mesh
        scene = pygltflib.Scene(nodes=[joint_node_start, mesh_node_idx])
        g.scenes.append(scene)

        # Attach binary blob
        import base64
        g.set_binary_blob(binary_blob)

        # Write GLB
        g.save(output_path)

        size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        console.print(f"[green]GLB (with skeleton) exported: {output_path} ({size_mb:.1f} MB)[/green]")
        console.print(f"  Vertices: {n_verts}, Faces: {len(faces)}, Joints: {n_joints}")
        return output_path

    # ─── trimesh: mesh-only fallback ──────────────────────────────────

    def _export_with_trimesh(
        self,
        mesh_data: dict,
        texture_path: Optional[str],
        output_path: str,
    ) -> str:
        import trimesh

        vertices = np.array(mesh_data["vertices"], dtype=np.float32)
        faces = np.array(mesh_data["faces"], dtype=np.int32)
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

        if "colors" in mesh_data and mesh_data["colors"] is not None:
            colors = np.array(mesh_data["colors"])
            if colors.shape[1] == 3:
                alpha = np.ones((len(colors), 1))
                colors = np.hstack([colors, alpha])
            mesh.visual.vertex_colors = (np.clip(colors, 0, 1) * 255).astype(np.uint8)

        if "normals" in mesh_data and mesh_data["normals"] is not None:
            mesh.vertex_normals = np.array(mesh_data["normals"])

        if texture_path and Path(texture_path).exists():
            from PIL import Image
            uv = self._compute_uv_coordinates(vertices)
            mesh.visual = trimesh.visual.TextureVisuals(uv=uv, image=Image.open(texture_path))

        mesh.export(output_path, file_type="glb")
        size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        console.print(f"[green]GLB exported: {output_path} ({size_mb:.1f} MB)[/green]")
        console.print(f"  Vertices: {len(vertices)}, Faces: {len(faces)}")
        return output_path

    # ─── manual: no-dependency fallback ───────────────────────────────

    def _export_manual(self, mesh_data: dict, output_path: str) -> str:
        vertices = np.array(mesh_data["vertices"], dtype=np.float32)
        faces = np.array(mesh_data["faces"], dtype=np.uint32)

        gltf = {
            "asset": {"version": "2.0", "generator": "佳文AI-Engine"},
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0, "name": "PetMesh"}],
            "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1, "mode": 4}]}],
            "accessors": [
                {"bufferView": 0, "componentType": 5126, "count": len(vertices), "type": "VEC3",
                 "max": vertices.max(axis=0).tolist(), "min": vertices.min(axis=0).tolist()},
                {"bufferView": 1, "componentType": 5125, "count": faces.size, "type": "SCALAR",
                 "max": [int(faces.max())], "min": [int(faces.min())]},
            ],
            "bufferViews": [
                {"buffer": 0, "byteOffset": 0, "byteLength": vertices.nbytes, "target": 34962},
                {"buffer": 0, "byteOffset": vertices.nbytes, "byteLength": faces.nbytes, "target": 34963},
            ],
            "buffers": [{"byteLength": vertices.nbytes + faces.nbytes}],
        }

        binary_data = vertices.tobytes() + faces.tobytes()
        json_str = json.dumps(gltf, separators=(",", ":"))
        while len(json_str) % 4 != 0:
            json_str += " "
        json_bytes = json_str.encode("utf-8")
        while len(binary_data) % 4 != 0:
            binary_data += b"\x00"

        glb_header = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(json_bytes) + 8 + len(binary_data))
        with open(output_path, "wb") as f:
            f.write(glb_header)
            f.write(struct.pack("<II", len(json_bytes), 0x4E4F534A))
            f.write(json_bytes)
            f.write(struct.pack("<II", len(binary_data), 0x004E4942))
            f.write(binary_data)

        size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        console.print(f"[green]GLB exported: {output_path} ({size_mb:.2f} MB)[/green]")
        return output_path

    @staticmethod
    def _compute_uv_coordinates(vertices: np.ndarray) -> np.ndarray:
        center = vertices.mean(axis=0)
        centered = vertices - center
        theta = np.arctan2(centered[:, 0], centered[:, 2])
        u = (theta + np.pi) / (2 * np.pi)
        height_range = centered[:, 1].max() - centered[:, 1].min()
        v = (centered[:, 1] - centered[:, 1].min()) / height_range if height_range > 0 else np.zeros(len(vertices))
        return np.column_stack([u, v]).astype(np.float32)


class USDZExporter:
    def __init__(self, config):
        self.config = config.export
        self.project_dir = Path(config.project_dir)

    def export(self, mesh_data: dict, output_path: Optional[str] = None) -> str:
        if output_path is None:
            output_dir = self.project_dir / "export"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / "pet_digital_twin.usdz")

        console.print("[cyan]Exporting to USDZ format...[/cyan]")
        try:
            import trimesh
            vertices = np.array(mesh_data["vertices"], dtype=np.float32)
            faces = np.array(mesh_data["faces"], dtype=np.int32)
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            if "colors" in mesh_data and mesh_data["colors"] is not None:
                colors = np.array(mesh_data["colors"])
                if colors.shape[1] == 3:
                    colors = np.hstack([colors, np.ones((len(colors), 1))])
                mesh.visual.vertex_colors = (np.clip(colors, 0, 1) * 255).astype(np.uint8)
            gltf_path = output_path.replace(".usdz", ".glb")
            mesh.export(gltf_path, file_type="glb")
            console.print(f"[green]GLB exported (USDZ requires Apple usdzconvert): {gltf_path}[/green]")
            return gltf_path
        except ImportError:
            console.print("[red]trimesh required for USDZ export[/red]")
            return ""


class FBXExporter:
    def __init__(self, config):
        self.config = config.export
        self.project_dir = Path(config.project_dir)

    def export(self, mesh_data: dict, output_path: Optional[str] = None) -> str:
        if output_path is None:
            output_dir = self.project_dir / "export"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / "pet_digital_twin.fbx")

        console.print("[cyan]Exporting to FBX format...[/cyan]")
        obj_path = output_path.replace(".fbx", ".obj")
        vertices = np.array(mesh_data["vertices"])
        faces = np.array(mesh_data["faces"])

        with open(obj_path, "w") as f:
            f.write("# 佳文AI-Engine Generated Mesh\n")
            for v in vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            if "normals" in mesh_data and mesh_data["normals"] is not None:
                for n in mesh_data["normals"]:
                    f.write(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")
            for face in faces:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

        console.print(f"[green]OBJ exported: {obj_path}[/green]")
        console.print("[yellow]Note: For FBX, import OBJ into Blender and export as FBX[/yellow]")
        return obj_path
