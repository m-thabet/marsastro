"""Reproducible runtime derivatives. Run with Blender --background --python this_file.
Original review masters are never modified. Geometry is illustrative, not NASA data.
"""
import bpy, math, random, json, struct
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'public/assets/models'
OUT.mkdir(parents=True, exist_ok=True)
random.seed(26)
reports = []

def clear():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def material(name, color, metal=0, emit=0):
    m = bpy.data.materials.new(name); m.diffuse_color = (*color, 1); m.use_nodes=True
    p = next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=.65
    p.inputs['Emission Color'].default_value=(*color,1); p.inputs['Emission Strength'].default_value=emit
    return m

def box(name, loc, scale, mat, bevel=.08):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.name=name
    o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('Manufactured edges','BEVEL');mod.width=bevel;mod.segments=2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.materials.append(mat);return o

def sphere(name,loc,scale,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    return o

def cylinder(name,loc,radius,depth,mat,rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=radius,depth=depth,location=loc)
    o=bpy.context.object;o.name=name;o.data.materials.append(mat)
    if rotation:o.rotation_euler=rotation
    return o

def finish_terrain_source():
    for material in bpy.data.materials:
        if not material.name.startswith('Iron oxide dust') or not material.use_nodes:continue
        nodes=material.node_tree.nodes
        shader=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
        texture=next((n for n in nodes if n.type=='TEX_IMAGE'),None)
        if not texture:continue
        vertex=nodes.new('ShaderNodeVertexColor');vertex.layer_name='RegolithColor'
        mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
        material.node_tree.links.new(vertex.outputs['Color'],mix.inputs[1])
        material.node_tree.links.new(texture.outputs['Color'],mix.inputs[2])
        material.node_tree.links.new(mix.outputs['Color'],shader.inputs['Base Color'])
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Assets/source/game-terrain.blend'),copy=True)

def consolidate_opaque(meshes,stem):
    shared={}
    for o in meshes:
        old=list(o.data.materials)
        if not old:continue
        previous=o.data.color_attributes.active_color
        values=[]
        for loop in o.data.loops:
            poly=None
            if previous:
                idx=loop.index if previous.domain=='CORNER' else loop.vertex_index
                values.append(tuple(previous.data[idx].color))
            else:values.append((1,1,1,1))
        colors=o.data.color_attributes.new(name='RuntimeTint',type='FLOAT_COLOR',domain='CORNER')
        for p in o.data.polygons:
            m=old[p.material_index]
            shader=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if m.use_nodes else None
            if not shader:continue
            rgba=tuple(shader.inputs['Base Color'].default_value)
            alpha=shader.inputs['Alpha'].default_value
            emission=shader.inputs['Emission Color'].default_value
            is_glow=max(emission[:3])>.005 and shader.inputs['Emission Strength'].default_value>.01
            if alpha<.99 or is_glow:continue
            key='metal' if shader.inputs['Metallic'].default_value>.5 else 'shell'
            if key not in shared:
                mat=material('Runtime / '+stem+' / '+key,(1,1,1),.6 if key=='metal' else .05)
                node=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
                vc=mat.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='RuntimeTint'
                mat.node_tree.links.new(vc.outputs['Color'],node.inputs['Base Color'])
                shared[key]=mat
            # Keep the exact painted colors while sharing surface materials.
            for li in p.loop_indices:
                color=values[li];colors.data[li].color=tuple(rgba[i]*color[i] for i in range(3))+(1,)
        for i,m in enumerate(old):
            shader=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if m and m.use_nodes else None
            if shader and shader.inputs['Alpha'].default_value>=.99 and not(max(shader.inputs['Emission Color'].default_value[:3])>.005 and shader.inputs['Emission Strength'].default_value>.01):
                key='metal' if shader.inputs['Metallic'].default_value>.5 else 'shell'
                o.data.materials[i]=shared[key]
        o.data.color_attributes.active_color=colors

def export(stem, ratio=1, normalize=False, target=None, merge=True):
    if stem in ('commander','shelter','lander','terrain','paths','rock','power-equipment','storage-equipment'):
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/('Assets/source/game-'+stem+'.blend')),copy=True)
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    if stem not in ('commander','terrain','paths','rock'):consolidate_opaque(meshes,stem)
    # Apply world transforms, then center and ground imported assemblies.
    if normalize:
        points=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
        lo=Vector(tuple(min(p[i] for p in points) for i in range(3)))
        hi=Vector(tuple(max(p[i] for p in points) for i in range(3)))
        shift=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
        factor=target/max(hi.x-lo.x,hi.y-lo.y) if target else 1
        for o in meshes:
            world=o.matrix_world.copy();o.parent=None;o.matrix_world=world
            o.location=(o.location-shift)*factor;o.scale*=factor
    for o in meshes:
        bpy.context.view_layer.objects.active=o
        if ratio<1 and len(o.data.polygons)>30:
            mod=o.modifiers.new('Runtime reduction','DECIMATE');mod.ratio=ratio
            bpy.ops.object.modifier_apply(modifier=mod.name)
    if not merge:
        # Consolidate the suit by material within each articulation pivot.
        for parent in [o for o in bpy.context.scene.objects if o.type=='EMPTY']:
            groups={}
            for child in list(parent.children):
                if child.type=='MESH':groups.setdefault(child.data.materials[0],[]).append(child)
            for mat,parts in groups.items():
                bpy.ops.object.select_all(action='DESELECT')
                for part in parts:part.select_set(True)
                bpy.context.view_layer.objects.active=parts[0]
                if len(parts)>1:bpy.ops.object.join()
                bpy.context.object.name=parent.name+' / '+mat.name
    if merge:
        bpy.ops.object.select_all(action='DESELECT')
        for o in meshes:o.select_set(True)
        bpy.context.view_layer.objects.active=meshes[0];bpy.ops.object.join()
        joined=bpy.context.object;joined.name=stem
        # Deduplicate slots so glTF emits one primitive per material, rather than per object.
        mats=list(joined.data.materials);unique=[];mapping={}
        for i,m in enumerate(mats):
            if m not in unique:unique.append(m)
            mapping[i]=unique.index(m)
        indices=[mapping[p.material_index] for p in joined.data.polygons]
        joined.data.materials.clear()
        for m in unique:joined.data.materials.append(m)
        for p,i in zip(joined.data.polygons,indices):p.material_index=i
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.context.scene.objects:
        if o.type=='MESH' or (not merge and o.type=='EMPTY'):o.select_set(True)
    path=OUT/(stem+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_animations=False)
    if stem=='terrain':
        # glTF exporters may reserve COLOR_0 for a material's implicit white attribute.
        # Promote the authored regolith field to the standard runtime color semantic.
        data=path.read_bytes();size=struct.unpack_from('<I',data,12)[0]
        document=json.loads(data[20:20+size])
        for mesh in document['meshes']:
            for primitive in mesh['primitives']:
                attr=primitive['attributes']
                if 'COLOR_1' in attr:attr['COLOR_0']=attr.pop('COLOR_1')
        encoded=json.dumps(document,separators=(',',':')).encode()
        encoded+=b' '*((-len(encoded))%4)
        tail=data[20+size:]
        path.write_bytes(b'glTF'+struct.pack('<II',2,20+len(encoded)+len(tail))+struct.pack('<II',len(encoded),0x4E4F534A)+encoded+tail)
    triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.context.scene.objects if o.type=='MESH')
    if stem=='terrain':finish_terrain_source()
    reports.append(dict(asset=stem,bytes=path.stat().st_size,triangles=triangles))
    print('ASSET',reports[-1],flush=True)

