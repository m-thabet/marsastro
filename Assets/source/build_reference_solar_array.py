"""Editable two-bank, eight-panel solar module from the user's reference.

All geometry and portable PBR materials are procedural. Each bank has its own
tilt pivot. Creates a dedicated scene and preserves prior output filenames.
"""
import bpy
import math
import random
import json
import time
import traceback
from pathlib import Path
from mathutils import Vector

ASSETS=Path(__file__).resolve().parents[1]
STEM='solar-array-reference-module'
SOURCE=ASSETS/'source'/(STEM+'.blend')
MODEL=ASSETS/'buildings'/(STEM+'.glb')
PREVIEW=ASSETS/'previews'/(STEM+'.png')
BACK=ASSETS/'previews'/(STEM+'-rear.png')
REPORT=ASSETS/'previews'/(STEM+'-report.json')
for folder in (SOURCE.parent,MODEL.parent,PREVIEW.parent):folder.mkdir(parents=True,exist_ok=True)
START=time.time();random.seed(2511)

def status(stage,**data):
    REPORT.write_text(json.dumps(dict(stage=stage,elapsed_seconds=round(time.time()-START,2),**data),indent=2))

def mat(name,color,metal=.15,rough=.43,emission=0):
    m=bpy.data.materials.new('Solar Module / '+name);m.use_nodes=True;m.diffuse_color=(*color,1)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    p.inputs['Coat Weight'].default_value=.12
    if emission:
        p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    return m

def group(name,parent=None,loc=(0,0,0)):
    o=bpy.data.objects.new(name,None);scene.collection.objects.link(o);o.parent=parent;o.location=loc;return o

def mesh(name,verts,faces,material,parent,smooth=False):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.parent=parent
    if material:data.materials.append(material)
    if smooth:
        for p in data.polygons:p.use_smooth=True
    return o

def box(name,loc,size,material,parent,bevel=.04,rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.name=name;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        b=o.modifiers.new('Rounded manufactured edges','BEVEL');b.width=bevel;b.segments=3
        o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    o.rotation_euler=rotation;o.parent=parent;o.data.materials.append(material);return o

def cylinder(name,loc,r,depth,material,parent,rotation=(0,0,0),segments=40):
    bpy.ops.mesh.primitive_cylinder_add(vertices=segments,radius=r,depth=depth,location=loc)
    o=bpy.context.object;o.name=name;o.rotation_euler=rotation;o.parent=parent;o.data.materials.append(material)
    bevel=o.modifiers.new('Machined edge radius','BEVEL');bevel.width=min(.018,depth*.15);bevel.segments=2
    o.modifiers.new('Weighted circular normals','WEIGHTED_NORMAL')
    for p in o.data.polygons:p.use_smooth=True
    return o

def beam(name,a,b,width,depth,material,parent):
    a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(width,depth,(b-a).length),material,parent,.035)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def line(name,points,r,material,parent):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=r;data.bevel_resolution=2
    s=data.splines.new('POLY');s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.parent=parent;data.materials.append(material);return o

def chamfer_outline(rx,ry,c):
    return [(-rx+c,-ry),(rx-c,-ry),(rx,-ry+c),(rx,ry-c),(rx-c,ry),(-rx+c,ry),(-rx,ry-c),(-rx,-ry+c)]

def solid_polygon(name,outline,z0,z1,material,parent,bevel=.015):
    area=sum(outline[i][0]*outline[(i+1)%len(outline)][1]-outline[(i+1)%len(outline)][0]*outline[i][1] for i in range(len(outline)))
    if area<0:outline=list(reversed(outline))
    n=len(outline);vs=[(x,y,z) for z in (z0,z1) for x,y in outline]
    fs=[tuple(reversed(range(n))),tuple(n+i for i in range(n))]
    fs += [(i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n)]
    o=mesh(name,vs,fs,material,parent)
    if bevel:
        b=o.modifiers.new('Precision edge chamfer','BEVEL');b.width=bevel;b.segments=2
        o.modifiers.new('Weighted plate normals','WEIGHTED_NORMAL')
    return o

