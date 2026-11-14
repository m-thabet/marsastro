"""Refine the explorer hairstyle and soften the sculpt after visual review."""
import bpy,math,json,random
from pathlib import Path
from mathutils import Vector

assets=Path(__file__).resolve().parents[1]
src=assets/'source/build_explorer_reference_bust.py'
helpers={'__file__':str(src),'__name__':'explorer_helpers'}
exec(compile(src.read_text(encoding='utf8').split('\ntry:\n')[0],str(src),'exec'),helpers)
scene=bpy.data.scenes['Explorer / Reference Character Bust'];bpy.context.window.scene=scene
root=scene.objects['Explorer | reference character bust'];hair=scene.objects['Hair | swept chestnut curls']
head=scene.objects['Head | sculpted face ears and neck'];suit=scene.objects['Suit | cream shell orange trim and collar']
hairtones=[bpy.data.materials['Explorer / Chestnut strand %02d'%i] for i in range(6)]
for m in hairtones:
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    color=p.inputs['Base Color'].default_value
    p.inputs['Base Color'].default_value=(color[0]*.5,color[1]*.5,color[2]*.5,1)
    p.inputs['Roughness'].default_value=.53;p.inputs['Specular IOR Level'].default_value=.25
helpers.update(scene=scene,hair=hair,hairtones=hairtones)

for obj in list(scene.objects):
    if obj.name.startswith(('Sculpted swept front curl','Side and rear wavy hair lock','Tapered sideburn','Fine combed strand')):
        bpy.data.objects.remove(obj,do_unlink=True)
# A fuller scalp supports the curls so their roots do not read as isolated spikes.
scalp=scene.objects['Chestnut scalp and swept hairline']
for v in scalp.data.vertices:
    if v.co.z>4.6:v.co.z+=.16*((v.co.z-4.6)/.44)**.6
scalp.data.update()

curl_settings=[(-.72,-.54,4.63,.29,1),(-.27,-.74,4.71,.33,-1),(.24,-.76,4.77,.37,1),(.70,-.53,4.65,.29,-1),
    (-.72,-.16,4.98,.31,1),(-.19,-.34,5.04,.35,1),(.36,-.27,5.02,.35,-1),(.75,-.04,4.96,.29,1),
    (-.40,.12,5.18,.28,-1),(.12,.14,5.20,.28,1),(-.91,-.27,4.39,.21,-1),(.94,-.23,4.36,.22,1)]
for i,(cx,cy,cz,r,direction) in enumerate(curl_settings):
    points=[]
    for k in range(9):
        t=k/8;a=math.radians(30+direction*286*t)
        rr=r*(1-.35*t*t)
        points.append((cx+rr*math.cos(a),cy+.085*math.cos(a+.4)-.035*math.sin(math.pi*t),cz+rr*.80*math.sin(a)))
    # The tip turns inward, producing a single C-shaped lock rather than a tower.
    helpers['hair_lock']('Overlapping sculpted chestnut curl',points,.12+(i%3)*.012,hairtones[i%5],5)
for i in range(25):
    theta=.76+(math.tau-1.52)*i/24;points=[]
    end=2.14+.40*max(0,-math.cos(theta))
    for k in range(7):
        t=k/6;phi=.55+(end-.55)*t;a=theta+.20*math.sin(t*math.tau)
        rr=1.02+.055*math.sin(math.pi*t)
        points.append((rr*math.sin(phi)*math.sin(a),.10-.84*math.sin(phi)*math.cos(a),4.05+1.12*math.cos(phi)))
    helpers['hair_lock']('Side and rear wavy hair lock',points,.125,hairtones[i%5],3)
for sx in (-1,1):
    helpers['hair_lock']('Tapered sideburn',[(sx*.86,-.20,4.08),(sx*.94,-.19,3.94),(sx*.94,-.18,3.73),(sx*.91,-.18,3.61)],.075,hairtones[0],3)

