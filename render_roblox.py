import bpy
import json
import math
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSET = ROOT / "roblox_dataset"
OUT = ROOT / "roblox_render"
OUT.mkdir(exist_ok=True)
TEXTURE_OUT = OUT / "textures"
TEXTURE_OUT.mkdir(exist_ok=True)

for path in OUT.iterdir():
    if path.is_file():
        path.unlink()
for path in TEXTURE_OUT.iterdir():
    if path.is_file():
        path.unlink()
for path in ASSET.glob("*.png"):
    shutil.copy2(path, OUT / path.name)

sanitized = OUT / "er_no_mtl.obj"
sanitized.write_text(
    "".join(line for line in ASSET.joinpath("er.obj").read_text(encoding="utf-8").splitlines(True)
            if not line.lstrip().lower().startswith("mtllib ")),
    encoding="utf-8",
)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 128
scene.cycles.preview_samples = 64
scene.cycles.use_denoising = True
scene.render.film_transparent = True
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.image_settings.color_depth = "8"
scene.render.filepath = str(OUT / "roblox_character_path_traced.png")
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1

bpy.ops.import_scene.obj(
    filepath=str(sanitized),
    use_image_search=False,
    use_split_objects=False,
    use_split_groups=True,
    axis_forward="-Z",
    axis_up="Y",
)

mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
baseplates = [obj for obj in mesh_objects if obj.name.lower().startswith("baseplate")]
baseplate_names = [obj.name for obj in baseplates]
for obj in baseplates:
    bpy.data.objects.remove(obj, do_unlink=True)
mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]

material_map = {
    "Spawnlocation1": ("Spawnlocation1Mtl", "Spawnlocation1_diff.png", "Spawnlocation1_nmap.png", None, None, False),
    "Spawnlocation2": ("Spawnlocation2Mtl", "Spawnlocation2_diff.png", None, None, None, False),
    "Cazyundee1": ("Cazyundee1Mtl", "Cazyundee1_diff.png", None, None, None, False),
    "Cazyundee2": ("Cazyundee1Mtl", "Cazyundee1_diff.png", None, None, None, False),
    "Cazyundee3": ("Cazyundee1Mtl", "Cazyundee1_diff.png", None, None, None, False),
    "Cazyundee4": ("Cazyundee1Mtl", "Cazyundee1_diff.png", None, None, None, False),
    "Cazyundee5": ("Cazyundee5Mtl", "Cazyundee5_diff.png", None, None, None, False),
    "Cazyundee6": ("Cazyundee1Mtl", "Cazyundee1_diff.png", None, None, None, False),
    "Cazyundee7": ("Cazyundee1Mtl", "Cazyundee1_diff.png", None, None, None, False),
    "Cazyundee8": ("Cazyundee1Mtl", "Cazyundee1_diff.png", None, None, None, False),
    "Cazyundee9": ("Cazyundee1Mtl", "Cazyundee1_diff.png", None, None, None, False),
    "Handle1": ("Handle1Mtl", "Handle1_diff.png", None, None, "Handle1_emap.png", True),
    "Handle2": ("Handle2Mtl", "Handle2_diff.png", "Handle2_nmap.png", "Handle2_spec.png", "Handle2_emap.png", True),
    "Handle3": ("Handle3Mtl", None, None, None, "Handle3_emap.png", True),
    "Handle4": ("Handle4Mtl", "Handle4_diff.png", "Handle4_nmap.png", "Handle4_spec.png", "Handle4_emap.png", True),
    "Handle5": ("Handle5Mtl", "Handle5_diff.png", "Handle5_nmap.png", "Handle5_spec.png", "Handle5_emap.png", True),
    "Handle6": ("Handle6Mtl", "Handle6_diff.png", None, None, None, False),
    "Handle7": ("Handle7Mtl", "Handle7_diff.png", None, None, None, False),
}

image_cache = {}

def load_image(filename, color_space="sRGB"):
    if not filename:
        return None
    if filename in image_cache:
        return image_cache[filename]
    image = bpy.data.images.load(str(ASSET / filename), check_existing=False)
    image.colorspace_settings.name = color_space
    image_cache[filename] = image
    return image

