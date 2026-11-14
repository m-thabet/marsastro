"""Build the user's cream/orange fan-and-tank life-support reference in 3D.

Dedicated scene, named editable assemblies, portable PBR materials, and a
real recessed window cavity. No downloaded models or image textures are used.
"""
import bpy
import math
import json
import time
import traceback
from pathlib import Path
from mathutils import Vector

ASSETS=Path(__file__).resolve().parents[1]
STEM='life-support-reference-module'
SOURCE=ASSETS/'source'/(STEM+'.blend')
MODEL=ASSETS/'buildings'/(STEM+'.glb')
PREVIEW=ASSETS/'previews'/(STEM+'.png')
BACK=ASSETS/'previews'/(STEM+'-rear.png')
REPORT=ASSETS/'previews'/(STEM+'-report.json')
for folder in (SOURCE.parent,MODEL.parent,PREVIEW.parent):folder.mkdir(parents=True,exist_ok=True)
START=time.time()

def status(stage,**data):
    REPORT.write_text(json.dumps(dict(stage=stage,elapsed_seconds=round(time.time()-START,2),**data),indent=2))

def mat(name,color,metal=.15,rough=.43,emission=0,alpha=1):
    m=bpy.data.materials.new('Life Support / '+name);m.use_nodes=True;m.diffuse_color=(*color,alpha)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    p.inputs['Coat Weight'].default_value=.12;p.inputs['Alpha'].default_value=alpha
    if emission:
        p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    if alpha<1:m.surface_render_method='DITHERED'
    return m

def group(name,parent=None,loc=(0,0,0)):
    o=bpy.data.objects.new(name,None);scene.collection.objects.link(o);o.parent=parent;o.location=loc;return o

def mesh(name,vs,fs,material,parent,smooth=False):
    data=bpy.data.meshes.new(name);data.from_pydata(vs,[],fs);data.update()
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.parent=parent
    if material:data.materials.append(material)
    if smooth:
        for p in data.polygons:p.use_smooth=True
    return o

def box(name,loc,size,material,parent,bevel=.05,rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        b=o.modifiers.new('Manufactured edge radii','BEVEL');b.width=bevel;b.segments=3
        o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    o.rotation_euler=rotation;o.parent=parent
    if material:o.data.materials.append(material)
    return o

def cylinder(name,loc,r,depth,material,parent,rotation=(0,0,0),segments=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=segments,radius=r,depth=depth,location=loc)
    o=bpy.context.object;o.name=name;o.parent=parent;o.rotation_euler=rotation;o.data.materials.append(material)
    b=o.modifiers.new('Machined circular rim','BEVEL');b.width=min(.022,depth*.13);b.segments=2
    o.modifiers.new('Weighted rim normals','WEIGHTED_NORMAL')
    for p in o.data.polygons:p.use_smooth=True
    return o

def rod(name,a,b,r,material,parent):
    a,b=Vector(a),Vector(b);o=cylinder(name,(a+b)/2,r,(b-a).length,material,parent,segments=32)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def beam(name,a,b,width,depth,material,parent):
    a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(width,depth,(b-a).length),material,parent,.045)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def line(name,points,r,material,parent,closed=False):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=r;data.bevel_resolution=3
    s=data.splines.new('POLY');s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    s.use_cyclic_u=closed
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.parent=parent;data.materials.append(material);return o

def outline(rx,ry,c):
    return [(-rx+c,-ry),(rx-c,-ry),(rx,-ry+c),(rx,ry-c),(rx-c,ry),(-rx+c,ry),(-rx,ry-c),(-rx,-ry+c)]

def casing(name,profiles,material,parent,bevel=.06):
    vs=[]
    for z,rx,ry,c in profiles:vs.extend([(x,y,z) for x,y in outline(rx,ry,c)])
    fs=[(j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i) for j in range(len(profiles)-1) for i in range(8)]
    fs += [tuple(reversed(range(8))),tuple((len(profiles)-1)*8+i for i in range(8))]
    o=mesh(name,vs,fs,material,parent)
    if bevel:
        b=o.modifiers.new('Casing edge softness','BEVEL');b.width=bevel;b.segments=3
        o.modifiers.new('Casing weighted normals','WEIGHTED_NORMAL')
    return o