# Derive five detailed facilities and landing pad from existing GLBs.
for stem,source,ratio,target in [
    ('habitat','habitat',.055,14),('power','solar-array',.14,12),
    ('life-support','life-support',.10,10),('greenhouse','greenhouse',.10,14),
    ('landing-pad','landing-pad',.07,16)]:
    clear();bpy.ops.import_scene.gltf(filepath=str(ROOT/f'Assets/buildings/{source}-reference-module.glb'))
    export(stem,ratio,True,target)

# Reuse the original outpost's authored laboratory, dish, workshop and rover.
for stem,prefix,target in [('laboratory','Laboratory |',12),('communications','Communications |',8),('storage','Hangar |',10),('rover','Rover |',4)]:
    clear();bpy.ops.import_scene.gltf(filepath=str(ROOT/'Assets/world/mars-reference-outpost.glb'))
    roots=[o for o in bpy.context.scene.objects if o.name.startswith(prefix)]
    if not roots:raise RuntimeError('Missing authored assembly '+prefix)
    keep=set(roots)
    for o in roots:keep.update(o.children_recursive)
    for o in list(bpy.context.scene.objects):
        if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
    export(stem,.45,True,target)

white=material('Ceramic shell',(.78,.79,.73)); dark=material('Graphite machinery',(.075,.105,.12),.4)
orange=material('Safety ochre',(.85,.25,.055));cyan=material('Instrument cyan',(.08,.65,.68),.15,.5)
glass=material('Visor glass',(.06,.15,.18),.65);sand=material('Regolith',(.40,.20,.12))

