"""Editable upper-body robot modeled from the user's portrait reference.

Run in Blender. Uses a dedicated scene and refuses to overwrite prior output.
No downloaded assets, generated images, or external model services are needed.
"""
import bpy
import math
import json
import traceback
import time
from pathlib import Path
from mathutils import Vector

ASSETS=Path(__file__).resolve().parents[1]
STEM='nova-reference-robot-bust'
SOURCE=ASSETS/'source'/(STEM+'.blend')
MODEL=ASSETS/'characters'/(STEM+'.glb')
PREVIEW=ASSETS/'previews'/(STEM+'.png')
BACK=ASSETS/'previews'/(STEM+'-back.png')
REPORT=ASSETS/'previews'/(STEM+'-report.json')
for folder in (SOURCE.parent,MODEL.parent,PREVIEW.parent):folder.mkdir(parents=True,exist_ok=True)
START=time.time()

def status(stage,**kwargs):
    REPORT.write_text(json.dumps(dict(stage=stage,elapsed_seconds=round(time.time()-START,2),**kwargs),indent=2))

def material(name,color,metal=0,rough=.35,emission=0):
    m=bpy.data.materials.new('NOVA / '+name);m.use_nodes=True
    m.diffuse_color=(*color,1)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    if emission:
        p.inputs['Emission Color'].default_value=(*color,1)
        p.inputs['Emission Strength'].default_value=emission
    return m

def group(name,parent=None):
    o=bpy.data.objects.new(name,None);scene.collection.objects.link(o)
    o.parent=parent;return o

def assign(o,name,mat,parent,smooth=True):
    o.name=name;o.parent=parent
    if mat:o.data.materials.append(mat)
    if smooth and o.type=='MESH':
        for p in o.data.polygons:p.use_smooth=True
    return o

def mesh(name,verts,faces,mat,parent,smooth=True):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o)
    return assign(o,name,mat,parent,smooth)

def sphere(name,loc,scale,mat,parent,segments=48):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=24,location=loc)
    o=bpy.context.object;o.scale=scale
    return assign(o,name,mat,parent)

def cube(name,loc,size,mat,parent,bevel=.08,rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('Soft armor edges','BEVEL');mod.width=bevel;mod.segments=4
        o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL')
    o.rotation_euler=rotation
    return assign(o,name,mat,parent,False)

def cylinder(name,loc,r,depth,mat,parent,rotation=(0,0,0),vertices=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc)
    o=bpy.context.object;o.rotation_euler=rotation
    bevel=o.modifiers.new('Machined edge radius','BEVEL');bevel.width=min(.025,depth*.13);bevel.segments=3
    o.modifiers.new('Weighted rim normals','WEIGHTED_NORMAL')
    return assign(o,name,mat,parent)

def rod(name,a,b,r,mat,parent):
    a,b=Vector(a),Vector(b)
    o=cylinder(name,(a+b)/2,r,(b-a).length,mat,parent,vertices=32)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o

def torus(name,loc,r,tube,mat,parent,rotation=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=tube,major_segments=72,minor_segments=12,location=loc)
    o=bpy.context.object;o.rotation_euler=rotation
    return assign(o,name,mat,parent)

def line(name,points,r,mat,parent,closed=False):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D'
    data.bevel_depth=r;data.bevel_resolution=4
    s=data.splines.new('POLY');s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    s.use_cyclic_u=closed
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o)
    return assign(o,name,mat,parent)

def signpow(x,e):return math.copysign(abs(x)**e,x)

def superellipsoid(name,center,radii,exponent,mat,parent,segments=96,rings=48):
    verts=[]
    for j in range(1,rings):
        phi=-math.pi/2+math.pi*j/rings
        for i in range(segments):
            theta=math.tau*i/segments
            verts.append((center[0]+radii[0]*signpow(math.cos(phi),exponent)*signpow(math.cos(theta),exponent),
                center[1]+radii[1]*signpow(math.cos(phi),exponent)*signpow(math.sin(theta),exponent),
                center[2]+radii[2]*signpow(math.sin(phi),exponent)))
    bottom=len(verts);verts.append((center[0],center[1],center[2]-radii[2]))
    top=len(verts);verts.append((center[0],center[1],center[2]+radii[2]))
    faces=[]
    for j in range(rings-2):
        for i in range(segments):
            faces.append((j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i))
    for i in range(segments):
        faces.append((bottom,(i+1)%segments,i))
        a=(rings-2)*segments+i;b=(rings-2)*segments+(i+1)%segments
        faces.append((a,b,top))
    return mesh(name,verts,faces,mat,parent)

