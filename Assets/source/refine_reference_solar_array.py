"""Resolve coplanar connecting decks and refine the photovoltaic finish."""
import bpy,json
from pathlib import Path
from mathutils import Vector

assets=Path(__file__).resolve().parents[1]
scene=bpy.data.scenes['Solar / Reference Twin Array'];bpy.context.window.scene=scene
deck=scene.objects['Center ivory linking deck']
for v in deck.data.vertices:
    if v.co.z>.59:v.co.z+=.025
deck.data.update()
for material in bpy.data.materials:
    if material.name.startswith('Solar Module / Photovoltaic navy variation'):
        p=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        p.inputs['Metallic'].default_value=.12;p.inputs['Roughness'].default_value=.38
        p.inputs['Specular IOR Level'].default_value=.23;p.inputs['Coat Weight'].default_value=.035
orange=bpy.data.materials['Solar Module / Amber orange safety enamel']
p=next(n for n in orange.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
p.inputs['Base Color'].default_value=(.93,.18,.004,1);p.inputs['Metallic'].default_value=.10
p.inputs['Coat Weight'].default_value=.05;p.inputs['Roughness'].default_value=.40
orange.diffuse_color=(.93,.18,.004,1)
root=scene.objects['SolarArray | reference twin-bank module'];objects=set()
def visit(o):
    objects.add(o)
    for c in o.children:visit(c)
visit(root);bpy.ops.object.select_all(action='DESELECT')
for obj in objects:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(assets/'buildings/solar-array-reference-module.glb'),export_format='GLB',
    use_selection=True,use_active_scene=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False,export_extras=True)
report=assets/'previews/solar-array-reference-module-report.json';stats=json.loads(report.read_text())
stats['stage']='Rendering refined solar array'
stats['refinements']=['Raised center deck to resolve coplanar overlap','Darker navy photovoltaic finish','More saturated orange guards']
report.write_text(json.dumps(stats,indent=2))
scene.render.filepath=str(assets/'previews/solar-array-reference-module.png');bpy.ops.render.render(write_still=True)
camera=scene.camera;loc=camera.location.copy();rot=camera.rotation_euler.copy()
camera.location=(9,15,10);camera.rotation_euler=(Vector((0,-.1,1.6))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.filepath=str(assets/'previews/solar-array-reference-module-rear.png')
bpy.ops.render.render(write_still=True)
camera.location=loc;camera.rotation_euler=rot;scene.render.resolution_x=1536;scene.render.resolution_y=1024
scene.render.filepath=str(assets/'previews/solar-array-reference-module.png')
bpy.ops.wm.save_as_mainfile(filepath=str(assets/'source/solar-array-reference-module.blend'))
stats['stage']='Complete';report.write_text(json.dumps(stats,indent=2))