def profile_body(name,profiles,material,parent):
    vs=[]
    for z,rx,ry,c in profiles:vs.extend([(x,y,z) for x,y in chamfer_outline(rx,ry,c)])
    fs=[(j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i) for j in range(len(profiles)-1) for i in range(8)]
    fs += [tuple(reversed(range(8))),tuple((len(profiles)-1)*8+i for i in range(8))]
    o=mesh(name,vs,fs,material,parent)
    b=o.modifiers.new('Soft casing edges','BEVEL');b.width=.045;b.segments=3
    o.modifiers.new('Casing weighted normals','WEIGHTED_NORMAL');return o

def bolt(name,x,y,z,parent):
    cylinder(name,(x,y,z),.035,.025,metal,parent,segments=12)
    box('Bolt driver slot',(x,y,z+.014),(.032,.009,.005),dark,parent,.002)

def panel(label,parent,loc):
    module=group(label,parent,loc)
    solid_polygon('Panel graphite backing',chamfer_outline(1.065,1.065,.135),-.10,.075,dark,module,.018)
    # A four-sided ring with raised ivory outer edges and recessed inner glass.
    profiles=[(1.053,.13,.062),(1.053,.13,.13),(.985,.105,.145),(.973,.098,.115)]
    vs=[]
    for radius,chamfer,z in profiles:vs.extend([(x,y,z) for x,y in chamfer_outline(radius,radius,chamfer)])
    fs=[(j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i) for j in range(len(profiles)-1) for i in range(8)]
    rim=mesh('Panel raised ivory perimeter',vs,fs,ivory,module)
    b=rim.modifiers.new('Soft panel perimeter','BEVEL');b.width=.009;b.segments=2
    rim.modifiers.new('Frame weighted normals','WEIGHTED_NORMAL')
    solid_polygon('Blue laminated cell substrate',chamfer_outline(.973,.973,.10),.080,.117,pv[0],module,.008)
    # Cell faces and silver grid are explicit meshes, with no texture dependency.
    verts=[];faces=[];count=8;span=1.87;pitch=span/count
    for row in range(count):
        for col in range(count):
            x=-span/2+col*pitch;y=-span/2+row*pitch;gap=.004
            start=len(verts)
            verts += [(x+gap,y+gap,.119),(x+pitch-gap,y+gap,.119),(x+pitch-gap,y+pitch-gap,.119),(x+gap,y+pitch-gap,.119)]
            faces.append((start,start+1,start+2,start+3))
    cells=mesh('Photovoltaic cells | 8 by 8 grid',verts,faces,pv[0],module)
    for material in pv[1:]:cells.data.materials.append(material)
    for p in cells.data.polygons:p.material_index=random.choices(range(len(pv)),[5,2,2,1])[0]
    verts=[];faces=[]
    def rectangle(x0,y0,x1,y1):
        start=len(verts);verts.extend([(x0,y0,.121),(x1,y0,.121),(x1,y1,.121),(x0,y1,.121)])
        faces.append((start,start+1,start+2,start+3))
    for i in range(1,count):
        d=-span/2+i*pitch
        rectangle(d-.0022,-span/2,d+.0022,span/2)
        rectangle(-span/2,d-.0022,span/2,d+.0022)
    mesh('Fine photovoltaic silver traces',verts,faces,grid,module)
    # Orange opposite-corner clamps match the clipped frame corners.
    outline=[(.77,1.073),(.963,1.073),(1.073,.963),(1.073,.77),(.992,.77),(.992,.922),(.922,.992),(.77,.992)]
    for sx,sy in [(-1,1),(1,-1)]:
        solid_polygon('Orange frame corner protector',[(sx*x,sy*y) for x,y in outline],.113,.177,orange,module,.013)
    # Rear frame rails and small electrical junctions remain editable.
    for x in (-.64,.64):box('Panel rear reinforcing rail',(x,0,-.13),(.105,1.90,.11),metal,module,.022)
    box('Panel rear cable junction',(0,-.43,-.19),(.33,.32,.12),trim,module,.035)
    line('Panel rear power lead',[(0,-.43,-.25),(.24,-.25,-.26),(.29,.50,-.25)],.018,dark,module)
    return module