def lathe(name,profiles,material,parent,segments=72,close=True):
    vs=[(r*math.cos(a*math.tau/segments),r*math.sin(a*math.tau/segments),z) for r,z in profiles for a in range(segments)]
    fs=[(j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i)
        for j in range(len(profiles)-1) for i in range(segments)]
    if close:fs += [tuple(reversed(range(segments))),tuple((len(profiles)-1)*segments+i for i in range(segments))]
    return mesh(name,vs,fs,material,parent,True)

def clamp(name,point,direction,radius,material,parent,depth=.11):
    o=cylinder(name,point,radius,depth,material,parent)
    o.rotation_euler=Vector(direction).to_track_quat('Z','Y').to_euler();return o

def elbow(name,cx,cy,cz,radius,a0,a1,tube,material,parent):
    return line(name,[(cx+radius*math.cos(a),cy,cz+radius*math.sin(a))
        for a in [a0+(a1-a0)*i/40 for i in range(41)]],tube,material,parent)

def front_plate(name,rx,rz,chamfer,cx,cz,y0,y1,material,parent):
    points=outline(rx,rz,chamfer);n=len(points)
    vs=[(cx+x,y,cz+z) for y in (y0,y1) for x,z in points]
    fs=[tuple(range(n)),tuple(reversed([n+i for i in range(n)]))]
    fs += [(i,n+i,n+(i+1)%n,(i+1)%n) for i in range(n)]
    return mesh(name,vs,fs,material,parent)

