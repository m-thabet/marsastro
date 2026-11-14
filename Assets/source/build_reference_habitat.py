"""Cream/orange habitat exterior modeled from the supplied reference image.

All geometry and materials are original procedural construction. Creates a
dedicated scene and refuses to overwrite an existing source or model.
"""
import bpy
import math
import json
import time
import traceback
from pathlib import Path
from mathutils import Vector

ASSETS=Path(__file__).resolve().parents[1]
STEM='habitat-reference-module'
SOURCE=ASSETS/'source'/(STEM+'.blend')
MODEL=ASSETS/'buildings'/(STEM+'.glb')
PREVIEW=ASSETS/'previews'/(STEM+'.png')
BACK=ASSETS/'previews'/(STEM+'-rear.png')
REPORT=ASSETS/'previews'/(STEM+'-report.json')
for folder in (SOURCE.parent,MODEL.parent,PREVIEW.parent):folder.mkdir(parents=True,exist_ok=True)
START=time.time()

def status(stage,**data):
    REPORT.write_text(json.dumps(dict(stage=stage,elapsed_seconds=round(time.time()-START,2),**data),indent=2))

def mat(name,color,metal=.1,rough=.45,emission=0):
    m=bpy.data.materials.new('Habitat / '+name);m.use_nodes=True;m.diffuse_color=(*color,1)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    p.inputs['Coat Weight'].default_value=.13
    if emission:
        p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    return m

def group(name,parent=None):
    o=bpy.data.objects.new(name,None);scene.collection.objects.link(o);o.parent=parent;return o

def mesh(name,verts,faces,material,parent,smooth=True):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.parent=parent
    if material:data.materials.append(material)
    if smooth:
        for p in data.polygons:p.use_smooth=True
    return o

def box(name,loc,size,material,parent,bevel=.08,rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        b=o.modifiers.new('Rounded manufactured edges','BEVEL');b.width=bevel;b.segments=3
        o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    o.rotation_euler=rotation;o.parent=parent;o.data.materials.append(material);return o

def cylinder(name,loc,r,depth,material,parent,rotation=(0,0,0),segments=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=segments,radius=r,depth=depth,location=loc)
    o=bpy.context.object;o.name=name;o.rotation_euler=rotation;o.parent=parent;o.data.materials.append(material)
    b=o.modifiers.new('Machined rim','BEVEL');b.width=min(.035,depth*.15);b.segments=2
    o.modifiers.new('Rim weighted normals','WEIGHTED_NORMAL')
    for p in o.data.polygons:p.use_smooth=True
    return o

def rod(name,a,b,r,material,parent):
    a,b=Vector(a),Vector(b);o=cylinder(name,(a+b)/2,r,(b-a).length,material,parent,segments=20)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def line(name,points,r,material,parent,closed=False):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=r;data.bevel_resolution=2
    s=data.splines.new('POLY');s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    s.use_cyclic_u=closed
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.parent=parent;data.materials.append(material);return o

def torus(name,loc,r,tube,material,parent):
    bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=tube,major_segments=64,minor_segments=10,location=loc)
    o=bpy.context.object;o.name=name;o.parent=parent;o.data.materials.append(material)
    for p in o.data.polygons:p.use_smooth=True
    return o

def signpow(v,e):return math.copysign(abs(v)**e,v)
def squircle(a,rx,ry,n=4):return rx*signpow(math.cos(a),2/n),ry*signpow(math.sin(a),2/n)

PROFILE=[(.60,6.34,3.36),(1.05,6.66,3.57),(1.85,6.85,3.70),(3.10,6.85,3.70),
    (3.85,6.66,3.58),(4.48,6.22,3.26),(4.96,5.65,2.86),(5.25,4.94,2.46),(5.31,4.58,2.28)]

