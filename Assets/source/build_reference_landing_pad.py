"""Industrial circular landing platform from the user-supplied reference.

Segmented metal deck, orange guidance rings, perimeter hardware, four amber
beacons, ventilation grilles, and an access ramp. No external assets required.
"""
import bpy
import bmesh
import math
import random
import json
import time
import traceback
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ASSETS=Path(__file__).resolve().parents[1]
STEM='landing-pad-reference-module'
SOURCE=ASSETS/'source'/(STEM+'.blend')
MODEL=ASSETS/'buildings'/(STEM+'.glb')
PREVIEW=ASSETS/'previews'/(STEM+'.png')
TOP=ASSETS/'previews'/(STEM+'-top.png')
REPORT=ASSETS/'previews'/(STEM+'-report.json')
for folder in (SOURCE.parent,MODEL.parent,PREVIEW.parent):folder.mkdir(parents=True,exist_ok=True)
START=time.time();random.seed(9117)

def status(stage,**data):
    REPORT.write_text(json.dumps(dict(stage=stage,elapsed_seconds=round(time.time()-START,2),**data),indent=2))

def mat(name,color,metal=.25,rough=.52,emission=0):
    m=bpy.data.materials.new('Landing Pad / '+name);m.use_nodes=True;m.diffuse_color=(*color,1)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    p.inputs['Coat Weight'].default_value=.08
    if emission:
        p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    return m

def group(name,parent=None,loc=(0,0,0)):
    o=bpy.data.objects.new(name,None);scene.collection.objects.link(o);o.parent=parent;o.location=loc;return o

def mesh(name,verts,faces,material,parent,closed=False):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    if closed:
        bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.parent=parent
    if material:data.materials.append(material)
    return o

def bevel(obj,width=.025,segments=2):
    b=obj.modifiers.new('Manufactured edge radii','BEVEL');b.width=width;b.segments=segments
    obj.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL');return obj