try:
    if SOURCE.exists() or MODEL.exists():raise FileExistsError('Choose a new stem to preserve previous life-support output.')
    scene=bpy.data.scenes.new('Life Support / Reference Processing Module');bpy.context.window.scene=scene;scene.unit_settings.system='METRIC'
    root=group('LifeSupport | reference processing module')
    base=group('Foundation | linked deck and running-light feet',root)
    cabinet=group('Cabinet | paneled filtration enclosure',root,(-1.90,-.25,0))
    filtration=group('Filters | three visible cyan processing cartridges',root)
    fan_mount=group('Fan Mount | articulated yoke and pedestal',root)
    tanks=group('Tanks | twin cream pressure vessels',root)
    plumbing=group('Plumbing | metallic elbows pipes and orange couplings',root)
    equipment=group('Equipment | vents compressor and radio masts',root)
    ivory=mat('Warm ivory ceramic',(.79,.70,.60),.15,.40)
    edge=mat('Light cream panel trim',(.91,.82,.70),.12,.37)
    dark=mat('Graphite pressure seals',(.025,.028,.032),.23,.46)
    trim=mat('Charcoal equipment shells',(.075,.079,.087),.30,.43)
    metal=mat('Brushed warm stainless steel',(.36,.35,.335),.74,.30)
    seam=mat('Recessed warm panel joints',(.29,.25,.21),.15,.65)
    orange=mat('Safety orange enamel',(.96,.205,.006),.12,.37)
    lamp=mat('Warm status-light diffusers',(1,.69,.30),.05,.28,2)
    blue=mat('Blue-grey filter housings',(.105,.225,.265),.50,.30)
    cyan=mat('Cyan cartridge status bands',(.10,.68,.91),.13,.27,1.8)
    glazing=mat('Transparent blue display glazing',(.16,.31,.37),.02,.12,alpha=.16)
    p=next(n for n in glazing.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Coat Weight'].default_value=.35

    status('Building the foundation and recessed filtration cabinet')
    casing('Graphite foundation lower frame',[(.06,5.09,2.93,.38),(.31,5.22,3.04,.40),(.48,5.15,2.98,.40)],trim,base)
    casing('Ivory foundation perimeter deck',[(.32,5.16,2.98,.39),(.56,5.02,2.86,.39)],ivory,base)
    for x in (-4.67,4.70):
        for y in (-2.63,2.63):
            box('Corner impact foot',(x,y,.33),(.78,.75,.58),trim,base,.16)
            box('Corner ivory cap',(x,y,.65),(.73,.70,.15),edge,base,.10)
            if y<0:
                box('Foot orange lamp bezel',(x,y-.387,.35),(.48,.035,.22),orange,base,.055)
                box('Foot amber running lamp',(x,y-.414,.37),(.36,.025,.11),lamp,base,.035)
    for x in (-2.7,0,2.7):
        box('Foundation front handle recess',(x,-3.015,.30),(1.33,.08,.18),dark,base,.055)
        box('Foundation front handle bar',(x,-3.067,.31),(.83,.03,.055),metal,base,.017)
    box('Base orange identification tab',(.42,-2.997,.52),(.66,.05,.14),orange,base,.03)
    profiles=[(.49,2.34,1.65,.34),(.70,2.52,1.80,.43),(2.73,2.52,1.80,.43),
        (3.15,2.36,1.65,.43),(3.47,2.02,1.38,.39),(3.58,1.81,1.20,.36)]
    shell=casing('Filtration cabinet pressure shell',profiles,ivory,cabinet,.075)
    casing('Cabinet graphite lower skirt',[(.48,2.39,1.69,.35),(.77,2.54,1.82,.44)],trim,cabinet,.07)
    # A real Boolean pocket leaves space behind the transparent front glazing.
    cutter=box('Construction | hidden window cavity cutter',(-2.0,-1.91,1.87),(3.55,1.30,1.64),None,None,.17)
    bpy.context.view_layer.objects.active=cutter
    bpy.ops.object.modifier_apply(modifier='Manufactured edge radii')
    cutter.hide_render=True;cutter.hide_set(True)
    boolean=shell.modifiers.new('True recessed processing display','BOOLEAN');boolean.operation='DIFFERENCE';boolean.solver='EXACT';boolean.object=cutter
    shell.modifiers.new('Post-cut weighted normals','WEIGHTED_NORMAL')
    # Dark cavity back and floor make the processing hardware read through glass.
    box('Window cavity dark back panel',(-2.0,-1.288,1.87),(3.43,.035,1.48),dark,filtration,.09)
    box('Window cavity bottom tray',(-2.0,-1.76,1.087),(3.36,.90,.08),trim,filtration,.035)
    # Front frame annulus, with no center-pole shading singularity.
    vs=[]
    for rx,rz,y in [(1.94,.91,-2.045),(1.94,.91,-2.13),(1.74,.74,-2.155),(1.74,.74,-1.97)]:
        vs.extend([(-2+x,y,1.87+z) for x,z in outline(rx,rz,.19)])
    fs=[(j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i) for j in range(3) for i in range(8)]
    frame=mesh('Processing window graphite frame',vs,fs,dark,filtration)
    bevel=frame.modifiers.new('Window rounded perimeter','BEVEL');bevel.width=.035;bevel.segments=3
    frame.modifiers.new('Window frame weighted normals','WEIGHTED_NORMAL')
    front_plate('Clear blue processing display window',1.72,.72,.17,-2.0,1.87,-2.163,-2.183,glazing,filtration)
    for x in (-2.575,-1.425):box('Window vertical structural mullion',(x,-2.196,1.87),(.075,.075,1.46),metal,filtration,.018)
    for i,x in enumerate((-3.15,-2.0,-.85),1):
        cartridge=group('Filter %d | cyan processing cartridge'%i,filtration,(x,-1.73,0))
        cylinder('Filter cartridge body',(0,0,1.87),.286,1.16,blue,cartridge)
        for z in (1.30,2.44):cylinder('Cartridge graphite end cap',(0,0,z),.30,.12,trim,cartridge)
        for z in (1.44,2.28):cylinder('Cyan luminous cartridge band',(0,0,z),.292,.055,cyan,cartridge)
        for z in (1.62,1.81,2.0,2.15):cylinder('Filter segmented housing ring',(0,0,z),.290,.018,metal,cartridge)
        for a in (0,math.pi/2,math.pi,3*math.pi/2):
            rod('Filter vertical cage rib',(.289*math.cos(a),.289*math.sin(a),1.49),(.289*math.cos(a),.289*math.sin(a),2.23),.010,metal,cartridge)
    for x in (-3.99,.13):
        box('Cabinet vertical lamp gasket',(x,-2.09,1.88),(.19,.11,1.37),metal,filtration,.08)
        box('Cabinet warm vertical status lamp',(x,-2.161,1.88),(.081,.035,1.15),lamp,filtration,.038)
    box('Cabinet lower front service slot',(-2.0,-2.105,.80),(1.48,.12,.28),dark,filtration,.065)
    for i in range(2):box('Front low service-vent slat',(-2.0,-2.177,.74+i*.11),(1.08,.024,.038),metal,filtration,.008)
    for x in (-3.70,-.19):box('Cabinet low orange corner tab',(x,-2.05,.74),(.50,.10,.16),orange,filtration,.045)
    # Roof panel joints and a recessed grille.
    for u in (-1.40,0,1.40):
        line('Cabinet roof panel joint',[(u*rx/2.52,-ry-.008,z+.006) for z,rx,ry,c in profiles[2:]],.010,seam,cabinet)
    box('Roof grille outer bezel',(-1.20,-.75,3.62),(2.02,1.05,.14),metal,equipment,.11)
    box('Roof grille dark recess',(-1.20,-.75,3.705),(1.79,.85,.045),dark,equipment,.065)
    for i in range(8):box('Roof ventilation louver',(-1.96+i*.217,-.75,3.744),(.075,.79,.048),trim,equipment,.018)
    box('Roof grille central crossbar',(-1.20,-.75,3.77),(1.78,.045,.04),metal,equipment,.009)
    box('Roof inspection hatch gasket',(-.52,-1.02,3.47),(.87,.63,.12),metal,equipment,.08,(math.radians(17),0,0))
    box('Roof inspection hatch inset',(-.52,-1.045,3.544),(.66,.43,.035),trim,equipment,.045,(math.radians(17),0,0))
    # Right-facing tall louver, as seen in the reference.
    box('Right cabinet intake frame',(.655,-.76,1.74),(.20,1.50,2.13),metal,equipment,.11)
    box('Right cabinet intake recess',(.776,-.76,1.74),(.055,1.29,1.91),dark,equipment,.08)
    for i in range(8):box('Right cabinet intake louver',(.824,-.76,.97+i*.21),(.083,1.19,.09),metal,equipment,.024)
    box('Right intake amber header',(.864,-.76,2.61),(.032,.97,.095),lamp,equipment,.035)
    box('Right intake orange eyebrow',(.759,-.76,2.88),(.17,1.44,.13),orange,equipment,.045)

    status('Constructing the nine-blade ventilation fan and yoke')
    cylinder('Fan pedestal charcoal base',(-2.50,.30,3.67),.84,.23,trim,fan_mount)
    cylinder('Fan pedestal ivory swivel',(-2.50,.30,3.87),.67,.19,edge,fan_mount)
    fan=group('Fan | steerable circular ventilation assembly',root,(-2.50,.30,5.04))
    fan.rotation_euler=Vector((-.16,-.88,.44)).to_track_quat('Z','Y').to_euler()
    fan['editing_note']='Fan assembly orientation is editable; rotor spins around its own local Z axis'
    bpy.context.view_layer.update()
    rotor=group('Rotor | nine blades local-Z pivot',fan)
    # Lathe the fan shroud around its local Z axis.
    profiles=[(1.10,-.36),(1.25,-.27),(1.29,-.10),(1.275,.18),(1.17,.27),(1.075,.225),(1.04,-.29)]
    shroud=lathe('Ivory annular fan shroud',profiles,ivory,fan,96,False)
    shroud.data.materials.append(dark)
    for p in shroud.data.polygons:
        if p.index//96>=5:p.material_index=1
    lathe('Fan front ivory rolled lip',[(1.175,.245),(1.17,.285),(1.075,.25),(1.07,.20)],edge,fan,96,False)
    cylinder('Fan dark rear duct disk',(0,0,-.32),1.04,.09,dark,fan)
    lathe('Fan rear charcoal protective collar',[(1.07,-.43),(1.16,-.39),(1.20,-.29)],trim,fan,72,False)
    for i in range(9):
        vs=[];angle=i*math.tau/9
        for j in range(9):
            t=j/8;r=.25+.80*t;center=angle+.32*t
            for k in range(5):
                s=-1+2*k/4;a=center+(.16+.07*t)*s
                vs.append((r*math.cos(a),r*math.sin(a),.018+.065*s+.024*math.sin(math.pi*t)))
        fs=[(j*5+k,j*5+k+1,(j+1)*5+k+1,(j+1)*5+k) for j in range(8) for k in range(4)]
        blade=mesh('Fan blade %02d'%(i+1),vs,fs,trim,rotor,True)
        solid=blade.modifiers.new('Fan blade thickness','SOLIDIFY');solid.thickness=.045
        bevel=blade.modifiers.new('Rounded blade edges','BEVEL');bevel.width=.018;bevel.segments=2
    cylinder('Rotor graphite center boss',(0,0,.09),.30,.18,dark,rotor)
    cylinder('Rotor orange hub face',(0,0,.205),.255,.12,orange,rotor)
    cylinder('Rotor ivory central cap',(0,0,.282),.174,.035,edge,rotor)
    for a in (.75,2.85,4.9):
        vs=[];N=22
        for z in (-.08,.16):
            for i in range(N):
                t=a-.13+.26*i/(N-1);vs.append((1.295*math.cos(t),1.295*math.sin(t),z))
        fs=[(i,i+1,N+i+1,N+i) for i in range(N-1)]
        patch=mesh('Fan orange shroud identification stripe',vs,fs,orange,fan,True)
        solid=patch.modifiers.new('Enamel stripe thickness','SOLIDIFY');solid.thickness=.015
    for sx in (-1,1):
        target=fan.matrix_world@Vector((sx*1.12,-.13,-.10))
        beam('Fan yoke charcoal arm',(-2.50+sx*.49,.30,3.90),target,.24,.29,trim,fan_mount)
        cylinder('Fan side pivot metal housing',(sx*1.17,-.13,-.10),.28,.21,metal,fan,(0,math.pi/2,0))
        cylinder('Fan side pivot ivory cap',(sx*1.29,-.13,-.10),.205,.065,edge,fan,(0,math.pi/2,0))
        cylinder('Fan side pivot charcoal pin',(sx*1.335,-.13,-.10),.13,.025,trim,fan,(0,math.pi/2,0))

    status('Building twin pressure vessels and portable piping')
    tank_profile=[(.69,.62),(.85,.76),(.885,1.08),(.88,3.89),(.85,4.15),(.77,4.36),(.61,4.55),(.46,4.65),(.44,4.73)]
    for label,x,y in [('A',1.85,.55),('B',3.67,1.38)]:
        tank=group('Tank '+label+' | pressure vessel and status strip',tanks,(x,y,0))
        lathe('Tank '+label+' ivory pressure shell',tank_profile,ivory,tank)
        cylinder('Tank graphite lower mounting sleeve',(0,0,.86),.895,.46,trim,tank)
        cylinder('Tank charcoal mid-height restraint band',(0,0,3.35),.906,.24,trim,tank)
        cylinder('Tank upper dark neck gasket',(0,0,4.69),.54,.13,dark,tank)
        lathe('Tank cream upper vent crown',[(.55,4.75),(.51,4.88),(.43,4.97),(.35,4.99)],edge,tank)
        cylinder('Tank recessed top vent opening',(0,0,4.986),.325,.025,dark,tank)
        for a in (-2.5,-1.45,-.25,.8,2.0):
            pts=[(.888*math.cos(a),.888*math.sin(a),z) for z in [1.13,1.5,2.5,3.5,3.9]]
            pts += [(.85*math.cos(a),.85*math.sin(a),4.15),(.77*math.cos(a),.77*math.sin(a),4.36),(.61*math.cos(a),.61*math.sin(a),4.55)]
            line('Tank formed-shell vertical seam',pts,.008,seam,tank)
        for start,end in [(-2.90,-1.35),(-1.17,.35)]:
            vs=[];N=44
            for z in (1.30,1.46):
                for i in range(N):
                    a=start+(end-start)*i/(N-1);vs.append((.892*math.cos(a),.892*math.sin(a),z))
            fs=[(i,i+1,N+i+1,N+i) for i in range(N-1)]
            mesh('Tank broken orange lower safety band',vs,fs,orange,tank,True)
        # A vertical diffuser is slightly offset around the cylinder toward the viewer.
        a=.30;px=.912*math.sin(a);py=-.912*math.cos(a)
        box('Tank status light charcoal housing',(px,py,3.04),(.25,.12,1.10),trim,tank,.10,(0,0,a))
        box('Tank warm vertical status lamp',(px+.023,py-.070,3.04),(.095,.038,.88),lamp,tank,.044,(0,0,a))
        box('Tank restraint-band locking block',(-.57,-.71,3.35),(.29,.16,.33),trim,tank,.06,(0,0,-.55))
        cylinder('Tank lower front pipe socket',(0,-.88,1.02),.225,.21,dark,tank,(math.pi/2,0,0))
        cylinder('Tank pipe socket steel collar',(0,-1.015,1.02),.18,.10,metal,tank,(math.pi/2,0,0))
    # Tall feed line, with actual rounded metallic elbows and orange couplings.
    rod('Tall feed line dark riser',(.72,.67,.63),(.72,.67,4.70),.158,trim,plumbing)
    elbow('Tall feed line upper curved elbow',1.07,.67,4.70,.35,math.pi,math.pi/2,.16,metal,plumbing)
    rod('Tall feed line horizontal bridge',(1.07,.67,5.05),(1.50,.67,5.05),.16,metal,plumbing)
    elbow('Tall feed line tank inlet bend',1.50,.67,4.70,.35,math.pi/2,0,.16,metal,plumbing)
    rod('Tall feed line tank insertion',(1.85,.67,4.70),(1.85,.67,4.58),.16,metal,plumbing)
    for point,direction in [((.72,.67,4.57),(0,0,1)),((1.17,.67,5.05),(1,0,0)),((1.85,.67,4.65),(0,0,1))]:
        clamp('Tall feed orange pressure coupling',point,direction,.186,orange,plumbing,.115)
    for z in (.82,3.77,4.39):clamp('Tall feed graphite service flange',(.72,.67,z),(0,0,1),.193,dark,plumbing,.12)
    # Cabinet exhaust travels into a descending external pipe.
    cylinder('Cabinet right upper exhaust socket',(.61,-.18,3.03),.235,.16,edge,plumbing,(0,math.pi/2,0))
    rod('Cabinet graphite exhaust bridge',(.61,-.18,3.03),(.97,-.18,3.03),.165,trim,plumbing)
    elbow('Cabinet exhaust descending elbow',.97,-.18,2.72,.31,math.pi/2,0,.166,metal,plumbing)
    rod('Cabinet exhaust dark vertical pipe',(1.28,-.18,2.72),(1.28,-.18,.69),.166,trim,plumbing)
    clamp('Exhaust bridge orange clamp',(.88,-.18,3.03),(1,0,0),.191,orange,plumbing)
    clamp('Exhaust riser orange clamp',(1.28,-.18,2.55),(0,0,1),.192,orange,plumbing,.14)
    clamp('Exhaust pipe lower steel shoe',(1.28,-.18,.75),(0,0,1),.20,metal,plumbing,.15)
    # Low inverted-U manifold in front of the tanks.
    for x in (1.98,3.95):
        rod('Low manifold vertical leg',(x,-1.12,.61),(x,-1.12,1.16),.155,metal,plumbing)
        cylinder('Manifold graphite ground receiver',(x,-1.12,.64),.225,.17,trim,plumbing)
        clamp('Low manifold orange coupling',(x,-1.12,1.02),(0,0,1),.18,orange,plumbing,.12)
    elbow('Low manifold left curved elbow',2.26,-1.12,1.16,.28,math.pi,math.pi/2,.155,metal,plumbing)
    rod('Low manifold horizontal transfer tube',(2.26,-1.12,1.44),(3.67,-1.12,1.44),.155,metal,plumbing)
    elbow('Low manifold right curved elbow',3.67,-1.12,1.16,.28,math.pi/2,0,.155,metal,plumbing)
    for x in (2.43,3.45):clamp('Horizontal manifold orange seal',(x,-1.12,1.44),(1,0,0),.18,orange,plumbing)
    for x,y in [(1.85,.55),(3.67,1.38)]:
        rod('Tank-to-manifold lower branch',(x,y-.99,1.02),(x,-1.11,1.02),.12,trim,plumbing)

    status('Adding compressor cassette antennas and panel details')
    compressor=group('Compressor | low vented equipment cassette',equipment,(.83,-1.73,0))
    casing('Compressor ivory casing',[(.59,.67,.52,.14),(1.12,.67,.52,.14),(1.35,.51,.43,.13)],ivory,compressor)
    box('Compressor front vent gasket',(0,-.537,.94),(1.02,.09,.48),metal,compressor,.08)
    box('Compressor dark louver recess',(0,-.596,.94),(.87,.045,.35),dark,compressor,.055)
    for i in range(3):box('Compressor horizontal louver',(0,-.631,.82+i*.12),(.77,.035,.043),metal,compressor,.009)
    box('Compressor orange side stripe',(-.57,0,.97),(.075,.92,.58),orange,compressor,.04)
    box('Compressor top removable plate',(0,0,1.365),(.77,.65,.055),trim,compressor,.07)
    for x in (-.24,0,.24):line('Compressor top service-panel seam',[(x,-.29,1.399),(x,.29,1.399)],.006,metal,compressor)
    def antenna(name,x,y,z,height):
        cylinder(name+' dark mounting foot',(x,y,z+.08),.12,.16,trim,equipment)
        cylinder(name+' cream lower sleeve',(x,y,z+.21),.072,.22,edge,equipment)
        rod(name+' graphite mast',(x,y,z+.28),(x,y,z+height),.028,dark,equipment)
        cylinder(name+' cream tip',(x,y,z+height+.045),.034,.13,edge,equipment,segments=24)
    antenna('Left cabinet radio',-3.71,.17,3.25,1.23)
    box('Tall radio ivory housing',(.06,.74,3.64),(.65,.65,.46),ivory,equipment,.12)
    box('Tall radio orange top insert',(.06,.74,3.884),(.40,.43,.035),orange,equipment,.06)
    antenna('Tall cabinet radio',.06,.74,3.90,2.12)
    box('Cabinet roof orange identification stripe',(-2.45,-1.46,3.42),(.40,.63,.045),orange,equipment,.04,(math.radians(25),0,0))
    # Complete the non-reference rear with simple service access rather than a blank wall.
    box('Cabinet rear service-door gasket',(-1.87,1.585,1.78),(1.83,.09,1.90),trim,equipment,.14)
    box('Cabinet rear ivory service panel',(-1.87,1.647,1.78),(1.57,.045,1.66),ivory,equipment,.11)
    for z in (1.26,1.45,1.64):box('Rear service-panel vent',(-1.87,1.680,z),(1.08,.025,.065),metal,equipment,.015)
    box('Rear service orange latch',(-1.27,1.69,2.22),(.15,.04,.31),orange,equipment,.025)
    root['reference']='User-supplied cream/orange processing cabinet, fan, twin tanks and pipework image'
    root['scope']='Editable illustrative life-support equipment exterior; no rated engineering process is implied'
    rotor['editing_note']='Rotate local Z to pose the fan rotor; no animation clip is supplied'
    bpy.context.view_layer.update()

    status('Lighting the studio and exporting portable geometry')
    floor=mat('Neutral studio floor',(.47,.445,.44),0,.87)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.015));ground=bpy.context.object;ground.name='Studio floor | excluded from GLB';ground.data.materials.append(floor)
    world=bpy.data.worlds.new('Life Support / neutral studio');world.use_nodes=True;scene.world=world
    bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.65,.63,.65,1);bg.inputs[1].default_value=.36
    for name,loc,energy,size,color in [('Large warm equipment softbox',(-7,-10,14),2400,7,(1,.89,.78)),
        ('Broad cool equipment fill',(7,-2,11),1650,10,(.80,.88,1))]:
        bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.data.color=color
        o.rotation_euler=(Vector((0,0,2.3))-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.light_add(type='SUN',location=(-10,-10,20));sun=bpy.context.object;sun.name='Soft equipment studio sun'
    sun.data.energy=1.3;sun.data.angle=math.radians(9);sun.data.color=(1,.91,.80);sun.rotation_euler=(math.radians(24),math.radians(-28),math.radians(-30))
    bpy.ops.object.camera_add(location=(10,-17,11.5));camera=bpy.context.object;camera.name='Life support reference hero camera'
    target=Vector((0,0,2.65));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=14.6;scene.camera=camera
    scene.render.engine='CYCLES';scene.cycles.samples=80;scene.cycles.use_denoising=True
    scene.render.resolution_x=1536;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.filepath=str(PREVIEW);scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.20
    try:scene.view_settings.look='AgX - Medium High Contrast'
    except TypeError:pass
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
        dimensions_meters=[round(hi[i]-lo[i],4) for i in range(3)],fan_blades=9,pressure_tanks=2,filter_cartridges=3,
        units='meters',gltf_up_axis='Y',animation_clips=[],external_assets=[],
        material_type='Portable PBR colors, transparent glazing and emissive status bands; no image textures',
        scope='Stylized editable life-support module inspired by the supplied reference')
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE));status('Rendering front equipment preview',**stats)
    bpy.ops.render.render(write_still=True)
    loc=camera.location.copy();rot=camera.rotation_euler.copy()
    camera.location=(-11,17,11);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.filepath=str(BACK)
    status('Rendering rear equipment preview',**stats);bpy.ops.render.render(write_still=True)
    camera.location=loc;camera.rotation_euler=rot;scene.render.resolution_x=1536;scene.render.resolution_y=1024
    scene.render.filepath=str(PREVIEW);bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE));status('Complete',**stats)
except Exception:
    status('Failed',traceback=traceback.format_exc())
    raise