clear()
box('Shielded pressure core',(0,0,1.5),(7,6,3),dark,.5)
sphere('Regolith shielding mound',(0,1,.5),(5.4,4.4,3.4),sand)
box('Entry structural frame',(0,-3.2,1.5),(3,.8,3),white,.2)
box('Shelter door',(0,-3.65,1.35),(2.1,.2,2.5),dark)
for x in [-1.25,1.25]:box('Amber refuge marker',(x,-3.8,1.5),(.18,.12,2.6),orange,.02)
box('StatusLight',(0,-3.8,2.8),(.8,.1,.12),cyan,.02)
for i in range(6):box('Shielding reinforcement',(-3.6+i*1.44,.6,2.15),(.2,5,1),sand)
box('Entrance ramp',(0,-4.6,.15),(3,2,.3),dark)
export('shelter')

clear()
# Editable full-body pressure suit with articulated parent pivots; game animates these pivots.
def pivot(name,loc):
    o=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(o);o.location=loc;return o
def attach(o,parent):
    bpy.context.view_layer.update()
    world=o.matrix_world.copy();o.parent=parent;o.matrix_world=world
    bpy.context.view_layer.update();return o
root=pivot('Commander',(0,0,0))
torso=box('Pressure suit torso',(0,0,1.18),(.64,.40,.66),white,.16);attach(torso,root)
attach(box('Life support backpack',(0,.29,1.23),(.48,.27,.58),dark),root)
for x in [-.24,.24]:attach(box('Harness strap',(x,-.215,1.23),(.08,.045,.5),orange,.02),root)
attach(box('Chest instrument',(0,-.25,1.25),(.27,.08,.22),dark,.035),root)
attach(box('Chest display',(0,-.3,1.28),(.18,.015,.07),cyan,.01),root)
attach(cylinder('Helmet seal',(0,0,1.55),.24,.12,dark),root)
attach(sphere('Pressure helmet',(0,0,1.82),(.33,.29,.33),white),root)
attach(sphere('Panoramic visor',(0,-.19,1.84),(.285,.16,.215),glass),root)
attach(box('Helmet light',(.29,-.08,1.9),(.09,.16,.12),cyan,.025),root)
for side,x in [('Left',-.19),('Right',.19)]:
    p=pivot(side+'Leg',(x,0,.92));attach(p,root)
    attach(box(side+' suit thigh',(x,0,.72),(.25,.30,.42),white,.09),p)
    attach(sphere(side+' knee joint',(x,-.01,.49),(.145,.16,.14),dark),p)
    attach(box(side+' shin',(x,0,.30),(.24,.29,.32),white,.07),p)
    attach(box(side+' boot',(x,-.09,.10),(.29,.48,.20),dark,.055),p)
for side,x in [('Left',-.43),('Right',.43)]:
    p=pivot(side+'Arm',(x,0,1.46));attach(p,root)
    attach(sphere(side+' shoulder',(x,0,1.42),(.18,.20,.2),orange),p)
    attach(box(side+' sleeve',(x,0,1.17),(.23,.28,.43),white,.095),p)
    attach(sphere(side+' glove',(x,-.02,.90),(.13,.15,.16),dark),p)
export('commander',merge=False)

clear()
cylinder('Descent pressure hull',(0,0,3.5),2,3.6,white)
sphere('Rounded capsule',(0,0,5.15),(2,2,1.1),white)
cylinder('Thermal base',(0,0,1.65),2.15,.35,dark)
for i in range(4):
    a=i*math.pi/2;x=math.cos(a)*2.6;y=math.sin(a)*2.6
    leg=box('Landing strut',(x,y,1.0),(.22,.22,2.6),dark);leg.rotation_euler=(math.sin(a)*.4,-math.cos(a)*.4,0)
    cylinder('Landing foot',(x*1.15,y*1.15,.15),.55,.2,dark)
    box('Service panel',(math.cos(a)*2,math.sin(a)*2,3),(.25,.6,1.3),orange)
box('Boarding door',(0,-2.02,3),(1.2,.15,2),dark)
for z in range(7):box('Boarding ladder',(0,-2.2,.4+z*.36),(1.1,.25,.08),white,.02)
export('lander')

clear()
# Sculpted bounded terrain; flat central basin for reliable walking/collision at the base.
verts=[];faces=[];N=100
for j in range(N+1):
    for i in range(N+1):
        x=(i-N/2)*3;y=(j-N/2)*3;r=math.hypot(x,y)
        h=max(0,min(1,(r-53)/45))*(5+4*math.sin(x*.055)*math.cos(y*.049)+2*math.sin(x*.16+y*.08))
        # Eroded circular crater with a raised rim outside the playable base.
        cr=math.hypot(x-83,y+45);h+=3.5*math.exp(-((cr-17)/5)**2)
        verts.append((x,y,h-.08))
for j in range(N):
    for i in range(N):
        a=j*(N+1)+i;faces.append((a,a+1,a+N+2,a+N+1))