def box(name,loc,size,material,parent,r=.04,rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if r:bevel(o,r,3)
    o.rotation_euler=rotation;o.parent=parent;o.data.materials.append(material);return o

def cylinder(name,loc,r,depth,material,parent,segments=96):
    bpy.ops.mesh.primitive_cylinder_add(vertices=segments,radius=r,depth=depth,location=loc)
    o=bpy.context.object;o.name=name;o.parent=parent;o.data.materials.append(material)
    bevel(o,min(.025,depth*.15),2)
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    return o

def outline(rx,ry,c):
    return [(-rx+c,-ry),(rx-c,-ry),(rx,-ry+c),(rx,ry-c),(rx-c,ry),(-rx+c,ry),(-rx,ry-c),(-rx,-ry+c)]

def casing(name,profiles,material,parent):
    vs=[]
    for z,rx,ry,c in profiles:vs.extend([(x,y,z) for x,y in outline(rx,ry,c)])
    fs=[(j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i) for j in range(len(profiles)-1) for i in range(8)]
    fs += [tuple(reversed(range(8))),tuple((len(profiles)-1)*8+i for i in range(8))]
    return bevel(mesh(name,vs,fs,material,parent,True),.035,3)

def lathe(name,profile,material,parent,segments=160):
    vs=[(r*math.cos(i*math.tau/segments),r*math.sin(i*math.tau/segments),z) for r,z in profile for i in range(segments)]
    fs=[(j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i)
        for j in range(len(profile)-1) for i in range(segments)]
    fs += [tuple(reversed(range(segments))),tuple((len(profile)-1)*segments+i for i in range(segments))]
    return bevel(mesh(name,vs,fs,material,parent,True),.028,2)

def wedge_geometry(r0,r1,a0,a1,z0,z1,steps=16):
    angles=[a0+(a1-a0)*i/steps for i in range(steps+1)];n=len(angles)
    vs=[(r*math.cos(a),r*math.sin(a),z) for z in (z0,z1) for r in (r0,r1) for a in angles]
    fs=[]
    for i in range(n-1):
        fs.extend([(i,i+1,n+i+1,n+i),(2*n+i,3*n+i,3*n+i+1,2*n+i+1),
            (i,2*n+i,2*n+i+1,i+1),(n+i,n+i+1,3*n+i+1,3*n+i)])
    fs += [(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)]
    return vs,fs

def wedge(name,r0,r1,a0,a1,z0,z1,material,parent):
    vs,fs=wedge_geometry(r0,r1,a0,a1,z0,z1)
    return bevel(mesh(name,vs,fs,material,parent,True),.009,2)

def segmented_ring(name,r0,r1,z,segments,gap,material,parent):
    vs=[];fs=[]
    for i in range(segments):
        a0=i*math.tau/segments+gap;a1=(i+1)*math.tau/segments-gap
        verts,faces=wedge_geometry(r0,r1,a0,a1,z-.012,z,8)
        start=len(vs);vs.extend(verts);fs.extend([tuple(start+j for j in f) for f in faces])
    return bevel(mesh(name,vs,fs,material,parent,True),.003,2)

def armor_sector(name,theta,parent):
    profile=[(6.10,.77),(6.23,1.045),(6.70,1.075),(6.94,.77),(6.88,.48),(6.48,.43),(6.16,.56)]
    steps=18;N=len(profile);vs=[]
    for i in range(steps+1):
        a=theta-.125+.25*i/steps
        vs += [(r*math.cos(a),r*math.sin(a),z) for r,z in profile]
    fs=[(i*N+j,(i+1)*N+j,(i+1)*N+(j+1)%N,i*N+(j+1)%N) for i in range(steps) for j in range(N)]
    fs += [tuple(reversed(range(N))),tuple(steps*N+j for j in range(N))]
    return bevel(mesh(name,vs,fs,ivory,parent,True),.035,2)

def ramp_height(y):return .12+(y+9.55)/3.37*.70

def ramp_wedge(name,rx,y0,y1,c,zoffset,material,parent):
    pts=[(x,y+(y0+y1)/2) for x,y in outline(rx,(y1-y0)/2,c)]
    vs=[(x,y,.035) for x,y in pts]+[(x,y,ramp_height(y)+zoffset) for x,y in pts]
    n=len(pts);fs=[tuple(reversed(range(n))),tuple(n+i for i in range(n))]
    fs += [(i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n)]
    return bevel(mesh(name,vs,fs,material,parent,True),.035,3)

try:
    if SOURCE.exists() or MODEL.exists():raise FileExistsError('Choose a fresh output stem to preserve the existing landing pad.')
    scene=bpy.data.scenes.new('Landing Pad / Reference Circular Platform');bpy.context.window.scene=scene;scene.unit_settings.system='METRIC'
    root=group('LandingPad | reference circular platform')
    deck=group('Deck | segmented circular load surface',root)
    markings=group('Guides | segmented orange concentric rings',root)
    perimeter=group('Perimeter | armored modules and recessed lamps',root)
    vents=group('Ventilation | four deck grilles and rim slots',root)
    beacons=group('Beacons | four amber perimeter markers',root)
    ramp=group('Ramp | sloped access deck and guide rails',root)
    hardware=group('Hardware | batched fasteners and subtle deck wear',root)
    ivory=mat('Warm ivory armor',(.77,.68,.57),.22,.43)
    edge=mat('Light ivory straps',(.88,.78,.66),.18,.41)
    dark=mat('Graphite seals',(.026,.029,.033),.25,.62)
    trim=mat('Charcoal equipment casing',(.083,.086,.093),.38,.51)
    steel=mat('Brushed warm steel',(.24,.23,.215),.62,.46)
    orange=mat('Safety orange enamel',(.97,.235,.007),.14,.46)
    lamp=mat('Warm landing-light diffuser',(1,.65,.24),.05,.29,3)
    beacon_glow=mat('Amber beacon glass',(.99,.36,.025),.07,.28,1.7)
    beacon_core=mat('Pale amber beacon core',(1,.70,.18),.02,.27,3)
    scuffmat=mat('Restrained worn deck edges',(.23,.21,.19),.42,.76)
    plates=[mat('Deck titanium variation %d'%i,c,.38,.66) for i,c in enumerate([
        (.185,.170,.157),(.198,.181,.167),(.175,.162,.153),(.205,.187,.171)])]

    status('Building the circular foundation and segmented deck')
    lathe('Lower graphite landing-platform foundation',[(6.20,.055),(6.64,.17),(6.77,.37),(6.63,.62),(6.29,.75)],trim,deck)
    cylinder('Continuous dark backing beneath deck seams',(0,0,.65),6.22,.15,dark,deck,192)
    cylinder('Central titanium inspection disk',(0,0,.763),.83,.045,plates[1],deck,96)
    segmented_ring('Center inspection-disk seam',.85,.87,.789,24,.008,steel,markings)
    for sector in range(12):
        gap=.0045 if sector%2 else .007
        a0=sector*math.tau/12+gap;a1=(sector+1)*math.tau/12-gap
        wedge('Inner deck plate %02d'%sector,.90,2.915,a0,a1,.722,.785,plates[sector%4],deck)
        for row,(r0,r1) in enumerate([(3.245,4.12),(4.145,5.045),(5.070,6.035)]):
            wedge('Outer deck plate %02d-%d'%(sector,row),r0,r1,a0,a1,.715,.783,plates[(sector+row)%4],deck)
    segmented_ring('Orange inner landing-guide ring',2.955,3.205,.795,24,.008,orange,markings)
    segmented_ring('Thin orange outer boundary ring',6.080,6.155,.789,48,.009,orange,markings)

    status('Installing perimeter armor lamps and ventilation modules')
    for i in range(16):
        if i==12:continue  # clear access opening at -Y for the ramp
        theta=i*math.tau/16
        station=group('Rim station %02d | armored perimeter module'%i,perimeter,(6.50*math.cos(theta),6.50*math.sin(theta),0))
        station.rotation_euler.z=theta-math.pi/2
        box('Station graphite impact footing',(0,.14,.26),(1.94,1.20,.44),trim,station,.12)
        if i%2==0:
            armor_sector('Curved ivory perimeter armor %02d'%i,theta,perimeter)
            box('Outer running-light dark bezel',(0,.48,.72),(1.25,.14,.30),dark,station,.065)
            box('Outer running-light warm diffuser',(0,.566,.73),(1.02,.035,.12),lamp,station,.045)
            box('Ivory module top orange marker',(0,-.11,1.09),(.62,.34,.035),orange,station,.03)
            box('Outer armor lower impact shoe',(0,.59,.20),(1.12,.38,.30),trim,station,.07)
        else:
            casing('Charcoal perimeter vent housing',[(.31,.85,.42,.12),(.69,.84,.41,.12),(.91,.76,.34,.10)],trim,station)
            box('Rim ventilation black recess',(0,.435,.59),(1.29,.045,.28),dark,station,.045)
            for j in range(11):box('Rim ventilation vertical louver',(-.55+j*.11,.469,.59),(.035,.025,.235),steel,station,.006)
            for x in (-.72,.72):box('Ivory perimeter bridge strap',(x,0,.73),(.18,.91,.40),ivory,station,.05)
            if i%4==1:box('Rim vent top orange label',(0,-.01,.929),(.47,.42,.035),orange,station,.024)
        # Warm deck-facing approach lights, set below the top of the safety rim.
        box('Inner rim lamp recess',(0,-.43,.878),(.87,.09,.145),dark,station,.04)
        box('Inner rim warm approach light',(0,-.486,.885),(.69,.025,.068),lamp,station,.025)
    for i,theta in enumerate([math.radians(a) for a in (45,135,225,315)],1):
        beacon=group('Beacon %d | amber perimeter warning light'%i,beacons,(6.43*math.cos(theta),6.43*math.sin(theta),0))
        beacon.rotation_euler.z=theta
        casing('Beacon graphite armored pedestal',[(1.02,.25,.25,.06),(1.35,.22,.22,.05),(1.43,.16,.16,.04)],trim,beacon)
        cylinder('Beacon stainless mounting collar',(0,0,1.48),.168,.13,steel,beacon,40)
        cylinder('Beacon orange lower gasket',(0,0,1.565),.153,.065,orange,beacon,40)
        cylinder('Amber warning-light envelope',(0,0,1.755),.145,.315,beacon_glow,beacon,48)
        cylinder('Pale luminous beacon center band',(0,0,1.767),.147,.205,beacon_core,beacon,48)
        cylinder('Beacon orange rounded top cap',(0,0,1.93),.148,.065,orange,beacon,48)

    status('Fitting four deck grilles and batched fasteners')
    for i,angle in enumerate((45,135,225,315),1):
        theta=math.radians(angle);grille=group('Deck grille %d | inset louver assembly'%i,vents,(4.77*math.cos(theta),4.77*math.sin(theta),0))
        grille.rotation_euler.z=theta+math.pi/2
        box('Deck grille dark recessed plate',(0,0,.795),(1.48,1.03,.035),dark,grille,.065)
        for x in (-.731,.731):box('Deck grille narrow side rim',(x,0,.818),(.035,1.00,.025),steel,grille,.008)
        for y in (-.501,.501):box('Deck grille narrow end rim',(0,y,.818),(1.45,.035,.025),steel,grille,.008)
        for j in range(24):box('Deck grille parallel ventilation slat',(-.655+j*1.31/23,0,.821),(.021,.91,.023),steel,grille,.005)
    # Rivet heads are batched into a single real mesh for a lighter export.
    vs=[];fs=[]
    for radius in (.98,2.84,3.31,5.92):
        for i in range(24):
            a=i*math.tau/24+.012;x=radius*math.cos(a);y=radius*math.sin(a);start=len(vs)
            for z in (.786,.800):
                vs += [(x+.023*math.cos(j*math.tau/6),y+.023*math.sin(j*math.tau/6),z) for j in range(6)]
            fs += [(start+j,start+(j+1)%6,start+6+(j+1)%6,start+6+j) for j in range(6)]
            fs += [tuple(start+5-j for j in range(6)),tuple(start+6+j for j in range(6))]
    mesh('Batched hexagonal deck fasteners',vs,fs,steel,hardware,True)
    # Subtle low-contrast abrasion marks, not image textures.
    vs=[];fs=[]
    for i in range(85):
        r=random.uniform(1.0,5.9)
        if 2.80<r<3.34:continue
        a=random.uniform(0,math.tau);x=r*math.cos(a);y=r*math.sin(a)
        angle=a+random.uniform(-.8,.8);length=random.uniform(.055,.22);width=.0025
        along=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-math.sin(angle),math.cos(angle),0))
        p=Vector((x,y,.7865));start=len(vs)
        vs += [tuple(p+along*dx+side*dy) for dx,dy in [(-length/2,-width),(length/2,-width),(length/2,width),(-length/2,width)]]
        fs.append((start,start+1,start+2,start+3))
    mesh('Restrained deck scuff geometry',vs,fs,scuffmat,hardware)

    status('Building the ribbed access ramp and paired foot lights')
    ramp_wedge('Ramp graphite structural wedge',1.69,-9.63,-6.15,.12,-.045,trim,ramp)
    ramp_wedge('Ramp ivory sloped deck',1.59,-9.55,-6.18,.12,0,ivory,ramp)
    slope=math.atan2(.70,3.37)
    cy=-7.865
    box('Ramp central dark anti-slip plate',(0,cy,ramp_height(cy)+.020),(2.23,3.18,.035),plates[0],ramp,.035,(slope,0,0))
    for i in range(18):
        y=-9.36+i*2.98/17
        box('Ramp transverse traction rib',(0,y,ramp_height(y)+.045),(2.17,.032,.025),steel,ramp,.006,(slope,0,0))
    for sx in (-1,1):
        box('Ramp orange edge-guidance strip',(sx*1.29,cy,ramp_height(cy)+.035),(.155,3.25,.032),orange,ramp,.018,(slope,0,0))
        a=Vector((sx*1.63,-9.51,.17));b=Vector((sx*1.63,-6.20,.86))
        rail=box('Ramp graphite side-impact rail',(a+b)/2,(.12,.12,(b-a).length),trim,ramp,.025)
        rail.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
        for y in (-9.15,-7.10):
            box('Ramp ivory rail armor tab',(sx*1.62,y,ramp_height(y)+.07),(.16,.54,.14),ivory,ramp,.035,(slope,0,0))
        y=-9.25;z=ramp_height(y)+.064
        box('Ramp foot-light metal housing',(sx*1.29,y,z),(.42,.30,.075),steel,ramp,.045,(slope,0,0))
        box('Ramp warm foot-light diffuser',(sx*1.29,y-.006,z+.047),(.29,.185,.025),lamp,ramp,.025,(slope,0,0))
    box('Ramp deck-edge threshold',(0,-6.29,.819),(3.35,.17,.10),steel,ramp,.035)
    root['reference']='User-supplied circular graphite landing platform with orange rings, ivory perimeter armor, four amber beacons and ramp'
    root['scope']='Editable stylized platform; display dimensions do not certify an aircraft load rating'
    root['beacons']=4;root['deck_grilles']=4;root['deck_sectors']=12;root['access_ramps']=1
    bpy.context.view_layer.update()

    status('Lighting the studio and exporting the platform')
    floor=mat('Neutral studio floor',(.47,.445,.44),0,.87)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.012));ground=bpy.context.object;ground.name='Studio floor | excluded from GLB';ground.data.materials.append(floor)
    world=bpy.data.worlds.new('Landing Pad / neutral studio');world.use_nodes=True;scene.world=world
    bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.65,.63,.65,1);bg.inputs[1].default_value=.35
    for name,loc,energy,size,color in [('Large warm landing-pad softbox',(-8,-10,15),2700,9,(1,.89,.78)),
        ('Broad cool landing-pad fill',(8,-1,12),1700,11,(.80,.88,1))]:
        bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.data.color=color
        o.rotation_euler=(Vector((0,0,.4))-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.light_add(type='SUN',location=(-10,-10,20));sun=bpy.context.object;sun.name='Soft landing-pad studio sun';sun.data.energy=1.2
    sun.data.angle=math.radians(9);sun.data.color=(1,.91,.80);sun.rotation_euler=(math.radians(24),math.radians(-28),math.radians(-30))
    bpy.ops.object.camera_add(location=(-8,-17,13));camera=bpy.context.object;camera.name='Landing-pad reference hero camera'
    target=Vector((0,-.7,.65));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=19;scene.camera=camera
    scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
    scene.render.resolution_x=1600;scene.render.resolution_y=900;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.filepath=str(PREVIEW);scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.18
    try:scene.view_settings.look='AgX - Medium High Contrast'
    except TypeError:pass
    comp=bpy.data.node_groups.new('Landing Pad / warm marker-light bloom','CompositorNodeTree')
    comp.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
    layers=comp.nodes.new('CompositorNodeRLayers');layers.scene=scene
    glow=comp.nodes.new('CompositorNodeGlare');glow.inputs['Type'].default_value='Fog Glow';glow.inputs['Quality'].default_value='High'
    glow.inputs['Threshold'].default_value=1.5;glow.inputs['Size'].default_value=.35;glow.inputs['Strength'].default_value=.25
    output=comp.nodes.new('NodeGroupOutput');comp.links.new(layers.outputs['Image'],glow.inputs['Image']);comp.links.new(glow.outputs['Image'],output.inputs['Image']);scene.compositing_node_group=comp
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
    objects=set()
    def visit(o):
        objects.add(o)
        for child in o.children:visit(child)
    visit(root);bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(MODEL),export_format='GLB',use_selection=True,use_active_scene=True,
        export_apply=True,export_yup=True,export_cameras=False,export_lights=False,export_extras=True)
    deps=bpy.context.evaluated_depsgraph_get();triangles=0;coords=[]
    for o in objects:
        if o.type in {'MESH','CURVE'}:
            ev=o.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();triangles+=len(me.loop_triangles)
            coords += [o.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
    lo=[min(p[i] for p in coords) for i in range(3)];hi=[max(p[i] for p in coords) for i in range(3)]
    def fit_camera():
        bpy.context.view_layer.update()
        projected=[world_to_camera_view(scene,camera,p) for p in coords]
        xmin=min(p.x for p in projected);xmax=max(p.x for p in projected);ymin=min(p.y for p in projected);ymax=max(p.y for p in projected)
        width=camera.data.ortho_scale;aspect=scene.render.resolution_x/scene.render.resolution_y;height=width/aspect
        camera.location+=camera.rotation_euler.to_matrix()@Vector((((xmin+xmax)/2-.5)*width,((ymin+ymax)/2-.5)*height,0))
        camera.data.ortho_scale*=max((xmax-xmin)/.90,(ymax-ymin)/.86);bpy.context.view_layer.update()
    fit_camera()
    stats=dict(source=str(SOURCE),model=str(MODEL),preview=str(PREVIEW),top_preview=str(TOP),nodes=len(objects),triangles=triangles,
        dimensions_meters=[round(hi[i]-lo[i],4) for i in range(3)],beacons=4,deck_grilles=4,deck_sectors=12,
        access_ramps=1,units='meters',gltf_up_axis='Y',animation_clips=[],external_assets=[],
        material_type='Portable PBR colors, emissive markers, and modeled guide rings and grilles; no image textures',
        scope='Editable stylized circular landing pad based on the user-provided reference')
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE));status('Rendering platform hero preview',**stats)
    bpy.ops.render.render(write_still=True)
    loc=camera.location.copy();rot=camera.rotation_euler.copy();scale=camera.data.ortho_scale
    camera.location=(0,-1.2,25);camera.rotation_euler=(0,0,0);camera.rotation_euler=(Vector((0,-1.2,0))-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.resolution_x=1200;scene.render.resolution_y=1200;camera.data.ortho_scale=18.0;fit_camera()
    scene.render.filepath=str(TOP);status('Rendering top layout preview',**stats);bpy.ops.render.render(write_still=True)
    camera.location=loc;camera.rotation_euler=rot;camera.data.ortho_scale=scale
    scene.render.resolution_x=1600;scene.render.resolution_y=900;scene.render.filepath=str(PREVIEW)
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE));status('Complete',**stats)
except Exception:
    status('Failed',traceback=traceback.format_exc())
    raise
