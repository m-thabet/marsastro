"""Match the reference camera angle and refine the deck and paint finish."""
import bpy,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

assets=Path(__file__).resolve().parents[1]
scene=bpy.data.scenes['Landing Pad / Reference Circular Platform'];bpy.context.window.scene=scene
root=scene.objects['LandingPad | reference circular platform']
for material in bpy.data.materials:
    if material.name.startswith('Landing Pad / Deck titanium variation'):
        p=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        color=p.inputs['Base Color'].default_value
        color=(*[color[i]*.77 for i in range(3)],1)
        p.inputs['Base Color'].default_value=color;material.diffuse_color=color
        p.inputs['Metallic'].default_value=.27;p.inputs['Roughness'].default_value=.70
        p.inputs['Coat Weight'].default_value=0
orange=bpy.data.materials['Landing Pad / Safety orange enamel']
p=next(n for n in orange.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
p.inputs['Base Color'].default_value=(.95,.24,.002,1);p.inputs['Metallic'].default_value=0
p.inputs['Specular IOR Level'].default_value=.22;p.inputs['Coat Weight'].default_value=0
orange.diffuse_color=(.95,.24,.002,1)
objects=set()
def visit(o):
    objects.add(o)
    for c in o.children:visit(c)
visit(root);bpy.ops.object.select_all(action='DESELECT')
for obj in objects:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(assets/'buildings/landing-pad-reference-module.glb'),export_format='GLB',
    use_selection=True,use_active_scene=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False,export_extras=True)
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
coords=[obj.matrix_world@Vector(corner) for obj in objects if obj.type=='MESH' for corner in obj.evaluated_get(deps).bound_box]
def fit(camera):
    bpy.context.view_layer.update()
    projected=[world_to_camera_view(scene,camera,p) for p in coords]
    xmin=min(p.x for p in projected);xmax=max(p.x for p in projected);ymin=min(p.y for p in projected);ymax=max(p.y for p in projected)
    width=camera.data.ortho_scale;height=width/(scene.render.resolution_x/scene.render.resolution_y)
    camera.location+=camera.rotation_euler.to_matrix()@Vector((((xmin+xmax)/2-.5)*width,((ymin+ymax)/2-.5)*height,0))
    camera.data.ortho_scale*=max((xmax-xmin)/.90,(ymax-ymin)/.86);bpy.context.view_layer.update()
camera=scene.camera;camera.location=(8,-17,11.5)
camera.rotation_euler=(Vector((0,-.7,.65))-camera.location).to_track_quat('-Z','Y').to_euler();fit(camera)
report=assets/'previews/landing-pad-reference-module-report.json';stats=json.loads(report.read_text())
stats['stage']='Rendering refined landing-pad view'
stats['refinements']=['Reference-facing left ramp composition','Darker matte titanium deck','Less reflective safety-orange guide paint']
report.write_text(json.dumps(stats,indent=2))
scene.render.filepath=str(assets/'previews/landing-pad-reference-module.png');bpy.ops.render.render(write_still=True)
loc=camera.location.copy();rot=camera.rotation_euler.copy();scale=camera.data.ortho_scale
camera.location=(0,-1.2,25);camera.rotation_euler=(Vector((0,-1.2,0))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1200;scene.render.resolution_y=1200;camera.data.ortho_scale=18;fit(camera)
scene.render.filepath=str(assets/'previews/landing-pad-reference-module-top.png');bpy.ops.render.render(write_still=True)
camera.location=loc;camera.rotation_euler=rot;camera.data.ortho_scale=scale
scene.render.resolution_x=1600;scene.render.resolution_y=900;scene.render.filepath=str(assets/'previews/landing-pad-reference-module.png')
bpy.ops.wm.save_as_mainfile(filepath=str(assets/'source/landing-pad-reference-module.blend'))
stats['stage']='Complete';report.write_text(json.dumps(stats,indent=2))