def squircle(t,rx,rz,n=3.5):
    return rx*signpow(math.cos(t),2/n),rz*signpow(math.sin(t),2/n)

def visor_rings(name,profiles,mat,parent):
    N=128;verts=[]
    for rx,rz,y in profiles:
        for i in range(N):
            x,z=squircle(math.tau*i/N,rx,rz)
            verts.append((x,y,z+3.8))
    faces=[(j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i) for j in range(len(profiles)-1) for i in range(N)]
    return mesh(name,verts,faces,mat,parent)

def curved_disk(name,cx,cz,rx,rz,front_y,bulge,mat,parent,n=2,segments=96,rings=12):
    verts=[(cx,front_y-bulge,cz)]
    for j in range(1,rings+1):
        r=j/rings
        for i in range(segments):
            x,z=squircle(math.tau*i/segments,rx*r,rz*r,n)
            verts.append((cx+x,front_y-bulge*(1-r*r),cz+z))
    faces=[(0,1+i,1+(i+1)%segments) for i in range(segments)]
    faces += [(1+(j-1)*segments+i,1+(j-1)*segments+(i+1)%segments,
               1+j*segments+(i+1)%segments,1+j*segments+i) for j in range(1,rings) for i in range(segments)]
    # Clockwise in X/Z faces toward the viewer on negative Y.
    return mesh(name,verts,faces,mat,parent)

def panel(name,outline,y,depth,mat,parent,bevel=.07):
    # Outline is X/Z in clockwise order as seen from the front.
    verts=[(x,y,z) for x,z in outline]+[(x,y+depth,z) for x,z in outline]
    N=len(outline)
    faces=[tuple(reversed(range(N))),tuple(N+i for i in range(N))]
    faces += [(i,(i+1)%N,N+(i+1)%N,N+i) for i in range(N)]
    o=mesh(name,verts,faces,mat,parent,False)
    mod=o.modifiers.new('Rounded panel perimeter','BEVEL');mod.width=bevel;mod.segments=5
    o.modifiers.new('Panel weighted normals','WEIGHTED_NORMAL')
    return o

def helmet_y(x,z):
    n=2/.72
    return -.95*max(.0001,1-abs(x/1.73)**n-abs((z-3.8)/1.48)**n)**(1/n)

def crown_patch(name,rx,rz,cz,offset,mat):
    verts=[(0,helmet_y(0,cz)-offset,cz)];N=96;R=8
    for j in range(1,R+1):
        for i in range(N):
            x,z=squircle(i*math.tau/N,rx*j/R,rz*j/R,4)
            z+=cz;verts.append((x,helmet_y(x,z)-offset,z))
    fs=[(0,1+i,1+(i+1)%N) for i in range(N)]
    fs += [(1+(j-1)*N+i,1+(j-1)*N+(i+1)%N,1+j*N+(i+1)%N,1+j*N+i) for j in range(1,R) for i in range(N)]
    return mesh(name,verts,fs,mat,head)

