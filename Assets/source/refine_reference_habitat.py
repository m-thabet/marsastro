"""Refine curved glazing and airlock trim after the first rendered inspection."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector

assets=Path(__file__).resolve().parents[1];src=assets/'source/build_reference_habitat.py'
h={'__file__':str(src),'__name__':'habitat_helpers'}
exec(compile(src.read_text(encoding='utf8').split('\ntry:\n')[0],str(src),'exec'),h)
scene=bpy.data.scenes['Habitat / Reference Exterior'];bpy.context.window.scene=scene
h['scene']=scene
root=scene.objects['Habitat | reference exterior module'];entry=scene.objects['Airlock | arch door and status lights']
glass=bpy.data.materials['Habitat / Smoked blue glass'];metal=bpy.data.materials['Habitat / Warm brushed titanium']
trim=bpy.data.materials['Habitat / Charcoal equipment casing'];seam=bpy.data.materials['Habitat / Warm panel seam']
# Use all-quad surfaces to avoid a concentrated smooth-normal singularity in the
# center of the reflective glass. The square-to-squircle map matches the rims.
for name,cu,cz,rx,rz,axis in [('Front left paired window',-2.6,2.70,1.15,.52,'front'),
    ('Front right paired window',5,2.70,1,.49,'front'),('Left end window',-.80,2.64,.91,.49,'left'),
    ('Rear left paired window',-3.25,2.7,1.05,.48,'rear'),('Rear right paired window',3.25,2.7,1.05,.48,'rear')]:
    obj=scene.objects[name+' / smoked blue glazing'];vs=[];A=40;B=20
    for j in range(B+1):
        v=-1+2*j/B
        for i in range(A+1):
            u=-1+2*i/A;x=cu+rx*.94*u*(1-.16*v**6);z=cz+rz*.94*v*(1-.16*u**6)
            if axis=='left':point=(h['hull_x'](x,z)-.145,x,z)
            elif axis=='rear':point=(x,-h['hull_y'](x,z)+.145,z)
            else:point=(x,h['hull_y'](x,z)-.145,z)
            vs.append(point)
    fs=[(j*(A+1)+i,j*(A+1)+i+1,(j+1)*(A+1)+i+1,(j+1)*(A+1)+i) for j in range(B) for i in range(A)]
    if axis in ('left','rear'):fs=[tuple(reversed(f)) for f in fs]
    data=bpy.data.meshes.new(name+' / continuous quad glazing');data.from_pydata(vs,[],fs);data.update();data.materials.append(glass)
    for p in data.polygons:p.use_smooth=True
    obj.data=data
    solid=obj.modifiers.new('Glazing thickness','SOLIDIFY');solid.thickness=.035
    if axis in ('left','rear'):
        for suffix in ('ivory rim','deep rubber gasket','inner metal liner'):
            frame=scene.objects[name+' / '+suffix]
            for p in frame.data.polygons:p.flip()
            frame.data.update()
# Crisp outer perimeter separates the projecting arch from the continuous hull.
points=[]
for i in range(180):
    a=i*math.tau/180;x,z=h['squircle'](a,1.777,2.315,3.7)
    points.append((1.45+x,-4.265,2.67+z))
h['line']('Airlock surround recessed outer joint',points,.014,seam,entry,True)
h['box']('Airlock top inspection plate',(1.45,-3.74,5.13),(.96,.70,.10),trim,entry,.075,(math.radians(17),0,0))
h['box']('Airlock left shoulder equipment inset',(-.34,-3.91,3.83),(.11,.65,.75),trim,entry,.055,(0,math.radians(-12),0))
orange=bpy.data.materials['Habitat / Safety orange enamel']
p=next(n for n in orange.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
p.inputs['Base Color'].default_value=(.95,.205,.006,1);p.inputs['Roughness'].default_value=.36
orange.diffuse_color=(.95,.205,.006,1)
for obj in scene.objects:
    if obj.name.startswith('Ramp dark anti-slip tread'):
        obj.data.materials.clear();obj.data.materials.append(trim)
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[1].default_value=.35
try:scene.view_settings.look='AgX - Medium High Contrast'
except TypeError:pass
scene.objects['Large soft studio key'].data.energy=2700
scene.objects['Broad cool studio fill'].data.energy=1750
objects=set()
def visit(o):
    objects.add(o)
    for c in o.children:visit(c)
visit(root);bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(assets/'buildings/habitat-reference-module.glb'),export_format='GLB',
    use_selection=True,use_active_scene=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False,export_extras=True)
deps=bpy.context.evaluated_depsgraph_get();tris=0;coords=[]
for obj in objects:
    if obj.type in {'MESH','CURVE'}:
        ev=obj.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();tris+=len(me.loop_triangles)
        coords += [obj.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
lo=[min(v[i] for v in coords) for i in range(3)];hi=[max(v[i] for v in coords) for i in range(3)]
report=assets/'previews/habitat-reference-module-report.json';stats=json.loads(report.read_text())
stats.update(stage='Rendering refined habitat',nodes=len(objects),triangles=tris,dimensions_meters=[round(hi[i]-lo[i],4) for i in range(3)])
stats['refinements']=['Continuous quad glazing','Correct window surface normals','Airlock surround contour and equipment insets','Deeper orange trim','Dark ramp tread material','Studio contrast']
report.write_text(json.dumps(stats,indent=2))
scene.render.filepath=str(assets/'previews/habitat-reference-module.png');bpy.ops.render.render(write_still=True)
camera=scene.camera;loc=camera.location.copy();rot=camera.rotation_euler.copy()
camera.location=(14,19,12);camera.rotation_euler=(Vector((0,-.6,3))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.filepath=str(assets/'previews/habitat-reference-module-rear.png')
bpy.ops.render.render(write_still=True)
camera.location=loc;camera.rotation_euler=rot;scene.render.resolution_x=1536;scene.render.resolution_y=1024
scene.render.filepath=str(assets/'previews/habitat-reference-module.png')
bpy.ops.wm.save_as_mainfile(filepath=str(assets/'source/habitat-reference-module.blend'))
stats['stage']='Complete';report.write_text(json.dumps(stats,indent=2))
