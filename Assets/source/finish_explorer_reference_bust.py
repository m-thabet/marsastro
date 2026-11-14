"""Support the sculpted curls with continuous volume and optimize fine strands."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector

assets=Path(__file__).resolve().parents[1]
src=assets/'source/build_explorer_reference_bust.py'
h={'__file__':str(src),'__name__':'explorer_helpers'}
exec(compile(src.read_text(encoding='utf8').split('\ntry:\n')[0],str(src),'exec'),h)
scene=bpy.data.scenes['Explorer / Reference Character Bust'];bpy.context.window.scene=scene
hair=scene.objects['Hair | swept chestnut curls'];root=scene.objects['Explorer | reference character bust']
h['scene']=scene
mats=[bpy.data.materials['Explorer / Chestnut strand %02d'%i] for i in range(6)]
# The curls sit on continuous supporting hair volume, with dark inner cores.
for center,size in [((-.32,-.51,4.79),(.76,.25,.48)),((.53,-.44,4.79),(.48,.26,.45)),((-.05,.01,5.08),(.77,.55,.25))]:
    h['sphere']('Continuous swept hair underlayer',center,size,mats[1],hair,64)
settings=[(-.72,-.54,4.63,.29),(-.27,-.74,4.71,.33),(.24,-.76,4.77,.37),(.70,-.53,4.65,.29),
    (-.72,-.16,4.98,.31),(-.19,-.34,5.04,.35),(.36,-.27,5.02,.35),(.75,-.04,4.96,.29),
    (-.40,.12,5.18,.28),(.12,.14,5.20,.28),(-.91,-.27,4.39,.21),(.94,-.23,4.36,.22)]
for i,(x,y,z,r) in enumerate(settings):
    h['sphere']('Soft inner volume of curl',(x,y+.055,z),(r*.87,.12,r*.69),mats[i%3],hair,40)
    for k in range(6):
        pts=[]
        theta=-1.1+2.2*k/5
        for j in range(25):
            t=-.85+1.70*j/24
            xx=x+r*.80*t;zz=z+r*.57*math.sin(theta+.37*t)
            yy=y+.055-.124*math.sqrt(max(.03,1-t*t-(.57*math.sin(theta+.37*t)/.69)**2))
            pts.append((xx,yy,zz))
        h['curve']('Fine curl core strand',pts,.002,mats[(i+k)%4],hair)
sculpt=scene.objects['Continuous sculpted head and nose']
if sculpt.modifiers.get('Smooth portrait surface'):sculpt.modifiers.remove(sculpt.modifiers['Smooth portrait surface'])
sculpt.modifiers['Softened sculpt transitions'].iterations=20
for o in scene.objects:
    if o.type=='CURVE' and ('strand' in o.name.lower() or 'eyebrow hair' in o.name.lower()):o.data.bevel_resolution=0
objects=set()
def visit(o):
    objects.add(o)
    for c in o.children:visit(c)
visit(root);bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(assets/'characters/explorer-reference-bust.glb'),export_format='GLB',
    use_selection=True,use_active_scene=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False)
deps=bpy.context.evaluated_depsgraph_get();tris=0;coords=[]
for o in objects:
    if o.type in {'MESH','CURVE'}:
        ev=o.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();tris+=len(me.loop_triangles)
        coords += [o.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
lo=[min(v[i] for v in coords) for i in range(3)];hi=[max(v[i] for v in coords) for i in range(3)]
report=assets/'previews/explorer-reference-bust-report.json';stats=json.loads(report.read_text())
stats.update(stage='Rendering final portrait',model_nodes=len(objects),triangles=tris,dimensions_meters=[round(hi[i]-lo[i],4) for i in range(3)])
stats['refinements']+=['Continuous supporting curl volume','Reduced fine-strand geometry']
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