try:
    if SOURCE.exists() or MODEL.exists():raise FileExistsError('Choose a new STEM to preserve the existing robot.')
    status('Creating robot materials and dedicated scene')
    scene=bpy.data.scenes.new('NOVA / Reference Robot Bust');bpy.context.window.scene=scene
    scene.unit_settings.system='METRIC'
    root=group('NOVA | reference robot bust')
    head=group('Head | ceramic helmet and display',root)
    face=group('Face | modeled eyes brows and smile',head)
    neck=group('Neck | articulated bellows',root)
    torso=group('Torso | segmented ceramic armor',root)
    arms=group('Arms | shoulders and upper forearms',root)
    cream=material('Pearl warm ceramic',(.83,.70,.60),.22,.25)
    creamlight=material('Ivory edge trim',(.94,.84,.70),.28,.22)
    sage=material('Olive green armor accents',(.36,.48,.12),.28,.27)
    darkgreen=material('Olive inset gasket',(.13,.19,.045),.25,.35)
    graphite=material('Graphite flexible joints',(.035,.035,.045),.2,.38)
    steel=material('Soft gunmetal',(.22,.21,.235),.72,.28)
    seam=material('Warm recessed shell seams',(.36,.28,.24),.2,.45)
    navy=material('Midnight blue glossy face',(.012,.021,.045),.35,.16)
    eyeseal=material('Eye socket navy',(.003,.006,.012),.1,.23)
    white=material('Pearlescent eye surround',(.90,.88,.91),.15,.22)
    pupil=material('Obsidian pupils',(.0015,.005,.008),.2,.13)
    iris=material('Turquoise iris',(.02,.50,.39),.35,.22)
    glow=material('Mint status lights',(.22,1,.45),.1,.25,2.4)
    smile=material('Mint smile',(.28,1,.69),.1,.26,1.6)
    brow=material('Lavender expressive eyebrows',(.40,.40,.61),.15,.3,.15)
    highlight=material('Eye catchlights',(.98,1,1),.05,.18,.7)

    status('Modeling rounded helmet and curved faceplate')
    superellipsoid('Helmet full back and side shell',(0,0,3.8),(1.73,.95,1.48),.72,cream,head)
    visor_rings('Thick ceramic face-opening rim',[(1.72,1.39,-.48),(1.67,1.34,-.73),
        (1.59,1.26,-.94),(1.50,1.17,-1.005)],creamlight,head)
    visor_rings('Graphite visor perimeter gasket',[(1.51,1.185,-1.004),(1.47,1.145,-1.038)],graphite,head)
    curved_disk('Convex midnight face display',0,3.8,1.475,1.15,-1.043,.145,navy,face,n=3.5)
    # The face has thickness and a closed back; it is not an image plane.
    visor_rings('Visor side return',[(1.475,1.15,-1.043),(1.475,1.15,-.96)],navy,face)
    crown_patch('Crown green inset border',.36,.245,5.025,.025,darkgreen)
    crown_patch('Rounded olive crown panel',.325,.223,5.025,.041,sage)

    for sx in (-1,1):
        x=.83*sx;pts=[]
        for k in range(40):
            z=4.82+k*.37/39
            xx=x*(1-.23*k/39)
            pts.append((xx,helmet_y(xx,z)-.008,z))
        line('Upper ceramic longitudinal panel seam',pts,.008,seam,head)
    pts=[]
    for i in range(90):
        x=-1.45+2.9*i/89;z=4.72+.06*(1-(x/1.45)**2)
        pts.append((x,helmet_y(x,z)-.008,z))
    line('Upper brow shell panel joint',pts,.009,seam,head)
    for sx in (-1,1):
        # Rear vertical panel seams and flush service bolts.
        line('Rear helmet panel joint',[(sx*.87,.82,2.95),(sx*.96,.88,3.8),(sx*.83,.78,4.72)],.012,seam,head)
        for z in (3.0,4.65):sphere('Flush helmet fastener',(sx*1.35,-.68,z),(.032,.016,.032),steel,head,24)
    cube('Central chin impact plate',(0,-.84,2.47),(.95,.22,.21),steel,head,.085)
    for sx in (-1,1):cube('Side chin graphite bumper',(sx*1.02,-.73,2.60),(.55,.18,.19),steel,head,.075,(0,sx*.35,0))
    # Properly modeled rear service cover makes the asset useful beyond this portrait angle.
    superellipsoid('Rear service hatch',(0,.87,3.67),(.86,.12,.83),.6,creamlight,head,64,32)
    cube('Rear olive service badge',(0,1.004,4.12),(.68,.06,.28),sage,head,.11)
    for i in range(5):cube('Rear cooling vent',(0,1.014,3.25+i*.13),(.65,.035,.045),steel,head,.02)

    status('Modeling concentric ear modules and antennas')
    for sx,label in [(-1,'Left'),(1,'Right')]:
        ear=group(label+' ear | concentric audio module',head)
        rot=(0,math.pi/2,0)
        for name,x,r,d,mat in [('Ear inner flexible joint',1.77,.66,.28,graphite),
            ('Ear machined housing',1.94,.63,.23,steel),('Ear cream bezel',2.095,.565,.16,cream),
            ('Ear recessed olive center',2.185,.405,.035,sage)]:
            cylinder(label+' '+name,(sx*x,.0,3.8),r,d,mat,ear,rot)
        torus(label+' ear luminous status ring',(sx*2.205,0,3.8),.45,.035,glow,ear,rot)
        torus(label+' ear inset metallic rim',(sx*2.215,0,3.8),.405,.016,steel,ear,rot)
        for a in (.6,2.7,4.8):
            cylinder(label+' ear bezel screw',(sx*2.19,.51*math.sin(a),3.8+.51*math.cos(a)),.025,.014,steel,ear,rot,24)
        a=(sx*1.75,.10,4.30);b=(sx*1.99,.10,5.65)
        rod(label+' radio antenna mast',a,b,.055,steel,ear)
        rod(label+' antenna lower sleeve',a,(sx*1.81,.10,4.64),.092,creamlight,ear)
        rod(label+' antenna dark collar',(sx*1.96,.10,5.51),b,.062,graphite,ear)
        sphere(label+' glowing antenna tip',(sx*2.003,.1,5.73),(.093,.093,.12),glow,ear)
        sphere(label+' antenna tip highlight',(sx*2.003,-.03,5.76),(.035,.015,.045),highlight,ear,24)

    status('Sculpting friendly eyes and expression')
    # Iris vertex colors keep the radial teal shading portable in the GLB.
    inode=iris.node_tree.nodes.new('ShaderNodeVertexColor');inode.layer_name='IrisColor'
    ip=next(n for n in iris.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    iris.node_tree.links.new(inode.outputs['Color'],ip.inputs['Base Color'])
    for sx,label in [(-1,'Left'),(1,'Right')]:
        x=sx*.62;z=3.86
        sphere(label+' soft dark eye socket',(x,-1.173,z),(.405,.085,.545),eyeseal,face)
        sphere(label+' pearlescent eye surround',(x,-1.205,z),(.373,.09,.505),white,face)
        ix=x+sx*.005;iz=z-.015;seg=96;radii=[.61,.72,.87,1]
        verts=[]
        for r in radii:
            for i in range(seg):
                a=math.tau*i/seg
                verts.append((ix+.268*r*math.cos(a),-1.31-.017*(1-r*r),iz+.356*r*math.sin(a)))
        fs=[(j*seg+i,j*seg+(i+1)%seg,(j+1)*seg+(i+1)%seg,(j+1)*seg+i) for j in range(len(radii)-1) for i in range(seg)]
        eye=mesh(label+' dimensional turquoise iris',verts,fs,iris,face)
        colors=eye.data.color_attributes.new(name='IrisColor',type='FLOAT_COLOR',domain='CORNER')
        for loop in eye.data.loops:
            v=eye.data.vertices[loop.vertex_index].co
            a=math.atan2((v.z-iz)/.356,(v.x-ix)/.268)
            r=math.hypot((v.x-ix)/.268,(v.z-iz)/.356)
            light=.25+.75*max(0,-math.sin(a))
            edge=.32 if r>.96 else 1
            fibers=.90+.10*math.sin(a*61)
            colors.data[loop.index].color=(.035*light*edge,.78*light*edge*fibers,.59*light*edge*fibers,1)
        eye.data.color_attributes.active_color=colors
        sphere(label+' deep black pupil',(ix,-1.331,iz+.035),(.180,.024,.258),pupil,face)
        sphere(label+' large white catchlight',(ix-.083,-1.365,iz+.177),(.075,.014,.075),highlight,face,32)
        sphere(label+' small white catchlight',(ix+.09,-1.355,iz-.155),(.024,.01,.024),highlight,face,24)
        # Tapered arched brows carry the same gentle expression as the reference.
        points=[]
        for i in range(32):
            t=i/31;xx=x-.25+.5*t
            zz=4.48+.11*math.sin(math.pi*t)+sx*.06*(t-.5)
            points.append((xx,-1.205,zz))
        line(label+' soft lavender eyebrow',points,.027,brow,face)
    smilepoints=[(-.28+.56*i/40,-1.201,3.23-.075*math.sin(math.pi*i/40)) for i in range(41)]
    line('Gentle mint smile',smilepoints,.025,smile,face)
    for co in (smilepoints[0],smilepoints[-1]):sphere('Rounded smile end',co,(.025,.025,.025),smile,face,20)

    status('Building articulated neck and chest armor')
    cylinder('Neck bottom swivel',(0,.10,2.09),.57,.30,steel,neck)
    for i in range(4):
        cylinder('Neck graphite accordion ring',(0,.10,2.23+i*.115),.43-.022*i,.10,graphite,neck)
    torus('Neck upper metal lip',(0,.1,2.60),.43,.045,steel,neck)
    torus('Neck lower ceramic collar',(0,.1,2.08),.56,.055,creamlight,neck)
    superellipsoid('Torso dark underlying chassis',(0,.16,.88),(1.06,.63,1.18),.65,graphite,torso,64,40)
    superellipsoid('Cream torso main shell',(0,.10,.88),(1.02,.64,1.12),.65,cream,torso,64,40)
    for sx in (-1,1):
        superellipsoid('Olive side torso insert',(sx*.95,.04,.56),(.18,.59,.56),.65,sage,torso,48,32)
    chest=[(-.40,1.95),(.40,1.95),(.77,1.64),(.79,1.08),(.53,.77),(-.53,.77),(-.79,1.08),(-.77,1.64)]
    panel('Chest dark panel gasket',[(x*1.025,(z-1.35)*1.025+1.35) for x,z in chest],-.615,.12,seam,torso,.09)
    panel('Segmented central chest shield',chest,-.66,.12,creamlight,torso,.085)
    panel('Green chest badge graphite recess',[(-.28,1.53),(.28,1.53),(.18,1.22),(-.18,1.22)],-.799,.055,darkgreen,torso,.065)
    panel('Rounded green chest badge',[(-.24,1.50),(.24,1.50),(.155,1.25),(-.155,1.25)],-.825,.05,sage,torso,.055)
    for sx in (-1,1):
        cube('Chest auxiliary status button',(sx*.48,-.80,1.38),(.12,.06,.27),steel,torso,.045,(0,sx*.36,0))
        line('Torso curved side panel seam',[(sx*.78,-.56,1.13),(sx*.97,-.34,.94),(sx*.99,-.30,.35)],.012,seam,torso)
    panel('Abdominal panel graphite gasket',[(-.55,.74),(.55,.74),(.73,.35),(.62,-.16),(-.62,-.16),(-.73,.35)],-.63,.08,seam,torso,.09)
    panel('Rounded lower abdominal plate',[(-.52,.71),(.52,.71),(.69,.34),(.59,-.13),(-.59,-.13),(-.69,.34)],-.675,.09,cream,torso,.08)
    cube('Upper chest dark collar inset',(0,-.49,1.98),(.45,.17,.15),steel,torso,.055)

    status('Building layered shoulders and upper arms')
    for sx,label in [(-1,'Left'),(1,'Right')]:
        arm=group(label+' arm | separate shoulder and forearm',arms)
        sphere(label+' shoulder joint',(sx*1.13,.06,1.43),(.45,.48,.53),graphite,arm)
        torus(label+' shoulder machined joint rim',(sx*1.18,.03,1.43),.43,.055,steel,arm,(0,math.pi/2,0))
        # Cream shoulder cover is an open-bottom spherical shell, exposing the joint.
        verts=[];N=64;R=20
        for j in range(R+1):
            phi=.015+1.72*j/R
            for i in range(N):
                a=math.tau*i/N
                verts.append((sx*1.37+.55*math.sin(phi)*math.cos(a),.04+.54*math.sin(phi)*math.sin(a),1.37+.62*math.cos(phi)))
        fs=[(j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i) for j in range(R) for i in range(N)]
        shoulder=mesh(label+' cream shoulder armor cap',verts,fs,cream,arm)
        sol=shoulder.modifiers.new('Shoulder ceramic thickness','SOLIDIFY');sol.thickness=.05
        # Olive crown plate nestled into the ivory shoulder shell.
        sphere(label+' olive shoulder accent',(sx*1.36,.025,1.929),(.29,.38,.085),sage,arm)
        a=(sx*1.39,.05,1.26);b=(sx*1.63,.035,.37)
        rod(label+' upper arm graphite actuator',a,b,.285,graphite,arm)
        sphere(label+' elbow joint',(sx*1.64,.035,.36),(.30,.31,.29),steel,arm)
        superellipsoid(label+' cream forearm cover',(sx*1.73,-.005,.0),(.38,.39,.47),.65,cream,arm,64,32)
        torus(label+' forearm olive upper trim',(sx*1.70,0,.37),.275,.04,sage,arm)
        cylinder(label+' lower forearm end cap',(sx*1.73,-.005,-.44),.29,.04,steel,arm)

    # Bring the stylized construction coordinates to a documented bust scale.
    root.scale=(.28,.28,.28)
    root['reference']='User-supplied cream and green friendly robot portrait'
    root['scope']='Upper-body bust; hidden legs and hands are not inferred'
    root['scale_note']='Construction coordinates scaled by 0.28; scene units meters'
    bpy.context.view_layer.update()

    status('Setting up portrait studio')
    world=bpy.data.worlds.new('NOVA / neutral portrait studio');world.use_nodes=True;scene.world=world
    bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
    bg.inputs[0].default_value=(.82,.85,.89,1);bg.inputs[1].default_value=.55
    def area(name,loc,target,energy,size,color):
        bpy.ops.object.light_add(type='AREA',location=loc)
        o=bpy.context.object;o.name=name;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.data.color=color
        o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    area('Large warm portrait softbox',(-2.8,-3.4,3.5),(0,0,1),330,2.8,(1,.85,.72))
    area('Cool front fill softbox',(2.8,-2.6,2.2),(0,0,1),180,2.4,(.73,.85,1))
    area('Warm rear edge light',(.6,2.5,3.4),(0,0,1.1),390,2,(1,.79,.53))
    area('Face highlight strip',(-.2,-2.8,3.3),(0,-.25,1.2),55,.7,(1,1,1))
    bpy.ops.object.camera_add(location=(-1.05,-4.35,1.92))
    camera=bpy.context.object;camera.name='Robot portrait camera'
    target=Vector((0,0,.76));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=1.89;camera.data.lens=65
    scene.camera=camera
    try:scene.render.engine='CYCLES'
    except TypeError:raise RuntimeError('This asset preview needs the available Cycles renderer')
    scene.cycles.samples=64;scene.cycles.use_denoising=True
    scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
    formats=[i.identifier for i in scene.render.image_settings.bl_rna.properties['file_format'].enum_items]
    scene.render.image_settings.file_format=next(x for x in formats if x=='PNG')
    scene.render.film_transparent=True
    # This dynamic enum under-reports as NONE in background mode. AgX was
    # verified in this Blender's runtime list of accepted transforms.
    scene.view_settings.view_transform='AgX'
    scene.view_settings.exposure=.15
    for screen in bpy.data.screens:
        for area_ in screen.areas:
            if area_.type=='VIEW_3D':
                area_.spaces.active.region_3d.view_perspective='CAMERA'
    # Export only the robot hierarchy; no studio lights/camera or default cube.
    status('Saving editable robot and GLB')
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
    bpy.ops.object.select_all(action='DESELECT')
    descendants=set()
    def visit(obj):
        descendants.add(obj)
        for child in obj.children:visit(child)
    visit(root)
    for obj in descendants:obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(MODEL),export_format='GLB',use_selection=True,use_active_scene=True,
        export_apply=True,export_yup=True,export_cameras=False,export_lights=False)
    deps=bpy.context.evaluated_depsgraph_get();tris=0
    coords=[]
    for obj in descendants:
        if obj.type in {'MESH','CURVE'}:
            ev=obj.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();tris+=len(me.loop_triangles)
            coords += [obj.matrix_world@Vector(c) for c in ev.bound_box]
            ev.to_mesh_clear()
    low=[min(v[i] for v in coords) for i in range(3)];high=[max(v[i] for v in coords) for i in range(3)]
    stats=dict(source=str(SOURCE),model=str(MODEL),preview=str(PREVIEW),back_preview=str(BACK),
        model_objects=len(descendants),triangles=tris,dimensions_meters=[round(high[i]-low[i],4) for i in range(3)],
        units='meters',export_up_axis='Y',animation_clips=[],external_assets=[],
        scope='Static editable upper-body robot bust based on user-provided portrait',
        materials='Portable PBR colors and modeled facial features; no image textures',
        reference='User-supplied image in conversation; no reference image embedded')
    status('Rendering front portrait',**stats)
    scene.render.filepath=str(PREVIEW);bpy.ops.render.render(write_still=True)
    status('Rendering back three-quarter preview',**stats)
    front_loc=camera.location.copy();front_rot=camera.rotation_euler.copy()
    camera.location=(1.65,3.5,1.7);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.resolution_x=800;scene.render.resolution_y=1000
    scene.render.filepath=str(BACK);bpy.ops.render.render(write_still=True)
    camera.location=front_loc;camera.rotation_euler=front_rot
    scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.filepath=str(PREVIEW)
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
    status('Complete',**stats)
except Exception:
    status('Failed',traceback=traceback.format_exc())
    raise
