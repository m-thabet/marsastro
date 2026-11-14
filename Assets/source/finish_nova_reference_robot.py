"""Replace the projected crown insert with a clean machined rounded plate."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector

assets=Path(__file__).resolve().parents[1]
scene=bpy.data.scenes['NOVA / Reference Robot Bust'];bpy.context.window.scene=scene
head=scene.objects['Head | ceramic helmet and display']
for name in ('Crown green inset border','Rounded olive crown panel'):
    obj=scene.objects.get(name)
    if obj:bpy.data.objects.remove(obj,do_unlink=True)

def rounded_plate(name,width,length,radius,depth,mat,offset):
    outline=[]
    for cx,cy,start in [(width/2-radius,length/2-radius,0),(-width/2+radius,length/2-radius,90),
                        (-width/2+radius,-length/2+radius,180),(width/2-radius,-length/2+radius,270)]:
        for i in range(17):
            a=math.radians(start+i*90/16)
            outline.append((cx+radius*math.cos(a),cy+radius*math.sin(a)))
    N=len(outline);verts=[(x,y,z) for z in (-depth/2,depth/2) for x,y in outline]
    faces=[tuple(reversed(range(N))),tuple(N+i for i in range(N))]
    faces += [(i,(i+1)%N,N+(i+1)%N,N+i) for i in range(N)]
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update();data.materials.append(mat)
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.parent=head
    obj.location=(0,-.63-.342*offset,5.16+.94*offset);obj.rotation_euler.x=math.radians(20)
    mod=obj.modifiers.new('Machined plate lip','BEVEL');mod.width=.008;mod.segments=3
    obj.modifiers.new('Plate weighted normals','WEIGHTED_NORMAL')
    return obj

rounded_plate('Crown green inset border',.72,.79,.13,.035,bpy.data.materials['NOVA / Olive inset gasket'],0)
rounded_plate('Rounded olive crown panel',.655,.725,.115,.035,bpy.data.materials['NOVA / Olive green armor accents'],.023)
scene.render.filepath=str(assets/'previews/nova-reference-robot-bust.png')
report=assets/'previews/nova-reference-robot-bust-report.json';stats=json.loads(report.read_text())
stats['stage']='Rendering final crown and portrait';report.write_text(json.dumps(stats,indent=2))
root=scene.objects['NOVA | reference robot bust'];objects=set()
def visit(o):
    objects.add(o)
    for child in o.children:visit(child)
visit(root)
bpy.ops.object.select_all(action='DESELECT')
for obj in objects:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(assets/'characters/nova-reference-robot-bust.glb'),export_format='GLB',
    use_selection=True,use_active_scene=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False)
deps=bpy.context.evaluated_depsgraph_get();triangles=0
for obj in objects:
    if obj.type in {'MESH','CURVE'}:
        ev=obj.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();triangles+=len(me.loop_triangles);ev.to_mesh_clear()
stats['triangles']=triangles;stats['refinements'].append('Machined rounded crown plate')
bpy.ops.render.render(write_still=True)
camera=scene.camera;loc=camera.location.copy();rot=camera.rotation_euler.copy()
camera.location=(1.65,3.5,1.7);camera.rotation_euler=(Vector((0,0,.76))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=800;scene.render.resolution_y=1000
scene.render.filepath=str(assets/'previews/nova-reference-robot-bust-back.png');bpy.ops.render.render(write_still=True)
camera.location=loc;camera.rotation_euler=rot
scene.render.resolution_x=1200;scene.render.resolution_y=1400
scene.render.filepath=str(assets/'previews/nova-reference-robot-bust.png')
bpy.ops.wm.save_as_mainfile(filepath=str(assets/'source/nova-reference-robot-bust.blend'))
stats['stage']='Complete';report.write_text(json.dumps(stats,indent=2))
