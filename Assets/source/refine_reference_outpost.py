"""Polish only the generated reference scene after visual review."""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector

ASSETS=Path(__file__).resolve().parents[1]
scene=bpy.data.scenes['Mars / Reference Outpost']
bpy.context.window.scene=scene
report=ASSETS/'previews/mars-reference-outpost-report.json'
stats=json.loads(report.read_text())
stats['stage']='Refining composition'
report.write_text(json.dumps(stats,indent=2))

road=scene.objects.get('Compacted loop road')
road.scale.z=.035

# Correct the alternating staggered rings so each panel is a compact triangle.
dome=scene.objects['Individual triangular transparent dome panes']
verts=[tuple(v.co) for v in dome.data.vertices]
seg=24;rings=7;faces=[]
for j in range(rings-1):
    for i in range(seg):
        a=j*seg+i;b=j*seg+(i+1)%seg;c=(j+1)*seg+i;d=(j+1)*seg+(i+1)%seg
        faces.extend([(a,b,d),(a,d,c)] if j%2 else [(a,b,c),(b,d,c)])
top=len(verts)-1
faces += [((rings-1)*seg+i,(rings-1)*seg+(i+1)%seg,top) for i in range(seg)]
material=dome.data.materials[0]
data=bpy.data.meshes.new('Corrected geodesic glazing')
data.from_pydata(verts,[],faces);data.materials.append(material);data.update()
dome.data=data
frame_material=bpy.data.materials['Outpost / Clean roof panels']
for obj in list(scene.objects):
    if obj.name.startswith('Geodesic aluminium glazing bar'):
        bpy.data.objects.remove(obj,do_unlink=True)
edges=set()
for f in faces:
    for a,b in zip(f,f[1:]+f[:1]):edges.add(tuple(sorted((a,b))))
for a,b in edges:
    curve=bpy.data.curves.new('Geodesic strut','CURVE');curve.dimensions='3D'
    curve.bevel_depth=.035;curve.bevel_resolution=2
    s=curve.splines.new('POLY');s.points.add(1)
    for p,co in zip(s.points,(verts[a],verts[b])):p.co=(*co,1)
    obj=bpy.data.objects.new('Geodesic aluminium glazing bar',curve)
    scene.collection.objects.link(obj);obj.parent=dome.parent;curve.materials.append(frame_material)
material.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=.12
material.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=0
material.diffuse_color=(*material.diffuse_color[:3],.12)
for obj in scene.objects:
    if obj.name.startswith('Crop leaf'):obj.location.z+=.7

# Round off the largest cliff transitions without losing the strata.
for obj in scene.objects:
    if obj.name.startswith('Eroded layered mesa'):
        sub=obj.modifiers.new('Eroded cliff transitions','SUBSURF')
        sub.levels=1;sub.render_levels=1
        for p in obj.data.polygons:p.use_smooth=True

camera=scene.camera
camera.location=(27,-105,43)
camera.rotation_euler=(Vector((0,11,2.8))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.lens=48
scene.render.resolution_x=1600;scene.render.resolution_y=900
scene.view_settings.exposure=.45
sun=scene.objects['Warm late-afternoon sun'];sun.data.color=(1,.8,.62);sun.data.energy=3.1
scene.objects['Large soft sky fill'].data.energy=5200

# Soft peach horizon, with no downloaded sky texture.
nt=scene.world.node_tree
coord=nt.nodes.new('ShaderNodeTexCoord')
separate=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(coord.outputs['Normal'],separate.inputs[0])
scale=nt.nodes.new('ShaderNodeMath');scale.operation='MULTIPLY_ADD'
scale.inputs[1].default_value=1.5;scale.inputs[2].default_value=.45
nt.links.new(separate.outputs['Z'],scale.inputs[0])
ramp=nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position=.1;ramp.color_ramp.elements[0].color=(.62,.31,.17,1)
ramp.color_ramp.elements[1].position=.9;ramp.color_ramp.elements[1].color=(.8,.52,.34,1)
nt.links.new(scale.outputs[0],ramp.inputs[0])
nt.links.new(ramp.outputs[0],nt.nodes['Background'].inputs[0]);nt.nodes['Background'].inputs[1].default_value=.65

bpy.ops.wm.save_as_mainfile(filepath=str(ASSETS/'source/mars-reference-outpost.blend'))
bpy.ops.object.select_all(action='DESELECT')
for obj in scene.objects:
    if obj.type in {'MESH','CURVE','FONT','EMPTY'}:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ASSETS/'world/mars-reference-outpost.glb'),export_format='GLB',
                          use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_yup=True)
deps=bpy.context.evaluated_depsgraph_get();triangles=0
for obj in scene.objects:
    if obj.type in {'MESH','CURVE','FONT'}:
        evaluated=obj.evaluated_get(deps);data=evaluated.to_mesh()
        data.calc_loop_triangles();triangles+=len(data.loop_triangles);evaluated.to_mesh_clear()
stats['triangles']=triangles
stats['stage']='Rendering refined preview'
stats['refinements']=['Ground-level drive','Corrected triangular greenhouse frame','Softer eroded cliffs','Lower strategy camera','Brighter peach atmosphere']
report.write_text(json.dumps(stats,indent=2))
bpy.ops.render.render(write_still=True)
stats['stage']='Complete'
report.write_text(json.dumps(stats,indent=2))