def profile(z):
    for i in range(len(PROFILE)-1):
        a,b=PROFILE[i:i+2]
        if a[0]<=z<=b[0]:
            t=(z-a[0])/(b[0]-a[0]);prev=PROFILE[max(0,i-1)];nxt=PROFILE[min(len(PROFILE)-1,i+2)]
            result=[]
            for axis in (1,2):
                m0=(b[axis]-prev[axis])/(b[0]-prev[0])*(b[0]-a[0])
                m1=(nxt[axis]-a[axis])/(nxt[0]-a[0])*(b[0]-a[0])
                value=(2*t**3-3*t*t+1)*a[axis]+(t**3-2*t*t+t)*m0+(-2*t**3+3*t*t)*b[axis]+(t**3-t*t)*m1
                result.append(value)
            return result
    return PROFILE[0][1:] if z<PROFILE[0][0] else PROFILE[-1][1:]

def hull_y(x,z):
    rx,ry=profile(z);return -ry*max(.001,1-abs(x/rx)**4)**.25
def hull_x(y,z):
    rx,ry=profile(z);return -rx*max(.001,1-abs(y/ry)**4)**.25

def hull(name,profiles,material,parent,segments=192):
    vs=[]
    for z,rx,ry in profiles:
        for i in range(segments):
            x,y=squircle(i*math.tau/segments,rx,ry);vs.append((x,y,z))
    fs=[(j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i)
        for j in range(len(profiles)-1) for i in range(segments)]
    fs += [tuple(reversed(range(segments))),tuple((len(profiles)-1)*segments+i for i in range(segments))]
    return mesh(name,vs,fs,material,parent)

def face_panel(name,outline,y,depth,material,parent,bevel=.05):
    n=len(outline);vs=[(x,y,z) for x,z in outline]+[(x,y+depth,z) for x,z in outline]
    fs=[tuple(reversed(range(n))),tuple(n+i for i in range(n))]
    fs += [(i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n)]
    o=mesh(name,vs,fs,material,parent,False)
    b=o.modifiers.new('Panel perimeter radius','BEVEL');b.width=bevel;b.segments=3
    o.modifiers.new('Panel weighted normals','WEIGHTED_NORMAL');return o

def wrapped_window(name,cu,cz,rx,rz,axis='front'):
    def point(u,z,offset):
        if axis=='left':return (hull_x(u,z)-offset,u,z)
        if axis=='rear':return (u,-hull_y(u,z)+offset,z)
        return (u,hull_y(u,z)-offset,z)
    # True curved perimeter rings follow the hull rather than floating flat over it.
    N=96
    for label,outer,inner,offset,material in [
        ('ivory rim',1.16,1.075,.065,shell),('deep rubber gasket',1.075,1.0,.095,dark),
        ('inner metal liner',1.0,.94,.125,metal)]:
        vs=[]
        for scale in (outer,inner):
            for i in range(N):
                u,z=squircle(i*math.tau/N,rx*scale,rz*scale,4)
                vs.append(point(cu+u,cz+z,offset))
        fs=[(i,(i+1)%N,N+(i+1)%N,N+i) for i in range(N)]
        o=mesh(name+' / '+label,vs,fs,material,windows)
        solid=o.modifiers.new('Window frame thickness','SOLIDIFY');solid.thickness=.035
    vs=[point(cu,cz,.145)]
    for j in range(1,9):
        for i in range(N):
            u,z=squircle(i*math.tau/N,rx*.94*j/8,rz*.94*j/8,4)
            vs.append(point(cu+u,cz+z,.145))
    fs=[(0,1+i,1+(i+1)%N) for i in range(N)]
    fs += [(1+(j-1)*N+i,1+(j-1)*N+(i+1)%N,1+j*N+(i+1)%N,1+j*N+i) for j in range(1,8) for i in range(N)]
    mesh(name+' / smoked blue glazing',vs,fs,glass,windows)
    if axis!='left':
        line(name+' / center mullion',[point(cu,cz+rz*.94*(-1+2*i/24),.18) for i in range(25)],.032,dark,windows)

