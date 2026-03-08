"""
Mesh Reconstruction
====================
Extract and refine triangle meshes from 3D representations.
Supports extraction from Gaussian Splatting and direct mesh reconstruction.
"""

from pathlib import Path
from typing import Optional

import numpy as np
import torch
from rich.console import Console

console = Console()


class MeshExtractor:
    """Extract triangle mesh from various 3D representations."""

    def __init__(self, config):
        self.config = config.reconstruction
        self.device = config.device
        self.project_dir = Path(config.project_dir)

    def from_gaussians(self, gaussians_path: str, output_dir: Optional[str] = None) -> dict:
        """Extract mesh from trained Gaussian Splatting model.

        Uses Marching Cubes on the opacity field of Gaussians.
        """
        console.print("[cyan]Extracting mesh from Gaussians...[/cyan]")

        output_dir = Path(output_dir or self.project_dir / "mesh")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load Gaussians
        data = torch.load(gaussians_path, map_location="cpu")
        positions = data["positions"].numpy()
        colors = data["colors"].numpy()
        opacities = data.get("opacities", torch.ones(len(positions), 1)).numpy()

        # Create voxel grid
        resolution = self.config.mesh_resolution
        console.print(f"  Grid resolution: {resolution}^3")

        # Compute bounding box
        margin = 0.1
        bbox_min = positions.min(axis=0) - margin
        bbox_max = positions.max(axis=0) + margin

        # Create density grid from Gaussian positions
        grid = np.zeros((resolution, resolution, resolution), dtype=np.float32)

        # Voxelize Gaussians
        for i in range(len(positions)):
            # Map position to grid coordinates
            grid_pos = (positions[i] - bbox_min) / (bbox_max - bbox_min) * (resolution - 1)
            grid_pos = grid_pos.astype(int)

            if all(0 <= grid_pos[j] < resolution for j in range(3)):
                opacity = float(opacities[i].squeeze()) if opacities[i].size > 0 else 1.0
                grid[grid_pos[0], grid_pos[1], grid_pos[2]] += opacity

        # Smooth the grid
        from scipy.ndimage import gaussian_filter
        grid = gaussian_filter(grid, sigma=1.0)

        # Marching Cubes
        try:
            from skimage.measure import marching_cubes

            threshold = grid.max() * 0.1
            if threshold < 1e-6:
                threshold = 0.5

            vertices, faces, normals, values = marching_cubes(grid, level=threshold)

            # Scale vertices back to world coordinates
            vertices = vertices / (resolution - 1) * (bbox_max - bbox_min) + bbox_min

            # Assign vertex colors from nearest Gaussian
            vertex_colors = self._assign_vertex_colors(vertices, positions, colors)

            # Save mesh
            mesh_path = output_dir / "pet_mesh.obj"
            self._save_obj(mesh_path, vertices, faces, normals, vertex_colors)

            # Also save PLY with colors
            ply_path = output_dir / "pet_mesh.ply"
            self._save_ply(ply_path, vertices, faces, vertex_colors)

            console.print(f"[green]Mesh extracted: {len(vertices)} vertices, {len(faces)} faces[/green]")
            console.print(f"  OBJ: {mesh_path}")
            console.print(f"  PLY: {ply_path}")

            return {
                "obj_path": str(mesh_path),
                "ply_path": str(ply_path),
                "n_vertices": len(vertices),
                "n_faces": len(faces),
                "vertices": vertices,
                "faces": faces,
                "normals": normals,
                "colors": vertex_colors,
            }

        except ImportError:
            console.print("[red]scikit-image required for mesh extraction[/red]")
            return {"error": "scikit-image not installed"}

    def from_point_cloud(self, ply_path: str, output_dir: Optional[str] = None) -> dict:
        """Reconstruct mesh from point cloud using Poisson reconstruction."""
        console.print("[cyan]Reconstructing mesh from point cloud...[/cyan]")

        output_dir = Path(output_dir or self.project_dir / "mesh")
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            import open3d as o3d

            # Load point cloud
            pcd = o3d.io.read_point_cloud(ply_path)
            console.print(f"  Loaded {len(pcd.points)} points")

            # Estimate normals
            pcd.estimate_normals(
                search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
            )
            pcd.orient_normals_consistent_tangent_plane(k=15)

            # Poisson surface reconstruction
            console.print("  Running Poisson reconstruction...")
            mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
                pcd, depth=9, width=0, scale=1.1, linear_fit=False
            )

            # Remove low-density vertices
            densities = np.asarray(densities)
            density_threshold = np.quantile(densities, 0.1)
            vertices_to_remove = densities < density_threshold
            mesh.remove_vertices_by_mask(vertices_to_remove)

            # Clean mesh
            mesh.remove_degenerate_triangles()
            mesh.remove_duplicated_triangles()
            mesh.remove_duplicated_vertices()
            mesh.remove_non_manifold_edges()

            # Save
            mesh_path = output_dir / "pet_mesh_poisson.obj"
            o3d.io.write_triangle_mesh(str(mesh_path), mesh)

            console.print(
                f"[green]Mesh reconstructed: "
                f"{len(mesh.vertices)} vertices, {len(mesh.triangles)} faces[/green]"
            )

            return {
                "obj_path": str(mesh_path),
                "n_vertices": len(mesh.vertices),
                "n_faces": len(mesh.triangles),
            }

        except ImportError:
            console.print("[yellow]Open3D not available. Using trimesh fallback.[/yellow]")
            return self._trimesh_reconstruction(ply_path, output_dir)

    def _trimesh_reconstruction(self, ply_path: str, output_dir: Path) -> dict:
        """Fallback mesh reconstruction using trimesh."""
        import trimesh

        # Load point cloud
        cloud = trimesh.load(ply_path)

        if hasattr(cloud, "vertices"):
            # Create convex hull as a simple mesh
            hull = cloud.convex_hull

            mesh_path = output_dir / "pet_mesh_hull.obj"
            hull.export(str(mesh_path))

            console.print(f"[green]Convex hull mesh: {len(hull.vertices)} vertices[/green]")
            return {
                "obj_path": str(mesh_path),
                "n_vertices": len(hull.vertices),
                "n_faces": len(hull.faces),
            }

        return {"error": "Could not create mesh from point cloud"}

    @staticmethod
    def _assign_vertex_colors(vertices, positions, colors):
        """Assign colors to mesh vertices from nearest Gaussian."""
        from scipy.spatial import KDTree

        tree = KDTree(positions)
        _, indices = tree.query(vertices, k=1)
        vertex_colors = colors[indices]
        return np.clip(vertex_colors, 0, 1)

    @staticmethod
    def _save_obj(path, vertices, faces, normals=None, colors=None):
        """Save mesh as OBJ file."""
        with open(path, "w") as f:
            f.write("# Video2Pet Generated Mesh\n")
            for i, v in enumerate(vertices):
                if colors is not None:
                    f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f} {colors[i][0]:.4f} {colors[i][1]:.4f} {colors[i][2]:.4f}\n")
                else:
                    f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            if normals is not None:
                for n in normals:
                    f.write(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")
            for face in faces:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

    @staticmethod
    def _save_ply(path, vertices, faces, colors=None):
        """Save mesh as PLY file."""
        n_verts = len(vertices)
        n_faces = len(faces)

        with open(path, "w") as f:
            f.write("ply\n")
            f.write("format ascii 1.0\n")
            f.write(f"element vertex {n_verts}\n")
            f.write("property float x\nproperty float y\nproperty float z\n")
            if colors is not None:
                f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
            f.write(f"element face {n_faces}\n")
            f.write("property list uchar int vertex_indices\n")
            f.write("end_header\n")

            for i in range(n_verts):
                line = f"{vertices[i][0]:.6f} {vertices[i][1]:.6f} {vertices[i][2]:.6f}"
                if colors is not None:
                    r, g, b = (colors[i] * 255).astype(int)
                    line += f" {r} {g} {b}"
                f.write(line + "\n")

            for face in faces:
                f.write(f"3 {face[0]} {face[1]} {face[2]}\n")
