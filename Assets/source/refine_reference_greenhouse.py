"""Expose the planted interior floor and refine the greenhouse preview."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

assets=Path(__file__).resolve().parents[1]
scene=bpy.data.scenes['Greenhouse / Reference Hydroponics'];bpy.context.window.scene=scene
root=scene.objects['Greenhouse | reference hydroponics module']
# The sill is a perimeter wall, not a solid block hiding the lower planter walls.
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,1.13));cutter=bpy.context.object
cutter.name='Construction | hidden sill interior cutter';cutter.scale=(10.0,5.0,1.0)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bevel=cutter.modifiers.new('Inner sill corner radius','BEVEL');bevel.width=.12;bevel.segments=3
bpy.ops.object.modifier_apply(modifier=bevel.name)
cutter.hide_render=True;cutter.hide_set(True)
sill=scene.objects['Ivory greenhouse sill']
boolean=sill.modifiers.new('Open interior sill perimeter','BOOLEAN');boolean.operation='DIFFERENCE';boolean.solver='EXACT';boolean.object=cutter
sill.modifiers.new('Cut sill weighted normals','WEIGHTED_NORMAL')
for i,color in enumerate([(.07,.21,.012),(.12,.30,.018),(.18,.36,.035)]):
    material=bpy.data.materials['Greenhouse / Leaf green %d'%i]
    p=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.72
    p.inputs['Specular IOR Level'].default_value=.25;p.inputs['Coat Weight'].default_value=.02
    material.diffuse_color=(*color,1)
# Add short stems between the growing medium and each modeled leaf cluster.
for foliage in [o for o in scene.objects if o.name.startswith('Crop foliage | ')]:
    vs=[];fs=[];bed=foliage.parent
    for plant in range(8):
        offset=plant*7*8*3
        center=sum((foliage.data.vertices[offset+k].co for k in range(3)),Vector())/3
        for z in (1.196,1.29):
            for j in range(6):
                a=math.tau*j/6;vs.append((center.x+.016*math.cos(a),center.y+.016*math.sin(a),z))
        start=plant*12
        fs += [(start+j,start+(j+1)%6,start+6+(j+1)%6,start+6+j) for j in range(6)]
        fs += [tuple(start+5-j for j in range(6)),tuple(start+6+j for j in range(6))]
    data=bpy.data.meshes.new('Crop stems');data.from_pydata(vs,[],fs);data.update()
    obj=bpy.data.objects.new('Crop stems | '+bed.name.split(' | ')[0],data)
    scene.collection.objects.link(obj);obj.parent=bed;data.materials.append(bpy.data.materials['Greenhouse / Leaf green 0'])
    for p in data.polygons:p.use_smooth=True
for obj in scene.objects:
    if obj.name.startswith('Opaque pressure end cap'):
        for polygon in obj.data.polygons:polygon.flip()
        obj.data.update()
bpy.context.view_layer.update()
objects=set()
def visit(o):
    objects.add(o)
    for child in o.children:visit(child)
visit(root)
deps=bpy.context.evaluated_depsgraph_get();triangles=0;coords=[]
for obj in objects:
    if obj.type in {'MESH','CURVE'}:
        ev=obj.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();triangles+=len(me.loop_triangles)
        coords += [obj.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
lo=[min(v[i] for v in coords) for i in range(3)];hi=[max(v[i] for v in coords) for i in range(3)]
bpy.ops.object.select_all(action='DESELECT')
for obj in objects:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(assets/'buildings/greenhouse-reference-module.glb'),export_format='GLB',
    use_selection=True,use_active_scene=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False,export_extras=True)
def fit_camera(camera):
    bpy.context.view_layer.update()
    projected=[world_to_camera_view(scene,camera,p) for p in coords]
    xmin=min(p.x for p in projected);xmax=max(p.x for p in projected)
    ymin=min(p.y for p in projected);ymax=max(p.y for p in projected)
    aspect=scene.render.resolution_x/scene.render.resolution_y
    width=camera.data.ortho_scale;height=width/aspect
    rotation=camera.rotation_euler.to_matrix()
    camera.location+=rotation@Vector((((xmin+xmax)/2-.5)*width,((ymin+ymax)/2-.5)*height,0))
    camera.data.ortho_scale*=max((xmax-xmin)/.88,(ymax-ymin)/.85)
    bpy.context.view_layer.update()
camera=scene.camera;fit_camera(camera)
report=assets/'previews/greenhouse-reference-module-report.json';stats=json.loads(report.read_text())
stats.update(stage='Rendering refined greenhouse',nodes=len(objects),triangles=triangles,dimensions_meters=[round(hi[i]-lo[i],4) for i in range(3)])
stats['refinements']=['Open sill perimeter and visible walkway','Exposed planter walls','Deeper leaf greens and short stems','Outward end-cap normals','Closer centered studio framing']
report.write_text(json.dumps(stats,indent=2))
scene.render.filepath=str(assets/'previews/greenhouse-reference-module.png');bpy.ops.render.render(write_still=True)
hero_loc=camera.location.copy();hero_rot=camera.rotation_euler.copy();hero_scale=camera.data.ortho_scale
camera.location=(13,18,11.5);camera.rotation_euler=(Vector((-.5,0,2.8))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1200;scene.render.resolution_y=800;fit_camera(camera)
scene.render.filepath=str(assets/'previews/greenhouse-reference-module-rear.png');bpy.ops.render.render(write_still=True)
camera.location=hero_loc;camera.rotation_euler=hero_rot;camera.data.ortho_scale=hero_scale
scene.render.resolution_x=1536;scene.render.resolution_y=1024;scene.render.filepath=str(assets/'previews/greenhouse-reference-module.png')
bpy.ops.wm.save_as_mainfile(filepath=str(assets/'source/greenhouse-reference-module.blend'))
stats['stage']='Complete';report.write_text(json.dumps(stats,indent=2))
