"""Polish the Mars hero view and prevent emission from the rear atmosphere."""
import bpy,json,math
from pathlib import Path
from mathutils import Matrix

assets=Path(__file__).resolve().parents[1]
scene=bpy.data.scenes['Mars / Cinematic Planet'];bpy.context.window.scene=scene
planet=scene.objects['Mars | UV sphere with portable 4K surface']
planet.rotation_euler=(Matrix.Rotation(math.radians(-8),3,'X')@planet.rotation_euler.to_matrix()).to_euler()
sun=scene.objects['Sun | corner glow source'];sun.location=(-7.08,4.0,3.83)
atmo=bpy.data.materials['Mars Cinema / warm thin limb'];nt=atmo.node_tree
mix=next(n for n in nt.nodes if n.type=='MIX_SHADER')
geo=next(n for n in nt.nodes if n.type=='NEW_GEOMETRY')
original=mix.inputs[0].links[0].from_socket
front=nt.nodes.new('ShaderNodeMath');front.operation='SUBTRACT';front.inputs[0].default_value=1
nt.links.new(geo.outputs['Backfacing'],front.inputs[1])
mask=nt.nodes.new('ShaderNodeMath');mask.operation='MULTIPLY'
nt.links.new(original,mask.inputs[0]);nt.links.new(front.outputs[0],mask.inputs[1]);nt.links.new(mask.outputs[0],mix.inputs[0])
scene.objects['Very soft cool shadow fill'].data.energy=145

root=scene.objects['MarsScene | cinematic reference composition'];objects=set()
def visit(o):
    objects.add(o)
    for child in o.children:visit(child)
visit(root)
bpy.ops.object.select_all(action='DESELECT')
for obj in objects:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(assets/'world/mars-cinematic-scene.glb'),export_format='GLB',
    use_selection=True,use_active_scene=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False,export_extras=True)
bpy.ops.object.select_all(action='DESELECT')
planet.select_set(True);planet.parent.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(assets/'world/mars-textured-planet.glb'),export_format='GLB',
    use_selection=True,use_active_scene=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False,export_extras=True)
report=assets/'previews/mars-cinematic-scene-report.json';stats=json.loads(report.read_text())
stats['stage']='Rendering refined Mars scene'
stats['refinements']=['Sunlit front-facing atmospheric limb','Visible warm corner sun','Canyon centered by an 8-degree globe tilt','Gentle blue shadow fill']
report.write_text(json.dumps(stats,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(assets/'source/mars-cinematic-scene.blend'))
bpy.ops.render.render(write_still=True)
stats['stage']='Complete';report.write_text(json.dumps(stats,indent=2))
