"""Close the helmet rim and refine the robot's curved display after review."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector

assets=Path(__file__).resolve().parents[1]
# Load only the reusable helper definitions, not the original build operation.
source=assets/'source/build_nova_reference_robot.py'
helpers={'__file__':str(source),'__name__':'robot_helpers'}
exec(compile(source.read_text(encoding='utf8').split('\ntry:\n')[0],str(source),'exec'),helpers)
scene=bpy.data.scenes['NOVA / Reference Robot Bust'];bpy.context.window.scene=scene
root=scene.objects['NOVA | reference robot bust'];head=scene.objects['Head | ceramic helmet and display']
face=scene.objects['Face | modeled eyes brows and smile']
helpers.update(scene=scene,head=head)
cream=bpy.data.materials['NOVA / Pearl warm ceramic']
navy=bpy.data.materials['NOVA / Midnight blue glossy face']

def remove(name):
    obj=scene.objects.get(name)
    if obj:bpy.data.objects.remove(obj,do_unlink=True)

remove('Helmet full back and side shell')
shell=helpers['superellipsoid']('Helmet full back and side shell',(0,0,3.8),(1.73,.95,1.48),2/3.5,cream,head)
remove('Thick ceramic face-opening rim')
rim=helpers['visor_rings']('Thick ceramic face-opening rim',[(1.73,1.48,0),(1.72,1.39,-.48),
    (1.67,1.34,-.73),(1.59,1.26,-.94),(1.50,1.17,-1.005)],cream,head)
remove('Convex midnight face display');remove('Visor side return')
helpers['superellipsoid']('Convex midnight face display',(0,-.99,3.8),(1.475,.205,1.15),2/3.5,navy,face,128,64)
p=next(n for n in navy.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
p.inputs['Base Color'].default_value=(.003,.007,.018,1)
p.inputs['Metallic'].default_value=.12;p.inputs['Roughness'].default_value=.19
p.inputs['Specular IOR Level'].default_value=.32

def setcolor(name,color,emission=None):
    mat=bpy.data.materials[name];mat.diffuse_color=(*color,1)
    bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value=(*color,1)
    if emission is not None:
        bs.inputs['Emission Color'].default_value=(*color,1)
        bs.inputs['Emission Strength'].default_value=emission
setcolor('NOVA / Olive green armor accents',(.28,.40,.075))
setcolor('NOVA / Mint status lights',(.045,.72,.10),2)
setcolor('NOVA / Pearl warm ceramic',(.83,.68,.56))

# Place the crown insert directly on the visible helmet surface rather than
# allowing it to disappear behind the newly continuous outer rim.
deps=bpy.context.evaluated_depsgraph_get()
shell_eval=shell.evaluated_get(deps);rim_eval=rim.evaluated_get(deps)
for name,offset in [('Crown green inset border',.012),('Rounded olive crown panel',.026)]:
    obj=scene.objects[name]
    for vertex in obj.data.vertices:
        x,z=vertex.co.x,vertex.co.z;hits=[]
        for surface in (shell_eval,rim_eval):
            hit,loc,normal,index=surface.ray_cast(Vector((x,-5,z)),Vector((0,1,0)))
            if hit:hits.append(loc.y)
        if hits:vertex.co.y=min(hits)-offset
    obj.data.update()
scene.objects['Large warm portrait softbox'].data.energy=240
scene.objects['Cool front fill softbox'].data.energy=110
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[1].default_value=.3

report=assets/'previews/nova-reference-robot-bust-report.json'
stats=json.loads(report.read_text());stats['stage']='Exporting refined robot';report.write_text(json.dumps(stats,indent=2))
bpy.ops.object.select_all(action='DESELECT')
objects=set()
def visit(o):
    objects.add(o)
    for child in o.children:visit(child)
visit(root)
for obj in objects:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(assets/'characters/nova-reference-robot-bust.glb'),export_format='GLB',
    use_selection=True,use_active_scene=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False)
deps=bpy.context.evaluated_depsgraph_get();tris=0;coords=[]
for obj in objects:
    if obj.type in {'MESH','CURVE'}:
        ev=obj.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();tris+=len(me.loop_triangles)
        # Derive bounds from evaluated vertices, not cached pre-update boxes.
        coords += [obj.matrix_world@v.co for v in me.vertices]
        ev.to_mesh_clear()
low=[min(v[i] for v in coords) for i in range(3)];high=[max(v[i] for v in coords) for i in range(3)]
stats.update(triangles=tris,model_objects=len(objects),dimensions_meters=[round(high[i]-low[i],4) for i in range(3)])
stats['refinements']=['Continuous helmet rim','Volumetric display without center-pole artifact','Darker midnight glass','More saturated green trim','Surface-mounted crown insert']
camera=scene.camera;loc=camera.location.copy();rot=camera.rotation_euler.copy()
stats['stage']='Rendering refined portrait';report.write_text(json.dumps(stats,indent=2))
scene.render.resolution_x=1200;scene.render.resolution_y=1400
scene.render.filepath=str(assets/'previews/nova-reference-robot-bust.png');bpy.ops.render.render(write_still=True)
camera.location=(1.65,3.5,1.7);camera.rotation_euler=(Vector((0,0,.76))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=800;scene.render.resolution_y=1000
scene.render.filepath=str(assets/'previews/nova-reference-robot-bust-back.png');bpy.ops.render.render(write_still=True)
camera.location=loc;camera.rotation_euler=rot;scene.render.resolution_x=1200;scene.render.resolution_y=1400
scene.render.filepath=str(assets/'previews/nova-reference-robot-bust.png')
bpy.ops.wm.save_as_mainfile(filepath=str(assets/'source/nova-reference-robot-bust.blend'))
stats['stage']='Complete';report.write_text(json.dumps(stats,indent=2))