def make_material(name, diff, normal, spec, emission, alpha):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    material.blend_method = "HASHED" if alpha else "OPAQUE"
    material.show_transparent_back = False
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (360, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (100, 0)
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    if diff:
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = load_image(diff, "sRGB")
        texture.location = (-300, 100)
        links.new(texture.outputs["Color"], bsdf.inputs["Base Color"])
        links.new(texture.outputs["Alpha"], bsdf.inputs["Alpha"])
    if normal:
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = load_image(normal, "Linear")
        texture.location = (-300, -150)
        normal_map = nodes.new("ShaderNodeNormalMap")
        normal_map.location = (-80, -150)
        normal_map.inputs["Strength"].default_value = 0.7
        links.new(texture.outputs["Color"], normal_map.inputs["Color"])
        links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])
    if spec:
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = load_image(spec, "Linear")
        texture.location = (-300, -350)
        invert = nodes.new("ShaderNodeMath")
        invert.operation = "SUBTRACT"
        invert.inputs[0].default_value = 1.0
        invert.location = (-80, -350)
        links.new(texture.outputs["Color"], invert.inputs[1])
        links.new(invert.outputs[0], bsdf.inputs["Roughness"])
    if emission:
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = load_image(emission, "sRGB")
        texture.location = (-300, -550)
        links.new(texture.outputs["Color"], bsdf.inputs["Emission"])
        bsdf.inputs["Emission Strength"].default_value = 0.45
    return material

for obj in mesh_objects:
    key = obj.name.split(".")[0]
    spec = material_map.get(key)
    if spec:
        material = make_material(*spec)
        obj.data.materials.clear()
        obj.data.materials.append(material)

for obj in mesh_objects:
    obj.select_set(True)
bpy.ops.export_scene.obj(
    filepath=str(OUT / "er_no_baseplate.obj"),
    use_selection=True,
    use_materials=True,
    use_animation=False,
    check_existing=False,
    axis_forward="-Z",
    axis_up="Y",
)

verts = []
for obj in mesh_objects:
    for vertex in obj.data.vertices:
        verts.append(vertex.co @ obj.matrix_world)
mins = [min(vertex[i] for vertex in verts) for i in range(3)]
maxs = [max(vertex[i] for vertex in verts) for i in range(3)]
center = [(mins[i] + maxs[i]) / 2 for i in range(3)]
size = [maxs[i] - mins[i] for i in range(3)]
radius = math.sqrt(sum(value * value for value in size)) / 2
center_v = bpy.data.objects["Camera"].location if False else None

bpy.ops.object.empty_add(type="PLAIN_AXES", location=center)
target = bpy.context.object
target.name = "CharacterTarget"
camera_data = bpy.data.cameras.new("CharacterCamera")
camera = bpy.data.objects.new("CharacterCamera", camera_data)
bpy.context.scene.collection.objects.link(camera)
camera.location = (center[0] + 8.5, center[1] - 10.5, center[2] + 6.5)
camera.rotation_euler = ((bpy.data.objects["CharacterTarget"].location - camera.location).to_track_quat("-Z", "Y").to_euler())
scene.camera = camera
camera_data.lens = 55
camera_data.type = "PERSP"

world = bpy.data.worlds.new("CharacterWorld")
scene.world = world
world.use_nodes = True
world_nodes = world.node_tree.nodes
world_nodes.clear()
world_output = world_nodes.new("ShaderNodeOutputWorld")
background = world_nodes.new("ShaderNodeBackground")
background.inputs["Color"].default_value = (0.025, 0.028, 0.035, 1.0)
background.inputs["Strength"].default_value = 0.25
world.node_tree.links.new(background.outputs["Background"], world_output.inputs["Surface"])

def add_light(name, location, energy, color=(1.0, 0.96, 0.9)):
    data = bpy.data.lights.new(name, type="AREA")
    data.energy = energy
    data.color = color
    data.shape = "DISK"
    data.size = 5
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = ((target.location - obj.location).to_track_quat("-Z", "Y").to_euler())
    return obj

add_light("KeyLight", (center[0] + 7, center[1] - 8, center[2] + 8), 900)
add_light("FillLight", (center[0] - 8, center[1] - 3, center[2] + 3), 350, (0.75, 0.85, 1.0))
add_light("RimLight", (center[0], center[1] + 7, center[2] + 7), 500, (0.8, 0.9, 1.0))

bpy.context.view_layer.objects.active = mesh_objects[0] if mesh_objects else None
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "roblox_character_no_baseplate.blend"))

info = {
    "imported_objects": [obj.name for obj in mesh_objects],
    "removed_baseplates": baseplate_names,
    "remaining_mesh_count": len(mesh_objects),
    "bounds_min": mins,
    "bounds_max": maxs,
    "center": center,
    "output_png": str(OUT / "roblox_character_path_traced.png"),
    "output_obj": str(OUT / "er_no_baseplate.obj"),
    "output_blend": str(OUT / "roblox_character_no_baseplate.blend"),
}
(OUT / "render-info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
print(json.dumps(info, indent=2))
bpy.ops.render.render(write_still=True)
