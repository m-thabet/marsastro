"""Final surface and greenhouse pass for the generated reference outpost."""
import bpy
import math
import json
from pathlib import Path
from mathutils import noise, Vector

assets=Path(__file__).resolve().parents[1]
scene=bpy.data.scenes['Mars / Reference Outpost'];bpy.context.window.scene=scene
report=assets/'previews/mars-reference-outpost-report.json'
stats=json.loads(report.read_text());stats['stage']='Polishing surfaces'
report.write_text(json.dumps(stats,indent=2))

cliff=bpy.data.materials.new('Outpost / Natural sandstone vertex colors')
cliff.diffuse_color=(.50,.16,.06,1);cliff.use_nodes=True
p=cliff.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.92
v=cliff.node_tree.nodes.new('ShaderNodeVertexColor');v.layer_name='CliffColor'
cliff.node_tree.links.new(v.outputs['Color'],p.inputs['Base Color'])
for obj in scene.objects:
    if not obj.name.startswith('Eroded layered mesa'):continue
    obj.data.materials.clear();obj.data.materials.append(cliff)
    colors=obj.data.color_attributes.new(name='CliffColor',type='FLOAT_COLOR',domain='CORNER')
    for loop in obj.data.loops:
        pos=obj.data.vertices[loop.vertex_index].co
        variation=1+.055*noise.noise_vector(pos*.7)[0]+.035*math.sin(pos.z*2.4)
        # Horizontal variation is deliberately restrained; avoid colored face tiles.
        colors.data[loop.index].color=(.50*variation,.16*variation,.060*variation,1)
    for f in obj.data.polygons:f.material_index=0
    obj.data.color_attributes.active_color=colors

soil=bpy.data.materials['Outpost / Terracotta sand'];nt=soil.node_tree
geo=nt.nodes.new('ShaderNodeNewGeometry')
coarse=next(n for n in nt.nodes if n.bl_idname=='ShaderNodeTexNoise')
coarse.inputs['Scale'].default_value=.55
nt.links.new(geo.outputs['Position'],coarse.inputs['Vector'])
fine=nt.nodes.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=18
fine.inputs['Detail'].default_value=2
nt.links.new(geo.outputs['Position'],fine.inputs['Vector'])
bump=next(n for n in nt.nodes if n.bl_idname=='ShaderNodeBump')
nt.links.new(fine.outputs['Fac'],bump.inputs['Height'])
bump.inputs['Distance'].default_value=.055;bump.inputs['Strength'].default_value=.27

dome=scene.objects['Individual triangular transparent dome panes']
gx,gy=-1,13;radius=6.8;base=2.2;seg=18;rings=5
verts=[]
for j in range(rings):
    phi=math.pi/2*j/rings;r=radius*math.cos(phi)
    for i in range(seg):
        a=math.tau*(i+.5*(j%2))/seg
        verts.append((gx+r*math.cos(a),gy+r*math.sin(a),base+radius*.79*math.sin(phi)))
top=len(verts);verts.append((gx,gy,base+radius*.79))
faces=[]
for j in range(rings-1):
    for i in range(seg):
        a=j*seg+i;b=j*seg+(i+1)%seg;c=(j+1)*seg+i;d=(j+1)*seg+(i+1)%seg
        faces.extend([(a,b,d),(a,d,c)] if j%2 else [(a,b,c),(b,d,c)])
faces += [((rings-1)*seg+i,(rings-1)*seg+(i+1)%seg,top) for i in range(seg)]
data=bpy.data.meshes.new('Simplified architectural dome glazing')
data.from_pydata(verts,[],faces);data.materials.append(dome.data.materials[0]);data.update();dome.data=data
frame=bpy.data.materials['Outpost / Clean roof panels']
for obj in list(scene.objects):
    if obj.name.startswith('Geodesic aluminium glazing bar'):bpy.data.objects.remove(obj,do_unlink=True)
edges=set()
for face in faces:
    for a,b in zip(face,face[1:]+face[:1]):edges.add(tuple(sorted((a,b))))
for a,b in edges:
    curve=bpy.data.curves.new('Dome strut','CURVE');curve.dimensions='3D'
    curve.bevel_depth=.046;curve.bevel_resolution=2
    s=curve.splines.new('POLY');s.points.add(1)
    for p,co in zip(s.points,(verts[a],verts[b])):p.co=(*co,1)
    obj=bpy.data.objects.new('Geodesic aluminium glazing bar',curve)
    scene.collection.objects.link(obj);obj.parent=dome.parent;curve.materials.append(frame)
# Move the dome's central antenna down with its roof.
for obj in scene.objects:
    if obj.parent==dome.parent and obj.name.startswith('Antenna'):
        obj.location.z-=radius*(1-.79)

bpy.ops.wm.save_as_mainfile(filepath=str(assets/'source/mars-reference-outpost.blend'))
bpy.ops.object.select_all(action='DESELECT')
for obj in scene.objects:
    if obj.type in {'MESH','CURVE','FONT','EMPTY'}:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(assets/'world/mars-reference-outpost.glb'),export_format='GLB',
    use_selection=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False)
deps=bpy.context.evaluated_depsgraph_get();triangles=0
for obj in scene.objects:
    if obj.type in {'MESH','CURVE','FONT'}:
        ev=obj.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();triangles+=len(me.loop_triangles);ev.to_mesh_clear()
stats.update(stage='Rendering final preview',triangles=triangles,objects=len(scene.objects))
stats['refinements']+=['Continuous sandstone vertex colors','Fine sand bump','Simplified 162-pane greenhouse dome']
report.write_text(json.dumps(stats,indent=2))
bpy.ops.render.render(write_still=True)
stats['stage']='Complete';report.write_text(json.dumps(stats,indent=2))