def arch_ring(name,cx,cz,profiles,material,parent,segments=128):
    vs=[]
    for rx,rz,y in profiles:
        for i in range(segments):
            x,z=squircle(i*math.tau/segments,rx,rz,3.7);vs.append((cx+x,y,cz+z))
    fs=[(j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i)
        for j in range(len(profiles)-1) for i in range(segments)]
    return mesh(name,vs,fs,material,parent)

try:
    if SOURCE.exists() or MODEL.exists():raise FileExistsError('Choose a new stem to preserve the prior habitat.')
    scene=bpy.data.scenes.new('Habitat / Reference Exterior');bpy.context.window.scene=scene;scene.unit_settings.system='METRIC'
    root=group('Habitat | reference exterior module')
    body=group('Hull | paneled rounded pressure shell',root)
    foundation=group('Foundation | skirt feet and service panels',root)
    windows=group('Windows | curved double glazing assemblies',root)
    entry=group('Airlock | arch door and status lights',root)
    ramp=group('Ramp | segmented access platform',root)
    roof=group('Roof | domed skylight and orange bridge',root)
    equipment=group('Equipment | antennas vents and communications dish',root)
    shell=mat('Warm ivory ceramic',(.80,.70,.59),.14,.39)
    edge=mat('Light ivory panel edges',(.91,.82,.70),.12,.36)
    seam=mat('Warm panel seam',(.29,.245,.20),.1,.65)
    dark=mat('Graphite pressure gaskets',(.043,.044,.046),.23,.43)
    trim=mat('Charcoal equipment casing',(.10,.105,.112),.36,.42)
    metal=mat('Warm brushed titanium',(.29,.27,.245),.68,.33)
    doorsteel=mat('Airlock door titanium',(.27,.235,.20),.50,.39)
    orange=mat('Safety orange enamel',(.98,.30,.018),.18,.34)
    glass=mat('Smoked blue glass',(.031,.065,.082),.45,.19)
    p=next(n for n in glass.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Coat Weight'].default_value=.5
    light=mat('Warm recessed status lamps',(1,.72,.32),.08,.3,2.0)

    status('Building smooth paneled hull and foundation')
    dense=[]
    for j in range(81):
        z=.6+(5.31-.6)*j/80;rx,ry=profile(z);dense.append((z,rx,ry))
    hull('Continuous rounded pressure hull',dense,shell,body)
    hull('Deep graphite lower equipment skirt',[(.16,6.23,3.28),(.30,6.55,3.52),(.64,6.74,3.66),
        (1.05,6.72,3.64),(1.22,6.65,3.58)],trim,foundation)
    for z in (1.20,1.85,3.57,4.55):
        rx,ry=profile(z)
        line('Continuous horizontal shell joint',[(x*1.002,y*1.002,z) for x,y in [squircle(i*math.tau/256,rx,ry) for i in range(256)]],.013,seam,body,True)
    # Meridians create real panel divisions around the curved roof and end caps.
    for theta in [math.tau*i/20 for i in range(20)]:
        pts=[]
        for j in range(90):
            z=.65+(5.3-.65)*j/89;rx,ry=profile(z);x,y=squircle(theta,rx,ry)
            pts.append((x*1.002,y*1.002,z))
        line('Curved vertical pressure-panel joint',pts,.013,seam,body)
    # Structural charcoal bands around the rounded short ends.
    for sx in (-1,1):
        u=sx*.84;vs=[];N=70
        for side in (-1,1):
            for j in range(N):
                z=.72+4.32*j/(N-1);rx,ry=profile(z);x=rx*(u+side*.017)
                vs.append((x,hull_y(x,z)-.027,z))
        fs=[(i,i+1,N+i+1,N+i) for i in range(N-1)]
        o=mesh('Front structural end rib',vs,fs,trim,body)
        solid=o.modifiers.new('Structural rib thickness','SOLIDIFY');solid.thickness=.06
    for x,y in [(-5.8,-2.8),(-3.8,-3.65),(6.0,-2.6),(-5.8,2.8),(5.8,2.8)]:
        cylinder('Rounded landing foot base',(x,y,.45),.57,.64,dark,foundation)
        cylinder('Landing foot ivory band',(x,y,.62),.565,.44,shell,foundation)
        cylinder('Landing foot upper shock casing',(x,y,.97),.49,.34,trim,foundation)
        box('Foot orange inset',(x,y-.535,.62),(.35,.075,.25),orange,foundation,.055)
        box('Foot amber running light',(x,y-.581,.65),(.25,.025,.11),light,foundation,.035)
    for x in (-4.4,-2.7,.0,3.8,5.2):
        y=hull_y(x,.75)-.04
        box('Skirt removable service panel',(x,y,.65),(1.14,.14,.48),metal,foundation,.08)
        for k in range(2):box('Skirt service vent',(x,y-.085,.58+k*.15),(.68,.035,.065),dark,foundation,.015)
    for sx in (-1,1):
        face_panel('Low orange hull safety marker',[(sx*4.8,1.16),(sx*4.65,1.52),(sx*4.09,1.52),(sx*3.87,1.16)],
            -3.63,.035,orange,body,.03)

    status('Fitting curved smoked-glass window modules')
    wrapped_window('Front left paired window',-2.6,2.70,1.15,.52)
    wrapped_window('Front right paired window',5.00,2.70,1.0,.49)
    wrapped_window('Left end window',-.80,2.64,.91,.49,'left')
    wrapped_window('Rear left paired window',-3.25,2.70,1.05,.48,'rear')
    wrapped_window('Rear right paired window',3.25,2.70,1.05,.48,'rear')

    status('Modeling layered airlock arch and recessed door')
    ex=1.45;ez=2.67
    arch_ring('Airlock massive ivory surround',ex,ez,[(1.92,2.41,-3.05),(1.92,2.41,-3.75),
        (1.76,2.30,-4.24),(1.32,1.92,-4.39),(1.32,1.92,-3.12)],edge,entry)
    arch_ring('Airlock dark pressure seal',ex,ez,[(1.33,1.93,-4.395),(1.15,1.79,-4.44),(1.15,1.79,-3.6)],dark,entry)
    # Orange enamel horseshoe follows the actual upper arch.
    vs=[];N=100
    for rx,rz in [(1.49,2.10),(1.33,1.94)]:
        for i in range(N):
            a=.025*math.pi+.95*math.pi*i/(N-1);x,z=squircle(a,rx,rz,3.7);vs.append((ex+x,-4.405,ez+z))
    fs=[(i,i+1,N+i+1,N+i) for i in range(N-1)]
    band=mesh('Orange arch inset band',vs,fs,orange,entry)
    solid=band.modifiers.new('Raised orange enamel','SOLIDIFY');solid.thickness=.045
    outline=[(-.74,.89),(.74,.89),(1.00,1.18),(1.00,3.85),(.73,4.15),(-.73,4.15),(-1.00,3.85),(-1.00,1.18)]
    face_panel('Airlock charcoal door frame',[(ex+x,z) for x,z in outline],-4.455,.18,trim,entry,.075)
    outline2=[(-.63,1.04),(.63,1.04),(.84,1.30),(.84,3.66),(.62,3.94),(-.62,3.94),(-.84,3.66),(-.84,1.30)]
    face_panel('Armored titanium airlock leaf',[(ex+x,z) for x,z in outline2],-4.59,.11,doorsteel,entry,.06)
    doorline=[(ex+x,-4.655,z) for x,z in [(-.55,1.18),(.55,1.18),(.73,1.4),(.73,2.06),(.61,2.2),
        (.61,2.87),(.73,3.05),(.73,3.58),(.53,3.81),(-.53,3.81),(-.73,3.58),(-.73,3.05),
        (-.61,2.87),(-.61,2.2),(-.73,2.06),(-.73,1.4)]]
    line('Machined door-leaf perimeter joint',doorline,.017,dark,entry,True)
    box('Door inspection-window frame',(ex,-4.68,3.47),(.88,.10,.43),metal,entry,.09)
    box('Door inspection smoked glass',(ex,-4.744,3.47),(.70,.045,.29),glass,entry,.06)
    box('Airlock header lamp casing',(ex,-4.50,4.26),(1.12,.14,.21),trim,entry,.075)
    box('Airlock warm header light',(ex,-4.582,4.26),(.91,.035,.095),light,entry,.04)
    for sx in (-1,1):
        box('Orange inner grab handle',(ex+sx*1.07,-4.55,2.44),(.105,.13,.78),orange,entry,.05)
        box('Jamb recessed lamp gasket',(ex+sx*1.60,-4.27,2.13),(.27,.12,1.35),metal,entry,.12)
        box('Jamb long amber light',(ex+sx*1.60,-4.346,2.13),(.12,.045,1.14),light,entry,.055)
        box('Airlock side impact pod',(ex+sx*1.82,-3.91,.80),(.89,1.35,1.30),trim,entry,.20)
        box('Airlock pod ivory outer plate',(ex+sx*1.95,-4.56,.78),(.53,.21,.96),shell,entry,.13)
        box('Airlock pod service latch',(ex+sx*1.78,-4.62,1.02),(.17,.045,.25),metal,entry,.045)
    face_panel('Door lower kick reinforcement',[(ex-.45,1.13),(ex+.45,1.13),(ex+.30,1.51),(ex-.25,1.51)],-4.681,.04,metal,entry,.035)

    status('Assembling ramp and roof skylight')
    angle=math.atan2(.64,2.6);cy=-5.94;cz=.45
    box('Ramp ivory structural deck',(ex,cy,cz),(2.80,2.75,.20),shell,ramp,.09,(angle,0,0))
    for i in range(3):
        d=-.85+i*.85;y=cy+d*math.cos(angle);z=cz+d*math.sin(angle)+.12
        box('Ramp dark anti-slip tread',(ex,y,z),(2.18,.79,.045),metal,ramp,.035,(angle,0,0))
    for sx in (-1,1):
        box('Ramp orange edge strip',(ex+sx*1.20,cy-.02,cz+.12),(.12,2.60,.045),orange,ramp,.03,(angle,0,0))
    # Oval dome: ceramic lower panels, blue upper glazing, and dark compression band.
    N=96;R=24;vs=[]
    for j in range(R):
        phi=(math.pi/2)*j/R
        for i in range(N):
            a=i*math.tau/N;vs.append((3.24*math.cos(phi)*math.cos(a),.40+2.18*math.cos(phi)*math.sin(a),5.20+1.16*math.sin(phi)))
    top=len(vs);vs.append((0,.40,6.36))
    fs=[(j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i) for j in range(R-1) for i in range(N)]
    fs += [((R-1)*N+i,(R-1)*N+(i+1)%N,top) for i in range(N)]
    dome=mesh('Paneled oval roof skylight',vs,fs,shell,roof)
    dome.data.materials.append(glass)
    for p in dome.data.polygons:
        if p.center.z>5.76:p.material_index=1
    for phi,radius,material in [(0,.13,trim),(.40,.045,metal)]:
        line('Dome continuous compression ring',[(3.24*math.cos(phi)*math.cos(a),.40+2.18*math.cos(phi)*math.sin(a),5.2+1.16*math.sin(phi))
            for a in [i*math.tau/160 for i in range(160)]],radius,material,roof,True)
    for i in range(16):
        a=i*math.tau/16
        line('Dome radial panel rib',[(3.248*math.cos(phi)*math.cos(a),.40+2.187*math.cos(phi)*math.sin(a),5.205+1.163*math.sin(phi))
            for phi in [j*math.pi/2/50 for j in range(51)]],.025,trim if i%2 else metal,roof)
    def dome_patch(name,x0,x1,y0,y1,height,material):
        vs=[];A=12;B=28
        for j in range(B+1):
            y=y0+(y1-y0)*j/B
            for i in range(A+1):
                x=x0+(x1-x0)*i/A
                z=5.2+1.16*math.sqrt(max(.001,1-(x/3.24)**2-((y-.4)/2.18)**2))+height
                vs.append((x,y,z))
        fs=[(j*(A+1)+i,j*(A+1)+i+1,(j+1)*(A+1)+i+1,(j+1)*(A+1)+i) for j in range(B) for i in range(A)]
        o=mesh(name,vs,fs,material,roof)
        solid=o.modifiers.new('Roof bridge plate thickness','SOLIDIFY');solid.thickness=.05
        return o
    dome_patch('Roof bridge charcoal gasket',-.52,1.02,-1.70,.97,.025,dark)
    dome_patch('Broad orange roof bridge',-.45,.95,-1.65,.45,.065,orange)
    dome_patch('Roof bridge graphite crown cap',-.45,.95,.45,.92,.068,trim)
    box('Roof utility hatch gasket',(-3.63,-1.35,5.15),(1.44,.90,.16),trim,equipment,.15)
    box('Roof flush service hatch',(-3.63,-1.35,5.26),(1.21,.72,.12),shell,equipment,.11)

    status('Adding rooftop antennas vents and parabolic dish')
    def antenna(name,x,y,z,height):
        cylinder(name+' ceramic mount',(x,y,z+.16),.22,.32,shell,equipment)
        cylinder(name+' dark shock collar',(x,y,z+.37),.17,.16,dark,equipment)
        cylinder(name+' lower receiver sleeve',(x,y,z+.70),.12,.60,metal,equipment)
        rod(name+' carbon radio mast',(x,y,z+.87),(x,y,z+height),.045,dark,equipment)
        cylinder(name+' ivory blunt tip',(x,y,z+height+.045),.052,.14,edge,equipment)
    antenna('Left roof radio',-5.04,-.22,4.78,2.33)
    antenna('Tall right radio',4.26,1.24,4.98,3.0)
    antenna('Short right radio',4.72,1.54,4.86,2.45)
    for x,y,z in [(-4.35,.83,4.97),(4.45,1.65,4.95)]:
        cylinder('Roof life-support vent base',(x,y,z+.28),.51,.56,trim,equipment)
        cylinder('Roof vent ivory shoulder',(x,y,z+.63),.51,.19,shell,equipment)
        cylinder('Roof vent orange seal',(x,y,z+.76),.48,.11,orange,equipment)
        cylinder('Roof vent charcoal collar',(x,y,z+.88),.47,.12,dark,equipment)
        cylinder('Roof vent mushroom cap',(x,y,z+1.03),.53,.23,edge,equipment)
        cylinder('Roof vent top recess',(x,y,z+1.153),.27,.02,dark,equipment)
    box('Left roof radio service casing',(-5.02,-.49,4.99),(.47,.45,.73),shell,equipment,.10)
    box('Radio service status lamp',(-5.02,-.73,5.0),(.09,.03,.31),light,equipment,.04)
    for i in range(4):box('Radio service vent',(-5.16,-.73,4.87+i*.08),(.12,.025,.03),dark,equipment,.006)
    dish=group('Dish | steerable parabolic reflector',equipment);dish.location=(5.35,.60,5.53)
    cylinder('Dish pedestal',(5.35,.60,5.15),.31,.35,trim,equipment)
    rod('Dish articulated yoke',(5.35,.60,5.25),(5.35,.60,5.62),.15,metal,equipment)
    N=64;R=12;vs=[(0,0,0)]
    for j in range(1,R+1):
        r=.73*j/R
        for i in range(N):
            a=math.tau*i/N;vs.append((r*math.cos(a),r*math.sin(a),.42*r*r))
    fs=[(0,1+i,1+(i+1)%N) for i in range(N)]
    fs += [(1+(j-1)*N+i,1+(j-1)*N+(i+1)%N,1+j*N+(i+1)%N,1+j*N+i) for j in range(1,R) for i in range(N)]
    reflector=mesh('Concave ivory communications dish',vs,fs,edge,dish)
    solid=reflector.modifiers.new('Dish wall thickness','SOLIDIFY');solid.thickness=.026
    torus('Dish rolled perimeter',(0,0,.42*.73*.73),.73,.024,shell,dish)
    for i in range(8):
        a=math.tau*i/8
        line('Dish petal panel seam',[(r*math.cos(a),r*math.sin(a),.42*r*r+.009) for r in [.73*j/22 for j in range(23)]],.007,seam,dish)
    rod('Dish axial receiver stalk',(0,0,.02),(0,0,.61),.042,trim,dish)
    cylinder('Dish feed horn',(0,0,.63),.075,.12,metal,dish)
    dish.rotation_euler=(math.radians(33),math.radians(-37),math.radians(-10))
    # Rear service equipment completes the unseen side without changing the front brief.
    for x in (-.85,.85):
        box('Rear life-support equipment cabinet',(x,3.68,1.45),(1.25,.35,1.35),trim,equipment,.13)
        for i in range(5):box('Rear cabinet horizontal louver',(x,3.88,1.05+i*.18),(.87,.035,.06),metal,equipment,.015)
        box('Rear cabinet orange identification tab',(x,3.89,1.98),(.29,.03,.10),orange,equipment,.025)

    root['reference']='User-provided cream and orange paneled habitat module image'
    root['scope']='Editable exterior model; rear service details are interpreted from the supplied style'
    root['units']='Meters; display asset dimensions, not a certified engineering design'
    status('Lighting neutral studio and saving GLB')
    stage=mat('Neutral studio ground',(.47,.445,.44),0,.86)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.02));ground=bpy.context.object;ground.name='Studio floor | excluded from GLB';ground.data.materials.append(stage)
    world=bpy.data.worlds.new('Habitat / neutral studio');world.use_nodes=True;scene.world=world
    bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.65,.63,.65,1);bg.inputs[1].default_value=.45
    bpy.ops.object.light_add(type='AREA',location=(-8,-10,16));key=bpy.context.object;key.name='Large soft studio key'
    key.data.energy=3100;key.data.shape='DISK';key.data.size=8;key.data.color=(1,.87,.75)
    key.rotation_euler=(Vector((0,0,2))-key.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.light_add(type='AREA',location=(7,-3,12));fill=bpy.context.object;fill.name='Broad cool studio fill'
    fill.data.energy=2000;fill.data.size=11;fill.data.color=(.82,.89,1)
    fill.rotation_euler=(Vector((0,0,2))-fill.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.light_add(type='SUN',location=(-10,-10,20));sun=bpy.context.object;sun.name='Soft warm studio sun'
    sun.data.energy=1.3;sun.data.angle=math.radians(9);sun.data.color=(1,.91,.80)
    sun.rotation_euler=(math.radians(24),math.radians(-28),math.radians(-30))
    bpy.ops.object.camera_add(location=(-13,-20,12.8));camera=bpy.context.object;camera.name='Habitat reference hero camera'
    target=Vector((0,-.6,3.0));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=20.2;scene.camera=camera
    scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
    scene.render.resolution_x=1536;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.filepath=str(PREVIEW)
    scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.25
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
    stats=dict(source=str(SOURCE),model=str(MODEL),preview=str(PREVIEW),rear_preview=str(BACK),
        nodes=len(objects),triangles=triangles,dimensions_meters=[round(hi[i]-lo[i],4) for i in range(3)],
        units='meters',gltf_up_axis='Y',animation_clips=[],external_assets=[],
        material_type='Portable PBR colors and modeled details; no image textures',
        scope='Editable stylized exterior habitat interpretation of the user-provided reference')
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
    status('Rendering front three-quarter preview',**stats);bpy.ops.render.render(write_still=True)
    loc=camera.location.copy();rot=camera.rotation_euler.copy()
    camera.location=(14,19,12);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.filepath=str(BACK)
    status('Rendering rear preview',**stats);bpy.ops.render.render(write_still=True)
    camera.location=loc;camera.rotation_euler=rot;scene.render.resolution_x=1536;scene.render.resolution_y=1024
    scene.render.filepath=str(PREVIEW);bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE));status('Complete',**stats)
except Exception:
    status('Failed',traceback=traceback.format_exc())
    raise