mesh=bpy.data.meshes.new('Eroded basin');mesh.from_pydata(verts,[],faces);mesh.update()
o=bpy.data.objects.new('Illustrative Mars basin',mesh);bpy.context.scene.collection.objects.link(o)
terrain=material('Iron oxide dust',(.40,.17,.08))
mesh.materials.append(terrain)
colors=mesh.color_attributes.new(name='RegolithColor',type='FLOAT_COLOR',domain='CORNER')
for p in mesh.polygons:
    p.use_smooth=True
    for loop in p.loop_indices:
        v=mesh.vertices[mesh.loops[loop].vertex_index].co
        variation=1+.08*math.sin(v.x*.09)*math.cos(v.y*.08)+.035*math.sin(v.x*.6+v.y*.4)
        colors.data[loop].color=(.42*variation,.205*variation,.105*variation,1)
# Portable, repeatable fine-grain albedo texture; glTF multiplies it by vertex colors.
image=bpy.data.images.new('Fine regolith grain',width=256,height=256)
pixels=[]
for y in range(256):
    for x in range(256):
        grain=.82+random.random()*.18
        pixels.extend((grain,grain*.96,grain*.91,1))
image.pixels=pixels;image.pack()
uv=mesh.uv_layers.new(name='Ground UV')
for loop in mesh.loops:
    v=mesh.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(v.x/6,v.y/6)
pnode=next(n for n in terrain.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
tex=terrain.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
terrain.node_tree.links.new(tex.outputs['Color'],pnode.inputs['Base Color'])
export('terrain')
clear()
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1)
o=bpy.context.object;o.name='Wind eroded basalt'
for v in o.data.vertices:
    v.co.x*=random.uniform(.85,1.2);v.co.y*=random.uniform(.7,1.1);v.co.z*=random.uniform(.45,.75)
o.data.materials.append(sand);export('rock')

clear()
pathmat=material('Compacted regolith tracks',(.32,.135,.065))
edgemat=material('Route safety edging',(.61,.40,.21))
def path_strip(a,b,width,mat):
    dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy)
    o=box('Connected service route',((a[0]+b[0])/2,(a[1]+b[1])/2,-.02),(width,length,.08),mat,0)
    o.rotation_euler.z=-math.atan2(dx,dy)
for a,b in [((0,8),(0,-12)),((0,-12),(-10,-12)),((0,-12),(12,-12)),((0,-12),(0,-18)),((0,-12),(17,-24)),((0,8),(-7,8)),((0,8),(12,8)),((0,8),(-9,22)),((0,8),(0,13)),((-10,-12),(-21,-23)),((12,8),(29,26))]:
    path_strip(a,b,2,pathmat)
    dx=b[0]-a[0];dy=b[1]-a[1];l=math.hypot(dx,dy)
    for sign in [-1,1]:
        offset=(dy/l*1.05*sign,-dx/l*1.05*sign)
        path_strip((a[0]+offset[0],a[1]+offset[1]),(b[0]+offset[0],b[1]+offset[1]),.07,edgemat)
export('paths')

# Battery cabinets and supply equipment remain reusable facility-local modules.
clear()
for x in [-1.6,0,1.6]:
    box('Battery cabinet',(x,-3.1,.85),(1.35,.85,1.7),white,.12)
    box('Battery service door',(x,-3.56,.9),(1.1,.05,1.35),dark,.035)
    box('Battery capacity status',(x,-3.6,1.4),(.8,.035,.10),cyan,.015)
    for z in [.45,.65,.85]:box('Vent grille',(x,-3.6,z),(.85,.04,.035),white,.01)
    for xx in [-.54,.54]:box('Safety corner',(x+xx,-3.6,.85),(.08,.04,1.4),orange,.015)
export('power-equipment',.65)
clear()
for x,y,z in [(-3,-4.8,.6),(-1.7,-4.8,.6),(-2.35,-4.8,1.8),(2.6,-4.8,.55)]:
    box('Supply crate',(x,y,z),(1.1,1,1.05),white,.08)
    for xx in [-.4,.4]:box('Cargo restraint',(x+xx,y-.52,z),(.12,.06,1.04),orange,.02)
    box('Inventory panel',(x,y-.55,z),(.40,.04,.24),dark,.025)
    box('Inventory seal',(x+.1,y-.58,z+.03),(.13,.025,.07),cyan,.01)
    for xx in [-.5,.5]:
        for zz in [-.44,.44]:box('Reinforced corner',(x+xx,y-.52,z+zz),(.15,.08,.15),dark,.025)
export('storage-equipment',.65)

# Save an editable assembly catalogue of the actual runtime exports.
clear()
for i,path in enumerate(sorted(OUT.glob('*.glb'))):
    before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path))
    for o in set(bpy.data.objects)-before:
        if o.parent is None:o.location.x+=(i%5)*28;o.location.y+=(i//5)*30
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Assets/source/game-runtime-catalogue.blend'))
(OUT/'asset-report.json').write_text(json.dumps(reports,indent=2))
print('COMPLETE',sum(r['bytes'] for r in reports),flush=True)