try:
    if SOURCE.exists() or MODEL.exists():raise FileExistsError('Choose a fresh stem to preserve the existing solar array.')
    scene=bpy.data.scenes.new('Solar / Reference Twin Array');bpy.context.window.scene=scene;scene.unit_settings.system='METRIC'
    root=group('SolarArray | reference twin-bank module')
    foundations=group('Bases | connected ivory foundation decks',root)
    supports=group('Supports | fixed A-frames hinges and actuators',root)
    controller=group('Control | pedestal antenna and service hatch',root,(0,-.18,0))
    ivory=mat('Warm ivory frame',(.79,.72,.62),.19,.38)
    edge=mat('Light ceramic edges',(.91,.84,.73),.12,.36)
    orange=mat('Amber orange safety enamel',(.98,.235,.007),.17,.35)
    dark=mat('Graphite seals and cables',(.024,.029,.035),.23,.49)
    trim=mat('Charcoal equipment casing',(.085,.089,.096),.30,.43)
    metal=mat('Brushed warm steel',(.28,.285,.29),.68,.34)
    grid=mat('Fine silver solar traces',(.28,.32,.39),.52,.46)
    light=mat('Warm recessed status lights',(1,.67,.27),.08,.28,2.0)
    pv=[mat('Photovoltaic navy variation %d'%i,c,.34,.32) for i,c in enumerate([
        (.017,.026,.050),(.019,.028,.054),(.014,.023,.046),(.021,.030,.056)])]

    status('Building connected bases and central control pedestal')
    for label,cx in [('Left',-3.30),('Right',3.30)]:
        base=group(label+' base | service deck and corner feet',foundations,(cx,0,0))
        box('Base graphite underframe',(0,0,.235),(5.42,4.30,.36),dark,base,.19)
        box('Base ivory perimeter deck',(0,0,.47),(5.30,4.20,.26),ivory,base,.18)
        for y in (-1.11,.84):
            box('Inset dark service-deck gasket',(0,y,.615),(2.90,.80,.055),dark,base,.07)
            box('Flush graphite access plate',(0,y,.65),(2.76,.67,.035),metal,base,.055)
        for x in (-2.43,2.43):
            for y in (-1.94,1.94):
                box('Corner landing shoe',(x,y,.32),(.65,.66,.57),trim,base,.14)
                box('Corner ivory top cap',(x,y,.63),(.58,.60,.12),edge,base,.08)
                if y<0:
                    box('Foot orange lamp recess',(x,y-.337,.34),(.43,.04,.19),orange,base,.05)
                    box('Foot warm running light',(x,y-.365,.35),(.33,.025,.095),light,base,.035)
        for side in (-1,1):
            y=side*2.135
            box('Base recessed carry-handle housing',(0,y,.34),(1.18,.11,.20),trim,base,.075)
            box('Base dark carry-handle slot',(0,y+side*.064,.36),(.77,.025,.065),dark,base,.022)
        # Visible short-end access slot.
        x=-2.72 if cx<0 else 2.72
        box('End base service vent',(x,0,.32),(.08,1.37,.20),trim,base,.055)
    profile_body('Center graphite linking foundation',[(.06,1.27,1.72,.24),(.31,1.34,1.77,.25),(.52,1.24,1.67,.24)],trim,foundations)
    profile_body('Center ivory linking deck',[(.36,1.31,1.73,.24),(.60,1.22,1.63,.24)],ivory,foundations)
    box('Center front orange identification stripe',(0,-1.715,.49),(.83,.065,.15),orange,foundations,.035)
    profile_body('Controller charcoal plinth',[(.58,.89,.75,.15),(.76,.87,.73,.15)],trim,controller)
    profile_body('Tapered cream controller casing',[(.72,.82,.69,.13),(.94,.80,.67,.13),(1.77,.66,.58,.11)],ivory,controller)
    profile_body('Controller dark status band',[(1.77,.67,.59,.10),(1.96,.72,.62,.11)],trim,controller)
    profile_body('Controller ivory roof cap',[(1.96,.78,.68,.13),(2.15,.71,.61,.12),(2.22,.57,.49,.10)],edge,controller)
    box('Controller orange service-door gasket',(0,-.699,1.22),(.42,.075,.85),trim,controller,.065)
    box('Controller orange service-door insert',(0,-.749,1.23),(.255,.045,.66),orange,controller,.038)
    box('Controller upper lamp recess',(0,-.637,1.87),(.75,.07,.125),dark,controller,.045)
    box('Controller warm status strip',(0,-.682,1.88),(.61,.03,.055),light,controller,.023)
    box('Controller top inspection plate',(.26,0,2.225),(.31,.34,.043),trim,controller,.055)
    cylinder('Controller antenna mounting collar',(-.36,.10,2.27),.090,.15,metal,controller)
    cylinder('Controller antenna lower sleeve',(-.36,.10,2.43),.047,.24,trim,controller)
    cylinder('Controller antenna mast',(-.36,.10,3.02),.025,.98,dark,controller,segments=24)
    cylinder('Controller ivory antenna tip',(-.36,.10,3.55),.031,.16,edge,controller,segments=24)

    status('Building A-frame supports and hinged eight-panel banks')
    banks=[]
    for label,cx in [('Left',-3.30),('Right',3.30)]:
        fixed=group(label+' support | triangulated fixed frame',supports,(cx,0,0))
        for x in (-1.69,1.69):
            for y in (-1.49,1.49):
                box('A-frame bolted mounting plate',(x,y,.665),(.60,.62,.15),metal,fixed,.055)
                for dx,dy in [(-.21,-.20),(.21,-.20),(-.21,.20),(.21,.20)]:bolt('Mounting plate hex bolt',x+dx,y+dy,.754,fixed)
            beam('A-frame front ivory strut',(x,-1.49,.73),(x,0,2.67),.34,.43,ivory,fixed)
            beam('A-frame rear ivory strut',(x,1.49,.73),(x,0,2.67),.29,.36,ivory,fixed)
            beam('A-frame graphite inner brace',(x,-1.20,.82),(x,.96,1.22),.15,.17,trim,fixed)
            # Orange safety flashes sit on the outward sides of the front struts.
            sx=-1 if x<0 else 1
            beam('Orange leg safety inset',(x+sx*.179,-1.23,1.04),(x+sx*.179,-.91,1.46),.026,.32,orange,fixed)
            cylinder('Support pivot housing',(x,0,2.66),.25,.47,trim,fixed,(0,math.pi/2,0))
        box('Low support crossbeam',(0,.94,.83),(3.72,.16,.20),trim,fixed,.045)
        box('High support crossbeam',(0,0,2.58),(4.33,.22,.22),dark,fixed,.04)
        cylinder('Bank continuous hinge shaft',(0,0,2.70),.095,4.62,metal,fixed,(0,math.pi/2,0))
        for sx in (-1,1):
            cylinder('Hinge graphite end hub',(sx*2.29,0,2.70),.248,.20,dark,fixed,(0,math.pi/2,0))
            cylinder('Hinge ivory machined cover',(sx*2.36,0,2.70),.206,.13,ivory,fixed,(0,math.pi/2,0))
            cylinder('Hinge orange center cap',(sx*2.44,0,2.70),.123,.034,orange,fixed,(0,math.pi/2,0))
            cylinder('Hinge center steel pin',(sx*2.463,0,2.70),.066,.025,metal,fixed,(0,math.pi/2,0),24)
        bank=group(label+' bank | adjustable panel hinge pivot',root,(cx,0,2.70))
        bank.rotation_euler.x=math.radians(30);bank['tilt_degrees']=30
        bank['editing_note']='Rotate local X about the central hinge to adjust bank tilt'
        banks.append(bank)
        for row in range(2):
            for col in range(2):
                panel(label+' panel %d%d | framed photovoltaic module'%(row+1,col+1),bank,((-1 if col==0 else 1)*1.10,(-1 if row==0 else 1)*1.10,0))
        for x in (-1.10,1.10):
            cylinder('Inner row-joining hinge barrel',(x,0,-.015),.14,.25,ivory,bank,(0,math.pi/2,0))
        box('Bank rear hinge spine',(0,0,-.18),(4.28,.17,.18),trim,bank,.035)
        # Flexible power loop from the stationary frame into the central controller.
        inner=-1 if cx>0 else 1
        line('Bank flexible power conduit',[(inner*1.72,.34,2.49),(inner*2.02,.40,2.17),
            (inner*2.23,.40,1.48),(inner*2.40,.38,.88)],.032,dark,fixed)
    for sx in (-1,1):
        line('Controller buried-deck cable',[(sx*.82,.18,.77),(sx*1.33,.19,.73),(sx*1.62,.27,.74)],.039,dark,controller)

    root['reference']='User-supplied twin four-panel navy/ivory/orange solar array image'
    root['scope']='Stylized exterior equipment model; two banks with eight framed panels and central controller'
    root['units']='Meters; illustrative asset dimensions rather than rated power or certified engineering geometry'
    bpy.context.view_layer.update()
    status('Lighting neutral studio and exporting the solar module')
    floor=mat('Neutral studio floor',(.47,.445,.44),0,.87)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.015))
    ground=bpy.context.object;ground.name='Studio floor | excluded from GLB';ground.data.materials.append(floor)
    world=bpy.data.worlds.new('Solar / neutral studio');world.use_nodes=True;scene.world=world
    bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.65,.63,.65,1);bg.inputs[1].default_value=.36
    bpy.ops.object.light_add(type='AREA',location=(-7,-10,13));key=bpy.context.object;key.name='Large warm solar-module softbox'
    key.data.energy=2300;key.data.shape='DISK';key.data.size=7;key.data.color=(1,.89,.78)
    key.rotation_euler=(Vector((0,0,1.3))-key.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.light_add(type='AREA',location=(6,-2,10));fill=bpy.context.object;fill.name='Broad cool solar-module fill'
    fill.data.energy=1550;fill.data.size=10;fill.data.color=(.80,.88,1)
    fill.rotation_euler=(Vector((0,0,1.3))-fill.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.light_add(type='SUN',location=(-10,-10,20));sun=bpy.context.object;sun.name='Soft solar-module studio sun'
    sun.data.energy=1.3;sun.data.angle=math.radians(9);sun.data.color=(1,.91,.80)
    sun.rotation_euler=(math.radians(24),math.radians(-28),math.radians(-30))
    bpy.ops.object.camera_add(location=(-8,-16,10));camera=bpy.context.object;camera.name='Solar array reference hero camera'
    target=Vector((0,-.1,1.60));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=14.6;scene.camera=camera
    scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
    scene.render.resolution_x=1536;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.filepath=str(PREVIEW)
    scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.18
    try:scene.view_settings.look='AgX - Medium High Contrast'
    except TypeError:pass
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
    objects=set()
    def visit(obj):
        objects.add(obj)
        for child in obj.children:visit(child)
    visit(root);bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(MODEL),export_format='GLB',use_selection=True,use_active_scene=True,
        export_apply=True,export_yup=True,export_cameras=False,export_lights=False,export_extras=True)
    deps=bpy.context.evaluated_depsgraph_get();triangles=0;coords=[]
    for obj in objects:
        if obj.type in {'MESH','CURVE'}:
            ev=obj.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();triangles+=len(me.loop_triangles)
            coords += [obj.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
    lo=[min(p[i] for p in coords) for i in range(3)];hi=[max(p[i] for p in coords) for i in range(3)]
    stats=dict(source=str(SOURCE),model=str(MODEL),preview=str(PREVIEW),rear_preview=str(BACK),
        nodes=len(objects),triangles=triangles,dimensions_meters=[round(hi[i]-lo[i],4) for i in range(3)],
        panels=8,cells_per_panel=64,bank_tilt_degrees=30,units='meters',gltf_up_axis='Y',
        animation_clips=[],external_assets=[],material_type='Portable PBR colors and geometric cell grids; no image textures',
        scope='Editable stylized twin-bank solar module based on the user-provided reference')
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
    status('Rendering front three-quarter preview',**stats);bpy.ops.render.render(write_still=True)
    loc=camera.location.copy();rot=camera.rotation_euler.copy()
    camera.location=(9,15,10);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.filepath=str(BACK)
    status('Rendering rear equipment preview',**stats);bpy.ops.render.render(write_still=True)
    camera.location=loc;camera.rotation_euler=rot;scene.render.resolution_x=1536;scene.render.resolution_y=1024
    scene.render.filepath=str(PREVIEW);bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
    status('Complete',**stats)
except Exception:
    status('Failed',traceback=traceback.format_exc())
    raise
