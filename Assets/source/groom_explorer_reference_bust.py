"""Finish a coherent swept hairstyle with surface-following groom strands."""
import bpy,math,json,random
from pathlib import Path
from mathutils import Vector

assets=Path(__file__).resolve().parents[1];src=assets/'source/build_explorer_reference_bust.py'
h={'__file__':str(src),'__name__':'explorer_helpers'}
exec(compile(src.read_text(encoding='utf8').split('\ntry:\n')[0],str(src),'exec'),h)
scene=bpy.data.scenes['Explorer / Reference Character Bust'];bpy.context.window.scene=scene
hair=scene.objects['Hair | swept chestnut curls'];root=scene.objects['Explorer | reference character bust']
mats=[bpy.data.materials['Explorer / Chestnut strand %02d'%i] for i in range(6)]
h.update(scene=scene,hair=hair,hairtones=mats)
for obj in list(scene.objects):
    if obj.name.startswith(('Overlapping sculpted chestnut curl','Continuous swept hair underlayer',
        'Soft inner volume of curl','Fine curl core strand','Fine combed strand')):
        bpy.data.objects.remove(obj,do_unlink=True)
scalp=scene.objects['Chestnut scalp and swept hairline']
for v in scalp.data.vertices:
    if v.co.z>4.65:v.co.z+=.10*((v.co.z-4.65)/.55)**.8
scalp.data.update()
random.seed(1881)
# Follow the actual cap parameterization, so the strands always have solid hair
# beneath them and cannot read as detached curls or spikes.
for i in range(140):
    theta=math.tau*i/140;pts=[]
    front=(1+math.cos(theta))/2;limit=2.56-1.21*front+.045*math.sin(theta*7)
    for j in range(48):
        t=j/47;phi=.11+(limit-.11)*t
        a=theta+.09*math.sin(phi*3)+.025*math.sin(phi*9+i*.4)
        x=1.013*math.sin(phi)*math.sin(a);y=.1-.824*math.sin(phi)*math.cos(a)
        z=4.05+.99*math.cos(phi)
        if z>4.6:z+=.16*((z-4.6)/.44)**.6
        if z>4.65:z+=.10*((z-4.65)/.55)**.8
        pts.append((x,y,z+.005))
    o=h['curve']('Surface-following wavy groom',pts,.0032,mats[i%5],hair,
        radii=[.25+.75*math.sin(math.pi*(j+.5)/48)**.35 for j in range(48)])
    o.data.bevel_resolution=0
# Short swept waves soften the hairline and retain the portrait's loose fringe.
for i in range(8):
    x=-.83+i*.235
    points=[(x*.82,.02,4.99),(x-.06,-.36,4.96),(x-.14,-.67,4.77),
        (x-.14,-.84,4.57),(x+.04,-.91,4.43+.06*math.sin(i)),(x+.13,-.91,4.49+.06*math.sin(i))]
    h['hair_lock']('Swept hairline wave',points,.125,mats[i%4],6)
for obj in scene.objects:
    if obj.type=='CURVE' and obj.name.startswith('Fine combed strand'):obj.data.bevel_resolution=0
objects=set()
def visit(o):
    objects.add(o)
    for c in o.children:visit(c)
visit(root);bpy.ops.object.select_all(action='DESELECT')
for obj in objects:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(assets/'characters/explorer-reference-bust.glb'),export_format='GLB',
    use_selection=True,use_active_scene=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False)
deps=bpy.context.evaluated_depsgraph_get();tris=0;coords=[]
for obj in objects:
    if obj.type in {'MESH','CURVE'}:
        ev=obj.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();tris+=len(me.loop_triangles)
        coords += [obj.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
lo=[min(p[i] for p in coords) for i in range(3)];hi=[max(p[i] for p in coords) for i in range(3)]
report=assets/'previews/explorer-reference-bust-report.json';stats=json.loads(report.read_text())
stats.update(stage='Rendering groomed portrait',model_nodes=len(objects),triangles=tris,dimensions_meters=[round(hi[i]-lo[i],4) for i in range(3)])
stats['refinements'].append('Coherent swept hairstyle with 140 surface-following groom strands')
report.write_text(json.dumps(stats,indent=2))
scene.render.filepath=str(assets/'previews/explorer-reference-bust.png');bpy.ops.render.render(write_still=True)
camera=scene.camera;loc=camera.location.copy();rot=camera.rotation_euler.copy()
camera.location=(1.55,3.5,1.75);camera.rotation_euler=(Vector((0,0,.79))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=800;scene.render.resolution_y=1000;scene.render.filepath=str(assets/'previews/explorer-reference-bust-back.png')
bpy.ops.render.render(write_still=True)
camera.location=loc;camera.rotation_euler=rot;scene.render.resolution_x=1200;scene.render.resolution_y=1400
scene.render.filepath=str(assets/'previews/explorer-reference-bust.png')
bpy.ops.wm.save_as_mainfile(filepath=str(assets/'source/explorer-reference-bust.blend'))
stats['stage']='Complete';report.write_text(json.dumps(stats,indent=2))