sculpt=scene.objects['Continuous sculpted head and nose']
smooth=sculpt.modifiers.new('Softened sculpt transitions','SMOOTH');smooth.factor=.75;smooth.iterations=7
sub=sculpt.modifiers.new('Smooth portrait surface','SUBSURF');sub.levels=1;sub.render_levels=1

# Replace polygon-assigned color blocks with clean continuous orange shoulder insets.
orange=bpy.data.materials['Explorer / Safety orange piping']
for obj in scene.objects:
    if obj.name.startswith('Rounded suit shoulder'):
        for p in obj.data.polygons:p.material_index=0
for sx in (-1,1):
    vs=[];A=18;B=30
    for j in range(B+1):
        phi=.18+1.27*j/B
        for i in range(A+1):
            a=-1.37+.50*i/A
            vs.append((sx*(1.26+.605*math.sin(phi)*math.cos(a)),.10+.516*math.sin(phi)*math.sin(a),1.22+.765*math.cos(phi)))
    fs=[(j*(A+1)+i,j*(A+1)+i+1,(j+1)*(A+1)+i+1,(j+1)*(A+1)+i) for j in range(B) for i in range(A)]
    helpers['mesh']('Continuous orange shoulder panel',vs,fs,orange,suit)

# A gentle head tilt adds the relaxed posture seen in the reference.
pose=bpy.data.objects.new('Head pose | relaxed reference tilt',None);scene.collection.objects.link(pose);pose.parent=root
pose.location=(0,0,3.7)
for group_name in ['Head | sculpted face ears and neck','Expression | eyes lids brows and smile',
    'Hair | swept chestnut curls','Glasses | rectangular frames and temples']:
    o=scene.objects[group_name];o.parent=pose;o.location=(0,0,-3.7)
pose.rotation_euler=(0,math.radians(-4),math.radians(-3))
bpy.context.view_layer.update()
report=assets/'previews/explorer-reference-bust-report.json';stats=json.loads(report.read_text())
stats['stage']='Exporting refined character';report.write_text(json.dumps(stats,indent=2))
objects=set()
def visit(o):
    objects.add(o)
    for c in o.children:visit(c)
visit(root);bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(assets/'characters/explorer-reference-bust.glb'),export_format='GLB',
    use_selection=True,use_active_scene=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False)
deps=bpy.context.evaluated_depsgraph_get();triangles=0;coords=[]
for o in objects:
    if o.type in {'MESH','CURVE'}:
        ev=o.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();triangles+=len(me.loop_triangles)
        coords += [o.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
lo=[min(p[i] for p in coords) for i in range(3)];hi=[max(p[i] for p in coords) for i in range(3)]
stats.update(triangles=triangles,model_nodes=len(objects),dimensions_meters=[round(hi[i]-lo[i],4) for i in range(3)])
stats['refinements']=['Overlapping C-shaped hair locks','Fuller chestnut hair mass','Smoothed facial sculpt','Clean orange shoulder panels','Relaxed head tilt']
stats['stage']='Rendering refined front portrait';report.write_text(json.dumps(stats,indent=2))
scene.render.filepath=str(assets/'previews/explorer-reference-bust.png');bpy.ops.render.render(write_still=True)
camera=scene.camera;loc=camera.location.copy();rot=camera.rotation_euler.copy()
camera.location=(1.55,3.5,1.75);camera.rotation_euler=(Vector((0,0,.79))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=800;scene.render.resolution_y=1000;scene.render.filepath=str(assets/'previews/explorer-reference-bust-back.png')
bpy.ops.render.render(write_still=True)
camera.location=loc;camera.rotation_euler=rot;scene.render.resolution_x=1200;scene.render.resolution_y=1400
scene.render.filepath=str(assets/'previews/explorer-reference-bust.png')
bpy.ops.wm.save_as_mainfile(filepath=str(assets/'source/explorer-reference-bust.blend'))
stats['stage']='Complete';report.write_text(json.dumps(stats,indent=2))
