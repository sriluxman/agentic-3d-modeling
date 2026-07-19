from pathlib import Path

from build123d import Color, Mesher, MeshType
import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "exports" / "india-austria-dovetail-cube"
JOBS = {
    "india-multicolor.3mf": [
        ("india-green", Color(0.075, 0.533, 0.031)),
        ("india-white", Color(1, 1, 1)),
        ("india-saffron", Color(1, 0.55, 0.10)),
    ],
    "austria-multicolor.3mf": [
        ("austria-red-bottom", Color(0.784, 0.063, 0.18)),
        ("austria-white", Color(1, 1, 1)),
        ("austria-red-top", Color(0.784, 0.063, 0.18)),
    ],
}


def load_job(volumes):
    loaded = []
    for name, color in volumes:
        source = EXPORT_DIR / "color-volumes" / f"{name}.stl"
        mesh = trimesh.load_mesh(source, force="mesh", process=True, validate=True)
        if not mesh.is_watertight or not mesh.is_volume:
            raise RuntimeError(f"Invalid color volume: {source}")
        loaded.append((name, color, source, mesh))

    bounds = np.array([mesh.bounds for _, _, _, mesh in loaded])
    minimum = bounds[:, 0, :].min(axis=0)
    maximum = bounds[:, 1, :].max(axis=0)
    offset = np.array([-(minimum[0] + maximum[0]) / 2, -(minimum[1] + maximum[1]) / 2, 0])
    for _, _, _, mesh in loaded:
        mesh.apply_translation(offset)
    return loaded


def write_job(file_name, volumes):
    mesher = Mesher()
    for name, color, source, mesh in load_job(volumes):
        mesh_3mf = mesher.model.AddMeshObject()
        vertices, triangles = Mesher._create_3mf_mesh(mesh.vertices.tolist(), mesh.faces.tolist())
        mesh_3mf.SetGeometry(vertices, triangles)
        mesh_3mf.SetType(Mesher._map_b3d_mesh_type_3mf[MeshType.MODEL])
        mesh_3mf.SetName(name)
        material_group = mesher.model.AddBaseMaterialGroup()
        material_id = material_group.AddMaterial(
            Name=name,
            DisplayColor=mesher.wrapper.FloatRGBAToColor(*tuple(color)),
        )
        mesh_3mf.SetObjectLevelProperty(material_group.GetResourceID(), material_id)
        if not mesh_3mf.IsValid() or not mesh_3mf.IsManifoldAndOriented():
            raise RuntimeError(f"Invalid 3MF color volume: {source}")
        mesher.meshes.append(mesh_3mf)
        mesher.model.AddBuildItem(mesh_3mf, mesher.wrapper.GetIdentityTransform())

    output = EXPORT_DIR / file_name
    mesher.write(output)
    print(output)


for output_name, job_volumes in JOBS.items():
    write_job(output_name, job_volumes)
