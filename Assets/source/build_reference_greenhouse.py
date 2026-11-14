"""Editable cream/orange greenhouse based on the supplied reference image.

Real curved glazing, six planted trays, 48 crop clusters, and three suspended
grow-light fixtures. Uses a separate scene and preserves existing output files.
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
STEM='greenhouse-reference-module'
SOURCE=ASSETS/'source'/(STEM+'.blend')
MODEL=ASSETS/'buildings'/(STEM+'.glb')
PREVIEW=ASSETS/'previews'/(STEM+'.png')
BACK=ASSETS/'previews'/(STEM+'-rear.png')
REPORT=ASSETS/'previews'/(STEM+'-report.json')
for folder in (SOURCE.parent,MODEL.parent,PREVIEW.parent):folder.mkdir(parents=True,exist_ok=True)
START=time.time();random.seed(4218)

def status(stage,**data):
    REPORT.write_text(json.dumps(dict(stage=stage,elapsed_seconds=round(time.time()-START,2),**data),indent=2))

def mat(name,color,metal=.12,rough=.43,emission=0,alpha=1):
    m=bpy.data.materials.new('Greenhouse / '+name);m.use_nodes=True;m.diffuse_color=(*color,alpha)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    p.inputs['Coat Weight'].default_value=.12;p.inputs['Alpha'].default_value=alpha
    if emission:
        p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    if alpha<1:m.surface_render_method='DITHERED'
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

def box(name,loc,size,material,parent,bevel=.05,rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        b=o.modifiers.new('Rounded manufactured edges','BEVEL');b.width=bevel;b.segments=3
        o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    o.rotation_euler=rotation;o.parent=parent;o.data.materials.append(material);return o

def cylinder(name,loc,r,depth,material,parent,rotation=(0,0,0),segments=40):
    bpy.ops.mesh.primitive_cylinder_add(vertices=segments,radius=r,depth=depth,location=loc)
    o=bpy.context.object;o.name=name;o.parent=parent;o.rotation_euler=rotation;o.data.materials.append(material)
    b=o.modifiers.new('Machined rim radii','BEVEL');b.width=min(.022,depth*.13);b.segments=2
    o.modifiers.new('Weighted circular normals','WEIGHTED_NORMAL')
    for p in o.data.polygons:p.use_smooth=True
    return o

def rod(name,a,b,r,material,parent):
    a,b=Vector(a),Vector(b);o=cylinder(name,(a+b)/2,r,(b-a).length,material,parent,segments=24)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def line(name,points,r,material,parent,closed=False):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=r;data.bevel_resolution=2
    s=data.splines.new('POLY');s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    s.use_cyclic_u=closed
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.parent=parent;data.materials.append(material);return o

def outline(rx,ry,c):
    return [(-rx+c,-ry),(rx-c,-ry),(rx,-ry+c),(rx,ry-c),(rx-c,ry),(-rx+c,ry),(-rx,ry-c),(-rx,-ry+c)]

def casing(name,profiles,material,parent,bevel=.05):
    vs=[]
    for z,rx,ry,c in profiles:vs.extend([(x,y,z) for x,y in outline(rx,ry,c)])
    fs=[(j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i) for j in range(len(profiles)-1) for i in range(8)]
    fs += [tuple(reversed(range(8))),tuple((len(profiles)-1)*8+i for i in range(8))]
    o=mesh(name,vs,fs,material,parent)
    b=o.modifiers.new('Soft casing edges','BEVEL');b.width=bevel;b.segments=3
    o.modifiers.new('Weighted casing normals','WEIGHTED_NORMAL');return o

def front_plate(name,points,y0,y1,material,parent,bevel=.04):
    n=len(points);vs=[(x,y,z) for y in (y0,y1) for x,z in points]
    fs=[tuple(range(n)),tuple(reversed([n+i for i in range(n)]))]
    fs += [(i,n+i,n+(i+1)%n,(i+1)%n) for i in range(n)]
    o=mesh(name,vs,fs,material,parent)
    if bevel:
        b=o.modifiers.new('Soft armor perimeter','BEVEL');b.width=bevel;b.segments=3
        o.modifiers.new('Weighted armor normals','WEIGHTED_NORMAL')
    return o

def cross_section():
    p=[Vector((-2.60,.90)),Vector((-2.60,1.45)),Vector((-2.60,2.2)),Vector((-2.60,3.0))]
    p += [Vector((-2.60*math.cos(phi),3+2.10*math.sin(phi))) for phi in [math.pi*i/64 for i in range(1,65)]]
    p += [Vector((2.60,2.2)),Vector((2.60,1.45)),Vector((2.60,.90))]
    return p

def rib(name,x,width,parent):
    points=cross_section();n=len(points);inner=[]
    for i,p in enumerate(points):
        tangent=(points[min(n-1,i+1)]-points[max(0,i-1)]).normalized()
        normal=Vector((-tangent.y,tangent.x))
        inner.append(p-normal*.13)
    vs=[]
    for xx in (x-width/2,x+width/2):
        vs += [(xx,p.x,p.y) for p in points]+[(xx,p.x,p.y) for p in inner]
    fs=[]
    for i in range(n-1):
        fs.extend([(i,i+1,2*n+i+1,2*n+i),(n+i,3*n+i,3*n+i+1,n+i+1),
            (i,n+i,n+i+1,i+1),(2*n+i,2*n+i+1,3*n+i+1,3*n+i)])
    fs += [(0,2*n,3*n,n),(n-1,2*n-1,4*n-1,3*n-1)]
    o=mesh(name,vs,fs,ivory,parent)
    b=o.modifiers.new('Soft greenhouse rib edges','BEVEL');b.width=.025;b.segments=2
    o.modifiers.new('Rib weighted normals','WEIGHTED_NORMAL');return o

def glaze(name,x0,x1,side,parent):
    if side=='front':
        p=[(-2.60,1.12),(-2.60,1.7),(-2.60,2.3),(-2.60,3.0)]
        p += [(-2.60*math.cos(phi),3+2.10*math.sin(phi)) for phi in [1.377*i/42 for i in range(1,43)]]
    else:
        p=[(-2.60*math.cos(phi),3+2.10*math.sin(phi)) for phi in [math.pi-1.377+1.377*i/42 for i in range(43)]]
        p += [(2.60,2.3),(2.60,1.7),(2.60,1.12)]
    vs=[];A=16;N=len(p)
    for i in range(A+1):
        x=x0+(x1-x0)*i/A
        vs += [(x,y,z) for y,z in p]
    fs=[(i*N+j,(i+1)*N+j,(i+1)*N+j+1,i*N+j+1) for i in range(A) for j in range(N-1)]
    o=mesh(name,vs,fs,glass,parent,True)
    solid=o.modifiers.new('Laminated glass wall thickness','SOLIDIFY');solid.thickness=.018
    # Actual dark perimeter seals frame each curved pane.
    for x in (x0,x1):line(name+' edge pressure gasket',[(x,y,z) for y,z in p],.044,dark,parent)
    return o

def arch_ring(name,profiles,material,parent,cz=2.61):
    N=112;vs=[]
    for rx,rz,y in profiles:
        for i in range(N):
            a=math.tau*i/N;x=rx*math.copysign(abs(math.cos(a))**.55,math.cos(a));z=rz*math.copysign(abs(math.sin(a))**.55,math.sin(a))
            vs.append((x,y,cz+z))
    fs=[(j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i) for j in range(len(profiles)-1) for i in range(N)]
    return mesh(name,vs,fs,material,parent,True)

def crop_foliage(label,parent):
    vs=[];fs=[];indices=[];plant_count=0
    for col in range(4):
        for row in range(2):
            px=-.98+col*.65+random.uniform(-.045,.045);py=-.27+row*.54+random.uniform(-.025,.025)
            for leaf in range(7):
                a=leaf*math.tau/7+random.uniform(-.3,.3);length=random.uniform(.29,.46);width=random.uniform(.105,.155)
                lift=random.uniform(.16,.29);start=len(vs);segments=7
                for j in range(segments+1):
                    t=j/segments;w=width*max(.008,math.sin(math.pi*t)**.75)
                    cx=px+math.cos(a)*length*t;cy=py+math.sin(a)*length*t
                    cz=1.12+lift*math.sin(math.pi*t*.72)+.11*t
                    for s in (-1,0,1):
                        vs.append((cx-math.sin(a)*w*s,cy+math.cos(a)*w*s,cz-.026*abs(s)*math.sin(math.pi*t)))
                color=random.randrange(3)
                for j in range(segments):
                    for k in range(2):
                        fs.append((start+j*3+k,start+(j+1)*3+k,start+(j+1)*3+k+1,start+j*3+k+1));indices.append(color)
            plant_count+=1
    o=mesh('Crop foliage | '+label,vs,fs,leaves[0],parent,True)
    for m in leaves[1:]:o.data.materials.append(m)
    for poly,index in zip(o.data.polygons,indices):poly.material_index=index
    solid=o.modifiers.new('Leaf blade thickness','SOLIDIFY');solid.thickness=.004
    o['plant_count']=plant_count
    return o

try:
    if SOURCE.exists() or MODEL.exists():raise FileExistsError('Choose a new stem to preserve prior greenhouse output.')
    scene=bpy.data.scenes.new('Greenhouse / Reference Hydroponics');bpy.context.window.scene=scene;scene.unit_settings.system='METRIC'
    root=group('Greenhouse | reference hydroponics module')
    base=group('Foundation | skirt feet and interior floor',root)
    structure=group('Structure | arched ivory ribs and end caps',root)
    glazing=group('Glazing | six continuous curved panels',root)
    growing=group('Cultivation | six beds and forty-eight crop clusters',root)
    lighting=group('Grow Lights | three suspended magenta fixtures',root)
    utility=group('Utilities | roof HVAC water tank and plumbing',root)
    door=group('Airlock | end entry and ramp',root,(-5.16,0,0));door.rotation_euler.z=-math.pi/2
    ivory=mat('Warm ivory ceramic',(.79,.70,.60),.15,.40)
    edge=mat('Light cream trim',(.91,.82,.70),.12,.37)
    dark=mat('Graphite pressure seals',(.025,.028,.032),.20,.48)
    trim=mat('Charcoal equipment casing',(.078,.082,.090),.30,.44)
    metal=mat('Brushed warm titanium',(.29,.285,.27),.65,.34)
    orange=mat('Safety orange enamel',(.96,.205,.006),.12,.38)
    lamp=mat('Warm status-light diffuser',(1,.69,.30),.05,.28,2)
    pink=mat('Magenta grow-light diffuser',(.95,.045,.36),.05,.28,3)
    glass=mat('Transparent blue-grey glazing',(.22,.31,.34),.015,.12,alpha=.105)
    p=next(n for n in glass.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Specular IOR Level'].default_value=.25;p.inputs['Coat Weight'].default_value=.25
    door_glass=mat('Dark blue inspection glass',(.035,.065,.085),.40,.21)
    soil=mat('Dark hydroponic medium',(.045,.030,.018),0,.95)
    leaves=[mat('Leaf green %d'%i,c,0,.66) for i,c in enumerate([(.15,.32,.028),(.24,.43,.045),(.31,.47,.065)])]

    status('Building foundation and pressure-frame structure')
    casing('Graphite greenhouse foundation',[(.06,5.29,2.91,.32),(.30,5.40,3.02,.35),(.69,5.33,2.94,.34)],trim,base)
    casing('Ivory greenhouse sill',[(.64,5.30,2.91,.34),(1.12,5.22,2.80,.32)],ivory,base)
    box('Interior raised greenhouse floor',(0,0,.77),(9.90,4.91,.16),edge,base,.07)
    box('Central clear service walkway',(0,0,.87),(9.74,.88,.035),metal,base,.035)
    for x in (-5.09,5.09):
        for y in (-2.64,2.64):
            box('Rounded corner landing foot',(x,y,.46),(.73,.74,.80),trim,base,.16)
            box('Landing-foot ivory cap',(x,y,.895),(.66,.69,.16),edge,base,.10)
            if y<0:
                box('Foot orange lamp recess',(x,y-.38,.43),(.45,.04,.22),orange,base,.055)
                box('Foot amber running light',(x,y-.408,.45),(.34,.025,.11),lamp,base,.033)
    for x in (-3.40,0,3.40):
        box('Sill charcoal service-vent panel',(x,-2.96,.58),(2.71,.11,.52),trim,base,.065)
        box('Sill recessed horizontal vent',(x,-3.025,.59),(1.53,.045,.15),dark,base,.045)
        box('Sill internal vent ridge',(x,-3.055,.59),(1.15,.025,.035),metal,base,.008)
        box('Orange bay identification plate',(x,-2.835,1.12),(1.04,.08,.17),orange,base,.045)
    for x,width in [(-5.08,.33),(-1.70,.20),(1.70,.20),(5.08,.33)]:rib('Ivory arched frame rib',x,width,structure)
    for x in (-5.08,5.08):
        points=cross_section();n=len(points)
        vs=[(xx,p.x,p.y) for xx in (x-.11,x+.11) for p in points]
        fs=[tuple(reversed(range(n))),tuple(n+i for i in range(n))]
        fs += [(i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n)]
        end=mesh('Opaque pressure end cap',vs,fs,ivory,structure)
        b=end.modifiers.new('Soft end-cap edge','BEVEL');b.width=.045;b.segments=3
        end.modifiers.new('End-cap weighted normals','WEIGHTED_NORMAL')
    for side in (-1,1):
        box('Longitudinal glass knee rail',(0,side*2.64,2.93),(10.14,.115,.13),trim,structure,.035)
        box('Longitudinal sill glass gasket',(0,side*2.65,1.14),(10.14,.11,.105),dark,structure,.025)
    for x in (-5.08,5.08):
        box('End-rib status-light gasket',(x,-2.675,2.14),(.25,.12,1.38),metal,structure,.10)
        box('End-rib warm vertical lamp',(x,-2.748,2.14),(.105,.045,1.15),lamp,structure,.045)

    status('Fitting six curved transparent glazing bays')
    for i,(x0,x1) in enumerate([(-4.88,-1.84),(-1.56,1.56),(1.84,4.88)],1):
        glaze('Front bay %d | continuous curved glazing'%i,x0,x1,'front',glazing)
        glaze('Rear bay %d | continuous curved glazing'%i,x0,x1,'rear',glazing)
    box('Roof central charcoal utility spine',(0,0,5.13),(10.16,1.04,.20),trim,structure,.095)
    for i,x in enumerate((-3.78,-1.26,1.26,3.78)):
        box('Roof ivory service-spine panel',(x,0,5.265),(2.40,.96,.13),edge,utility,.09)
        if i in (1,3):box('Roof orange service-spine insert',(x+.27,0,5.345),(.94,.90,.045),orange,utility,.055)
        else:
            box('Roof access-recess frame',(x+.36,0,5.345),(1.18,.65,.06),metal,utility,.055)
            box('Roof dark access-recess inset',(x+.36,0,5.38),(.95,.46,.025),trim,utility,.035)

    status('Planting hydroponic beds and suspending grow-light fixtures')
    bed_count=0
    for col,x in enumerate((-3.34,0,3.34),1):
        for row,y in enumerate((-1.35,1.35),1):
            bed_count+=1;label='%d%d'%(col,row)
            bed=group('Bed '+label+' | planted hydroponic tray',growing,(x,y,0));bed['plant_count']=8
            box('Hydroponic tray graphite base',(0,0,.95),(2.83,1.19,.17),trim,bed,.075)
            box('Hydroponic tray ivory shell',(0,0,1.08),(2.77,1.14,.23),edge,bed,.08)
            box('Hydroponic growing medium',(0,0,1.203),(2.56,.94,.035),soil,bed,.045)
            for sx in (-1,1):box('Tray orange corner label',(sx*1.15,-.58,1.08),(.14,.025,.11),orange,bed,.015)
            # Crop geometry is bed-local; raise stems and leaves to the medium.
            foliage=crop_foliage(label,bed);foliage.location.z=.12
        fixture=group('Grow fixture %d | suspended magenta lamp'%col,lighting,(x,0,0))
        rod('Grow-lamp suspension stem',(0,0,4.81),(0,0,3.90),.047,trim,fixture)
        box('Grow-lamp upper electrical collar',(0,0,3.96),(.21,.21,.20),trim,fixture,.04)
        box('Grow-lamp graphite housing',(0,0,3.80),(1.94,.77,.18),trim,fixture,.075)
        box('Grow-lamp top magenta inset',(0,0,3.898),(1.54,.51,.025),pink,fixture,.04)
        box('Grow-lamp lower magenta diffuser',(0,0,3.695),(1.72,.63,.035),pink,fixture,.04)
        box('Grow-lamp visible front pink strip',(0,-.405,3.79),(1.68,.045,.075),pink,fixture,.032)
        bpy.ops.object.light_add(type='AREA',location=(x,0,3.67));light=bpy.context.object;light.name='Grow illumination %d | excluded from GLB'%col
        light.data.energy=28;light.data.shape='RECTANGLE';light.data.size=1.6;light.data.size_y=.55;light.data.color=(1,.16,.45)
    rod('Interior overhead electrical conduit',(-4.76,0,4.64),(4.76,0,4.64),.056,metal,lighting)

    status('Modeling layered end airlock and access ramp')
    arch_ring('Airlock ivory rounded surround',[(1.56,2.11,-.10),(1.56,2.11,-.40),(1.18,1.75,-.49),(1.18,1.75,-.12)],edge,door)
    arch_ring('Airlock graphite pressure gasket',[(1.19,1.76,-.496),(1.05,1.65,-.535),(1.05,1.65,-.18)],dark,door)
    vs=[];N=96
    for rx,rz in [(1.38,1.96),(1.20,1.78)]:
        for i in range(N):
            a=.025*math.pi+.95*math.pi*i/(N-1)
            vs.append((rx*math.copysign(abs(math.cos(a))**.55,math.cos(a)),-.49,2.61+rz*math.copysign(abs(math.sin(a))**.55,math.sin(a))))
    fs=[(i,i+1,N+i+1,N+i) for i in range(N-1)]
    o=mesh('Airlock orange upper horseshoe',vs,fs,orange,door,True)
    solid=o.modifiers.new('Orange enamel thickness','SOLIDIFY');solid.thickness=.05
    points=[(-.70,.96),(.70,.96),(.96,1.22),(.96,3.91),(.70,4.17),(-.70,4.17),(-.96,3.91),(-.96,1.22)]
    front_plate('Airlock charcoal armored frame',points,-.558,-.32,trim,door,.065)
    points=[(-.58,1.10),(.58,1.10),(.80,1.35),(.80,3.72),(.58,3.97),(-.58,3.97),(-.80,3.72),(-.80,1.35)]
    front_plate('Airlock titanium door leaf',points,-.67,-.54,metal,door,.055)
    line('Machined door-leaf inset joint',[(x,-.736,z) for x,z in [(-.50,1.25),(.50,1.25),(.69,1.46),(.69,2.15),(.58,2.31),
        (.58,2.91),(.69,3.07),(.69,3.63),(.50,3.84),(-.50,3.84),(-.69,3.63),(-.69,3.07),(-.58,2.91),(-.58,2.31),(-.69,2.15),(-.69,1.46)]],.014,dark,door,True)
    box('Door inspection-window gasket',(0,-.751,3.39),(.79,.10,.39),trim,door,.08)
    box('Door dark blue inspection pane',(0,-.813,3.39),(.60,.035,.25),door_glass,door,.05)
    box('Door header-light casing',(0,-.565,4.22),(1.02,.12,.19),dark,door,.06)
    box('Door warm header-light bar',(0,-.639,4.22),(.82,.035,.08),lamp,door,.03)
    for sx in (-1,1):
        box('Airlock orange internal grab handle',(sx*.99,-.64,2.45),(.105,.11,.78),orange,door,.045)
        box('Airlock jamb lamp gasket',(sx*1.37,-.43,2.04),(.23,.11,1.37),metal,door,.09)
        box('Airlock warm vertical jamb light',(sx*1.37,-.498,2.04),(.095,.04,1.13),lamp,door,.04)
        box('Airlock lower impact pod',(sx*1.41,-.27,.91),(.48,.75,.78),trim,door,.12)
    angle=math.atan2(.62,2.20)
    box('Airlock ramp ivory structure',(0,-1.77,.44),(2.53,2.39,.20),ivory,door,.085,(angle,0,0))
    for i in range(3):
        offset=-.70+i*.70
        box('Airlock dark ramp tread',(0,-1.77+offset*math.cos(angle),.56+offset*math.sin(angle)),(1.94,.64,.045),metal,door,.03,(angle,0,0))
    for sx in (-1,1):box('Airlock ramp orange edge strip',(sx*1.08,-1.77,.565),(.105,2.23,.045),orange,door,.025,(angle,0,0))
    box('Airlock upper graphite inspection plate',(0,-.12,4.74),(.88,.66,.10),trim,door,.065,(math.radians(18),0,0))

    status('Adding water supply pump pipework and rooftop HVAC')
    annex=group('Water supply | tank pump and metal pipework',utility,(-5.86,2.05,0))
    casing('Utility annex charcoal foundation',[(.06,.86,1.10,.16),(.40,.89,1.14,.18)],trim,annex)
    casing('Utility annex ivory deck',[(.35,.87,1.12,.17),(.67,.80,1.04,.17)],ivory,annex)
    casing('Water pump ivory casing',[(.68,.69,.74,.13),(1.18,.69,.74,.13),(1.35,.58,.63,.12)],ivory,annex)
    box('Water pump left vent gasket',(-.716,0,.98),(.10,1.04,.43),metal,annex,.065)
    box('Water pump dark vent recess',(-.78,0,.98),(.035,.88,.29),dark,annex,.04)
    for i in range(3):box('Water pump horizontal louver',(-.807,0,.88+i*.105),(.035,.78,.035),metal,annex,.007)
    cylinder('Water tank charcoal mounting collar',(0,0,1.40),.63,.24,trim,annex)
    cylinder('Water tank ivory main body',(0,0,2.24),.61,1.47,ivory,annex)
    cylinder('Water tank orange upper band',(0,0,2.91),.622,.12,orange,annex)
    casing_profile=[]
    N=64
    for r,z in [(.61,2.98),(.61,3.13),(.53,3.31),(.39,3.39)]:
        casing_profile.extend([(r*math.cos(i*math.tau/N),r*math.sin(i*math.tau/N),z) for i in range(N)])
    fs=[(j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i) for j in range(3) for i in range(N)]
    fs += [tuple(3*N+i for i in range(N))]
    mesh('Water tank rounded upper shoulder',casing_profile,fs,edge,annex,True)
    cylinder('Water tank upper pipe gasket',(0,0,3.40),.37,.10,dark,annex)
    rod('Water supply vertical inlet',(0,0,3.40),(0,0,3.95),.13,metal,annex)
    line('Water inlet curved upper elbow',[(.25+.25*math.cos(a),0,3.95+.25*math.sin(a)) for a in [math.pi-math.pi/2*i/36 for i in range(37)]],.13,metal,annex)
    rod('Water inlet end-wall connector',(.25,0,4.20),(.73,0,4.20),.13,metal,annex)
    cylinder('Water inlet vertical orange coupling',(0,0,3.83),.158,.11,orange,annex)
    cylinder('Water inlet horizontal orange coupling',(.48,0,4.20),.158,.11,orange,annex,(0,math.pi/2,0))
    rod('Pump lower vertical service line',(.05,-.66,1.05),(.05,-.66,1.78),.10,metal,annex)
    line('Pump lower curved service elbow',[(.25+.20*math.cos(a),-.66,1.78+.20*math.sin(a)) for a in [math.pi-math.pi/2*i/30 for i in range(31)]],.10,metal,annex)
    rod('Pump lower end-wall connection',(.25,-.66,1.98),(.78,-.66,1.98),.10,metal,annex)
    cylinder('Pump lower orange seal',(.05,-.66,1.55),.13,.10,orange,annex)
    box('Roof HVAC charcoal mounting plinth',(-4.18,0,5.25),(2.12,1.25,.20),trim,utility,.12)
    casing_hvac=casing('Roof HVAC chamfered ivory enclosure',[(5.30,1.02,.59,.16),(5.83,.95,.54,.16),(5.98,.81,.44,.14)],ivory,utility)
    casing_hvac.location.x=-4.18
    box('HVAC orange grille bezel',(-4.18,-.559,5.59),(1.68,.085,.43),orange,utility,.085)
    box('HVAC dark grille recess',(-4.18,-.614,5.59),(1.47,.035,.29),dark,utility,.055)
    for i in range(3):box('HVAC horizontal ventilation louver',(-4.18,-.643,5.50+i*.09),(1.36,.025,.034),metal,utility,.008)
    box('HVAC roof inspection recess',(-4.02,0,5.998),(.98,.59,.035),metal,utility,.055)
    for x in (-4.31,-4.08,-3.85):box('HVAC top grille bar',(x,0,6.027),(.055,.43,.025),trim,utility,.008)
    cylinder('Roof antenna mounting foot',(-4.43,.10,6.08),.10,.16,trim,utility)
    cylinder('Roof antenna lower sleeve',(-4.43,.10,6.27),.060,.25,metal,utility)
    rod('Roof antenna graphite mast',(-4.43,.10,6.38),(-4.43,.10,7.48),.026,dark,utility)
    cylinder('Roof antenna ivory tip',(-4.43,.10,7.53),.033,.14,edge,utility,segments=24)
    # A restrained rear service panel completes the opaque rear end.
    box('Rear service-panel gasket',(5.235,0,2.47),(.10,1.89,2.15),trim,utility,.13)
    box('Rear ivory access panel',(5.30,0,2.47),(.045,1.61,1.88),ivory,utility,.10)
    for i in range(4):box('Rear service horizontal louver',(5.334,0,1.91+i*.16),(.025,1.12,.055),metal,utility,.012)
    box('Rear service orange latch',(5.35,-.57,3.09),(.035,.15,.29),orange,utility,.025)
    root['reference']='User-supplied cream/orange greenhouse with curved glass, crops, magenta lamps, airlock and external water unit'
    root['scope']='Stylized architectural review model with modeled interior crops and fixtures'
    root['bed_count']=6;root['plant_clusters']=48;root['grow_fixtures']=3
    bpy.context.view_layer.update()

    status('Lighting neutral studio and exporting the greenhouse')
    floor=mat('Neutral studio floor',(.47,.445,.44),0,.87)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.015));ground=bpy.context.object;ground.name='Studio floor | excluded from GLB';ground.data.materials.append(floor)
    world=bpy.data.worlds.new('Greenhouse / neutral studio');world.use_nodes=True;scene.world=world
    bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.65,.63,.65,1);bg.inputs[1].default_value=.35
    for name,loc,energy,size,color in [('Large warm greenhouse softbox',(-8,-11,15),2600,8,(1,.89,.78)),
        ('Broad cool greenhouse fill',(8,-2,12),1700,10,(.80,.88,1))]:
        bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.data.color=color
        o.rotation_euler=(Vector((0,0,2.3))-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.light_add(type='SUN',location=(-10,-10,20));sun=bpy.context.object;sun.name='Soft greenhouse studio sun';sun.data.energy=1.3
    sun.data.angle=math.radians(9);sun.data.color=(1,.91,.80);sun.rotation_euler=(math.radians(24),math.radians(-28),math.radians(-30))
    bpy.ops.object.camera_add(location=(-13,-18,12));camera=bpy.context.object;camera.name='Greenhouse reference hero camera'
    target=Vector((-.5,0,2.8));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=17.2;scene.camera=camera
    scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.03
    scene.cycles.transparent_max_bounces=16
    scene.render.resolution_x=1536;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.filepath=str(PREVIEW);scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.20
    try:scene.view_settings.look='AgX - Medium High Contrast'
    except TypeError:pass
    comp=bpy.data.node_groups.new('Greenhouse / restrained grow-light bloom','CompositorNodeTree')
    comp.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
    layers=comp.nodes.new('CompositorNodeRLayers');layers.scene=scene
    glare=comp.nodes.new('CompositorNodeGlare');glare.inputs['Type'].default_value='Fog Glow';glare.inputs['Quality'].default_value='High'
    glare.inputs['Threshold'].default_value=1.5;glare.inputs['Size'].default_value=.35;glare.inputs['Strength'].default_value=.22
    output=comp.nodes.new('NodeGroupOutput');comp.links.new(layers.outputs['Image'],glare.inputs['Image']);comp.links.new(glare.outputs['Image'],output.inputs['Image']);scene.compositing_node_group=comp
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
    stats=dict(source=str(SOURCE),model=str(MODEL),preview=str(PREVIEW),rear_preview=str(BACK),nodes=len(objects),triangles=triangles,
        dimensions_meters=[round(hi[i]-lo[i],4) for i in range(3)],curved_glass_panels=6,hydroponic_beds=6,plant_clusters=48,grow_fixtures=3,
        units='meters',gltf_up_axis='Y',animation_clips=[],external_assets=[],
        material_type='Portable PBR colors, transparent glazing, modeled foliage and emissive lights; no image textures',
        render_only=['Grow illumination area lights','Studio camera floor and lights','Compositor bloom'],
        scope='Editable stylized greenhouse with visible planted interior based on the supplied reference')
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE));status('Rendering front greenhouse preview',**stats)
    bpy.ops.render.render(write_still=True)
    loc=camera.location.copy();rot=camera.rotation_euler.copy()
    camera.location=(13,18,11.5);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.filepath=str(BACK)
    status('Rendering rear greenhouse preview',**stats);bpy.ops.render.render(write_still=True)
    camera.location=loc;camera.rotation_euler=rot;scene.render.resolution_x=1536;scene.render.resolution_y=1024
    scene.render.filepath=str(PREVIEW);bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE));status('Complete',**stats)
except Exception:
    status('Failed',traceback=traceback.format_exc())
    raise
