"""Stylized explorer bust based on the user's supplied portrait.

Creates a dedicated scene. All geometry and materials are procedural; no paid
generators, downloaded assets, or reference-image textures are used.
"""
import bpy
import math
import json
import random
import time
import traceback
from pathlib import Path
from mathutils import Vector

ASSETS=Path(__file__).resolve().parents[1]
STEM='explorer-reference-bust'
SOURCE=ASSETS/'source'/(STEM+'.blend')
MODEL=ASSETS/'characters'/(STEM+'.glb')
PREVIEW=ASSETS/'previews'/(STEM+'.png')
BACK=ASSETS/'previews'/(STEM+'-back.png')
REPORT=ASSETS/'previews'/(STEM+'-report.json')
for p in (SOURCE.parent,MODEL.parent,PREVIEW.parent):p.mkdir(parents=True,exist_ok=True)
START=time.time();random.seed(1729)

def status(stage,**data):
    REPORT.write_text(json.dumps(dict(stage=stage,elapsed_seconds=round(time.time()-START,2),**data),indent=2))

def material(name,color,rough=.45,metal=0,subsurface=0):
    m=bpy.data.materials.new('Explorer / '+name);m.use_nodes=True;m.diffuse_color=(*color,1)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    p.inputs['Subsurface Weight'].default_value=subsurface
    return m

def group(name,parent=None):
    o=bpy.data.objects.new(name,None);scene.collection.objects.link(o);o.parent=parent;return o

def mesh(name,verts,faces,mat,parent,smooth=True):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.parent=parent
    if mat:data.materials.append(mat)
    if smooth:
        for p in data.polygons:p.use_smooth=True
    return o

def sphere(name,loc,size,mat,parent,segments=48):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=24,location=loc)
    o=bpy.context.object;o.name=name;o.scale=size;o.parent=parent;o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    return o

def box(name,loc,size,mat,parent,bevel=.04,rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.name=name;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        b=o.modifiers.new('Tailored rounded edges','BEVEL');b.width=bevel;b.segments=3
        o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    o.rotation_euler=rotation;o.parent=parent;o.data.materials.append(mat);return o

def curve(name,points,r,mat,parent,closed=False,radii=None):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=r;data.bevel_resolution=2
    s=data.splines.new('POLY');s.points.add(len(points)-1)
    for i,(p,co) in enumerate(zip(s.points,points)):
        p.co=(*co,1)
        if radii:p.radius=radii[i]
    s.use_cyclic_u=closed
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.parent=parent;data.materials.append(mat)
    return o

def catmull(points,resolution=10):
    points=[Vector(p) for p in points];out=[]
    for i in range(len(points)-1):
        a=points[max(0,i-1)];b=points[i];c=points[i+1];d=points[min(len(points)-1,i+2)]
        for k in range(resolution):
            t=k/resolution
            out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    out.append(points[-1]);return out

def ribbon(name,points,width,depth,mat,parent):
    pts=catmull(points,12);verts=[];frames=[]
    for i,p in enumerate(pts):
        tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
        side=Vector((1,0,0));side=(side-tangent*side.dot(tangent)).normalized()
        normal=tangent.cross(side).normalized();frames.append((side,normal))
        verts.extend([tuple(p+side*width/2+normal*depth/2),tuple(p-side*width/2+normal*depth/2),
                      tuple(p-side*width/2-normal*depth/2),tuple(p+side*width/2-normal*depth/2)])
    faces=[]
    for i in range(len(pts)-1):
        for j in range(4):faces.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
    faces.extend([(3,2,1,0),tuple((len(pts)-1)*4+j for j in range(4))])
    return mesh(name,verts,faces,mat,parent),pts,frames

def panel(name,outline,y,depth,mat,parent,bevel=.025):
    N=len(outline);verts=[(x,y,z) for x,z in outline]+[(x,y+depth,z) for x,z in outline]
    faces=[tuple(reversed(range(N))),tuple(N+i for i in range(N))]
    faces += [(i,(i+1)%N,N+(i+1)%N,N+i) for i in range(N)]
    o=mesh(name,verts,faces,mat,parent,False)
    b=o.modifiers.new('Soft panel seams','BEVEL');b.width=bevel;b.segments=3
    o.modifiers.new('Panel normals','WEIGHTED_NORMAL');return o

def profile_at(z,profile):
    for a,b in zip(profile,profile[1:]):
        if a[0]<=z<=b[0]:
            t=(z-a[0])/(b[0]-a[0]);return tuple(a[i]*(1-t)+b[i]*t for i in range(1,len(a)))
    return profile[0][1:] if z<profile[0][0] else profile[-1][1:]

def gauss(x,z,cx,cz,sx,sz):return math.exp(-.5*(((x-cx)/sx)**2+((z-cz)/sz)**2))

HEAD_PROFILE=[(2.57,.10,.15,.15),(2.62,.34,.40,.29),(2.74,.54,.56,.41),
    (2.91,.70,.65,.50),(3.13,.82,.71,.58),(3.37,.91,.75,.66),
    (3.62,.955,.765,.72),(3.87,.95,.74,.76),(4.13,.935,.70,.77),
    (4.39,.90,.66,.73),(4.62,.79,.56,.64),(4.82,.59,.40,.48),
    (4.96,.30,.20,.25),(5.01,.025,.025,.025)]

def face_y(x,z):
    width,front,back=profile_at(z,HEAD_PROFILE)
    c=math.sqrt(max(.001,1-(x/width)**2))
    y=-front*c
    y-=.165*gauss(x,z,0,3.69,.125,.31)
    y-=.300*gauss(x,z,0,3.425,.150,.118)
    y-=.07*(gauss(x,z,-.17,3.40,.075,.095)+gauss(x,z,.17,3.40,.075,.095))
    y+=.095*(gauss(x,z,-.40,3.82,.26,.19)+gauss(x,z,.40,3.82,.26,.19))
    y-=.060*(gauss(x,z,-.51,3.48,.23,.19)+gauss(x,z,.51,3.48,.23,.19))
    y-=.045*gauss(x,z,0,3.08,.36,.15)
    return y

def ellipse_disk(name,cx,cz,rx,rz,y,bulge,mat,parent,segments=64,rings=10):
    verts=[(cx,y-bulge,cz)]
    for j in range(1,rings+1):
        r=j/rings
        for i in range(segments):
            a=math.tau*i/segments
            verts.append((cx+rx*r*math.cos(a),y-bulge*(1-r*r),cz+rz*r*math.sin(a)))
    faces=[(0,1+i,1+(i+1)%segments) for i in range(segments)]
    faces += [(1+(j-1)*segments+i,1+(j-1)*segments+(i+1)%segments,
        1+j*segments+(i+1)%segments,1+j*segments+i) for j in range(1,rings) for i in range(segments)]
    return mesh(name,verts,faces,mat,parent)

def hair_lock(name,controls,width,mat,grooves=4):
    pts=catmull(controls,8);N=10;verts=[];frames=[]
    for i,p in enumerate(pts):
        t=i/(len(pts)-1)
        tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
        normal=p-Vector((0,.10,4.05));normal=(normal-tangent*normal.dot(tangent)).normalized()
        side=tangent.cross(normal).normalized()
        r=width*(.36+.64*math.sin(math.pi*(.05+.9*t)))*max(.05,(1-t)**.35)
        frames.append((side,normal,r))
        for k in range(N):
            a=math.tau*k/N
            verts.append(tuple(p+side*r*math.cos(a)+normal*r*.53*math.sin(a)))
    faces=[(i*N+k,i*N+(k+1)%N,(i+1)*N+(k+1)%N,(i+1)*N+k) for i in range(len(pts)-1) for k in range(N)]
    faces += [tuple(reversed(range(N))),tuple((len(pts)-1)*N+k for k in range(N))]
    mesh(name,verts,faces,mat,hair)
    for j in range(grooves):
        a=.35+(math.pi-.70)*(j+.5)/grooves
        strand=[tuple(p+side*r*math.cos(a)+normal*r*.54*math.sin(a)) for p,(side,normal,r) in zip(pts,frames)]
        curve('Fine combed strand',strand,.0035,random.choice(hairtones),hair,
              radii=[.2+.8*math.sin(math.pi*(i+.5)/len(strand)) for i in range(len(strand))])

try:
    if SOURCE.exists() or MODEL.exists():raise FileExistsError('Choose a fresh output stem to preserve the previous character.')
    scene=bpy.data.scenes.new('Explorer / Reference Character Bust');bpy.context.window.scene=scene
    scene.unit_settings.system='METRIC'
    root=group('Explorer | reference character bust')
    head=group('Head | sculpted face ears and neck',root)
    eyes=group('Expression | eyes lids brows and smile',root)
    hair=group('Hair | swept chestnut curls',root)
    specs=group('Glasses | rectangular frames and temples',root)
    suit=group('Suit | cream shell orange trim and collar',root)
    gear=group('Gear | straps buckles backpack and communicator',root)
    skin=material('Warm skin',(.63,.32,.195),.47,subsurface=.07)
    skinrim=material('Eyelids and helix',(.61,.285,.175),.48,subsurface=.04)
    inner=material('Inner ear and nostril warmth',(.38,.115,.072),.6)
    lip=material('Natural rose lips',(.48,.17,.125),.43,subsurface=.035)
    mouth=material('Soft mouth and nostril shadow',(.10,.027,.018),.8)
    eye_white=material('Warm eye whites',(.90,.86,.77),.25)
    iris=material('Amber brown irises',(.25,.09,.025),.28)
    pupil=material('Deep brown pupils',(.005,.002,.001),.17)
    glint=material('Eye catchlights',(1,.97,.91),.15)
    cream=material('Warm ivory suit',(.78,.74,.66),.63)
    orange=material('Safety orange piping',(.95,.205,.025),.4)
    charcoal=material('Charcoal scarf and webbing',(.035,.034,.037),.85)
    web=material('Woven graphite harness',(.085,.083,.084),.75)
    graphite=material('Rubber and pocket edging',(.025,.025,.027),.58)
    metal=material('Brushed buckle metal',(.30,.29,.28),.3,.72)
    frame=material('Graphite glasses frames',(.035,.041,.046),.27,.65)
    stitch=material('Harness and suit topstitching',(.22,.21,.19),.75)
    hairtones=[material('Chestnut strand %02d'%i,c,.40) for i,c in enumerate([
        (.075,.022,.011),(.115,.035,.016),(.16,.047,.021),(.20,.065,.029),(.25,.085,.039),(.13,.035,.014)])]
    # Fine woven shading remains procedural in Blender; portable base colors are exported.
    for m in (cream,charcoal,web):
        nt=m.node_tree;n=nt.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=170
        coord=nt.nodes.new('ShaderNodeTexCoord');nt.links.new(coord.outputs['Object'],n.inputs['Vector'])
        b=nt.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=.13;b.inputs['Distance'].default_value=.008
        nt.links.new(n.outputs['Fac'],b.inputs['Height'])
        nt.links.new(b.outputs[0],next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED').inputs['Normal'])

    status('Sculpting continuous facial features')
    N=160;R=176;verts=[]
    for j in range(R+1):
        z=2.57+(5.01-2.57)*j/R;width,front,back=profile_at(z,HEAD_PROFILE)
        for i in range(N):
            a=math.tau*i/N;c=math.cos(a);x=width*math.sin(a)
            y=face_y(x,z) if c>=0 else -back*c
            verts.append((x,y,z))
    fs=[(j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i) for j in range(R) for i in range(N)]
    fs += [tuple(reversed(range(N))),tuple(R*N+i for i in range(N))]
    sculpt=mesh('Continuous sculpted head and nose',verts,fs,skin,head)
    colors=sculpt.data.color_attributes.new(name='SkinColor',type='FLOAT_COLOR',domain='CORNER')
    for loop in sculpt.data.loops:
        x,y,z=sculpt.data.vertices[loop.vertex_index].co
        blush=(gauss(x,z,-.53,3.45,.25,.17)+gauss(x,z,.53,3.45,.25,.17)+.5*gauss(x,z,0,3.43,.19,.18))*max(0,min(1,-y/.6))
        colors.data[loop.index].color=(.63+.035*blush,.32-.018*blush,.195-.010*blush,1)
    sculpt.data.color_attributes.active_color=colors
    attr=skin.node_tree.nodes.new('ShaderNodeVertexColor');attr.layer_name='SkinColor'
    skin.node_tree.links.new(attr.outputs['Color'],next(n for n in skin.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Base Color'])
    # Separate neck material: the face vertex-color layer is not required on other skin parts.
    skinplain=material('Neck and ear skin',(.63,.32,.195),.47,subsurface=.07)
    sphere('Tapered exposed neck',(0,.10,2.39),(.36,.34,.63),skinplain,head)
    for sx in (-1,1):
        sphere('Ear pinna',(sx*.985,.045,3.57),(.18,.13,.30),skinplain,head)
        sphere('Ear concha',(sx*1.018,-.075,3.58),(.092,.025,.195),inner,head,32)
        curve('Ear outer helix',[(sx*(.995+.12*math.cos(a)),-.09,3.58+.25*math.sin(a)) for a in [math.tau*i/60 for i in range(61)]],.032,skinrim,head)
        curve('Ear inner cartilage',[(sx*1.03,-.112,3.42),(sx*1.07,-.12,3.53),(sx*1.00,-.118,3.69),(sx*1.04,-.11,3.76)],.025,skinplain,head)
        sphere('Nostril recess',(sx*.115,face_y(sx*.115,3.355)-.007,3.355),(.039,.012,.018),mouth,head,32)

    status('Modeling eyes lips and eyeglasses')
    irisattr=iris.node_tree.nodes.new('ShaderNodeVertexColor');irisattr.layer_name='IrisColor'
    iris.node_tree.links.new(irisattr.outputs['Color'],next(n for n in iris.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Base Color'])
    for sx,label in [(-1,'Left'),(1,'Right')]:
        cx=sx*.405;cz=3.835
        ellipse_disk(label+' almond eye white',cx,cz,.274,.173,-.715,.135,eye_white,eyes)
        ellipse_disk(label+' brown iris',cx+.012,cz-.005,.108,.127,-.85,.018,iris,eyes)
        io=bpy.context.scene.objects[label+' brown iris']
        colors=io.data.color_attributes.new(name='IrisColor',type='FLOAT_COLOR',domain='CORNER')
        for loop in io.data.loops:
            v=io.data.vertices[loop.vertex_index].co;a=math.atan2((v.z-cz)/.127,(v.x-cx-.012)/.108)
            r=math.hypot((v.x-cx-.012)/.108,(v.z-cz)/.127)
            f=(.72+.28*max(0,-math.sin(a)))*(.75+.25*math.sin(49*a)**2)*(.4 if r>.92 else 1)
            colors.data[loop.index].color=(.30*f,.115*f,.028*f,1)
        io.data.color_attributes.active_color=colors
        sphere(label+' pupil',(cx+.012,-.876,cz+.005),(.058,.012,.075),pupil,eyes,32)
        sphere(label+' catchlight',(cx-.018,-.894,cz+.054),(.022,.008,.024),glint,eyes,24)
        sphere(label+' small catchlight',(cx+.05,-.886,cz-.039),(.009,.005,.009),glint,eyes,20)
        for upper in (True,False):
            pts=[]
            for k in range(50):
                t=-1+2*k/49;x=cx+.278*t
                z=cz+(1 if upper else -1)*(.175 if upper else .151)*max(0,1-t*t)**.64
                pts.append((x,-.726-.04*(1-t*t),z))
            curve(label+(' upper eyelid' if upper else ' lower eyelid'),pts,.022 if upper else .017,skinrim,eyes)
            if upper:curve(label+' fine upper lash line',[(x,y-.006,z-.009) for x,y,z in pts],.006,hairtones[0],eyes)
        browpts=[]
        for k in range(30):
            t=k/29;x=cx-.285+.57*t;z=4.145+.063*math.sin(math.pi*t)-sx*.025*(t-.5)
            browpts.append((x,face_y(x,z)-.022,z))
        curve(label+' expressive eyebrow',browpts,.049,hairtones[1],eyes,
            radii=[.25+.75*math.sin(math.pi*(i+.5)/30)**.35 for i in range(30)])
        for k in range(22):
            t=k/21;x=cx-.26+.52*t;z=4.145+.063*math.sin(math.pi*t)
            curve('Individual eyebrow hair',[(x,face_y(x,z)-.055,z-.02),(x+sx*.025,face_y(x,z)-.059,z+.035)],.004,hairtones[k%3],eyes)
        # Softly rectangular, not round, spectacle rims.
        pts=[]
        for i in range(112):
            a=math.tau*i/112
            x=cx+.357*math.copysign(abs(math.cos(a))**.55,math.cos(a))
            z=cz+.235*math.copysign(abs(math.sin(a))**.55,math.sin(a))
            pts.append((x,-.958+.055*(abs(x)/.8)**2,z))
        curve(label+' rectangular glasses rim',pts,.016,frame,specs,True)
        curve(label+' glasses temple',catmull([(sx*.755,-.91,3.94),(sx*.85,-.68,3.97),(sx*.965,-.24,3.93),(sx*.97,.08,3.77)],10),.025,frame,specs)
        box(label+' glasses hinge',(sx*.79,-.83,3.95),(.055,.10,.045),metal,specs,.01)
        sphere(label+' nose pad',(sx*.075,-.889,3.80),(.025,.025,.045),metal,specs,24)
    curve('Glasses arched bridge',catmull([(-.067,-.96,3.94),(-.036,-.973,3.975),(.036,-.973,3.975),(.067,-.96,3.94)],10),.017,frame,specs)
    # Sculpted lips taper at the corners and follow a small, asymmetric smile.
    for upper in (True,False):
        vs=[];steps=64
        for j in range(5):
            r=j/4
            for i in range(steps+1):
                x=-.32+.64*i/steps;t=x/.32;base=3.065+.067*abs(t)**1.8+.007*t
                thickness=(.030 if upper else -.043)*max(0,1-t*t)**.75
                if upper:thickness+=.012*math.exp(-((abs(t)-.26)/.18)**2)
                z=base+thickness*r;y=face_y(x,z)-.006-.023*math.sin(math.pi*r)*max(0,1-t*t)
                vs.append((x,y,z))
        fs=[(j*(steps+1)+i,j*(steps+1)+i+1,(j+1)*(steps+1)+i+1,(j+1)*(steps+1)+i) for j in range(4) for i in range(steps)]
        mesh('Upper lip cupid bow' if upper else 'Soft lower lip',vs,fs,lip,eyes)
    curve('Gentle closed smile',[(x,face_y(x,3.065+.067*abs(x/.32)**1.8)-.012,3.065+.067*abs(x/.32)**1.8+.007*x/.32)
        for x in [-.32+.64*i/64 for i in range(65)]],.007,mouth,eyes)

    status('Grooming swept chestnut curls and fine strands')
    N=96;R=30;vs=[]
    for j in range(R+1):
        for i in range(N):
            theta=math.tau*i/N;front=(1+math.cos(theta))/2
            limit=2.56-1.21*front+.045*math.sin(theta*7)
            phi=.008+limit*j/R
            vs.append((1.005*math.sin(phi)*math.sin(theta),.1-.815*math.sin(phi)*math.cos(theta),4.05+.99*math.cos(phi)))
    fs=[(j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i) for j in range(R) for i in range(N)]
    mesh('Chestnut scalp and swept hairline',vs,fs,hairtones[0],hair)
    for row in range(3):
        for col in range(6):
            x=-.90+col*.34;variation=random.uniform(-.045,.045)
            controls=[(x*.8,.19+row*.10,4.86+.18*(1-abs(x))),
                (x-.10,-.015,5.32+row*.045+variation),(x-.24,-.40,5.20-row*.04),
                (x-.20,-.70,4.99-row*.11),(x+.12,-.84,4.84-row*.16),
                (x+.16,-.86,4.65-row*.16),(x+.06,-.83,4.59-row*.16)]
            hair_lock('Sculpted swept front curl',controls,.14+random.uniform(-.015,.025),hairtones[(row+col)%5],5)
    for i in range(25):
        theta=.76+(math.tau-1.52)*i/24
        controls=[]
        end=2.14+.40*max(0,-math.cos(theta))
        for k in range(7):
            t=k/6;phi=.55+(end-.55)*t;a=theta+.17*math.sin(t*math.tau)
            rr=1.02+.055*math.sin(math.pi*t)
            controls.append((rr*math.sin(phi)*math.sin(a),.10-.84*math.sin(phi)*math.cos(a),4.05+1.04*math.cos(phi)))
        hair_lock('Side and rear wavy hair lock',controls,.115,random.choice(hairtones[:5]),3)
    for sx in (-1,1):
        hair_lock('Tapered sideburn',[(sx*.86,-.20,4.08),(sx*.94,-.19,3.94),(sx*.94,-.18,3.73),(sx*.91,-.18,3.61)],.075,hairtones[0],3)

    status('Tailoring ivory and orange explorer suit')
    profile=[(0,1.28,.49),( .35,1.38,.51),(.85,1.43,.54),(1.35,1.39,.56),
        (1.67,1.23,.52),(1.9,.88,.46),(2.07,.53,.38)]
    N=96;R=70;vs=[]
    for j in range(R+1):
        z=2.07*j/R;rx,ry=profile_at(z,profile)
        for i in range(N):
            a=math.tau*i/N;vs.append((rx*math.sin(a),.08-ry*math.cos(a),z))
    fs=[(j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i) for j in range(R) for i in range(N)]
    fs += [tuple(reversed(range(N))),tuple(R*N+i for i in range(N))]
    mesh('Tailored cream jacket torso',vs,fs,cream,suit)
    for sx in (-1,1):
        o=sphere('Rounded suit shoulder',(sx*1.26,.10,1.22),(.60,.51,.76),cream,suit,64)
        o.data.materials.append(orange)
        for p in o.data.polygons:
            c=p.center
            if .03<sx*c.x<.57 and c.z>.25 and c.y<.05:p.material_index=1
        sphere('Upper sleeve bust segment',(sx*1.50,.12,.48),(.48,.47,.64),cream,suit)
        curve('Sleeve articulation seam',[(sx*(1.1+.7*t),-.32-.05*math.sin(math.pi*t),.69-.12*t) for t in [i/40 for i in range(41)]],.012,stitch,suit)
    # Black undersuit and scarf folds inside the high, open collar.
    sphere('Black turtleneck',(0,.06,2.11),(.42,.39,.39),charcoal,suit)
    panel('Visible scarf V',[(-.34,1.99),(.34,1.99),(.15,1.27),(0,1.08),(-.17,1.29)],-.54,.055,charcoal,suit)
    for j in range(3):
        curve('Soft scarf fold',catmull([(-.34,-.39,2.11-j*.13),(-.11,-.46,2.06-j*.13),(.19,-.45,2.04-j*.13),(.35,-.35,2.10-j*.13)],10),.025,charcoal,suit)
    # Double-walled standing collar, opening at the front.
    count=110;vs=[]
    for r in (.58,.69):
        for upper in (False,True):
            for i in range(count+1):
                a=.54+(math.tau-1.08)*i/count
                z=(2.37+.07*(-math.cos(a))) if upper else 1.69
                vs.append((r*math.sin(a),.05-r*.78*math.cos(a),z))
    stride=count+1;fs=[]
    for r in range(2):
        fs += [(r*2*stride+i,r*2*stride+i+1,r*2*stride+stride+i+1,r*2*stride+stride+i) for i in range(count)]
    fs += [(stride+i,stride+i+1,3*stride+i+1,3*stride+i) for i in range(count)]
    collar=mesh('Raised double-wall jacket collar',vs,fs,cream,suit)
    collar.data.materials.append(charcoal)
    for p in collar.data.polygons:
        if p.index<count:p.material_index=1
    for i in range(2):
        a=.54 if i==0 else math.tau-.54
        curve('Collar front closure piping',[(.69*math.sin(a),.05-.69*.78*math.cos(a),z) for z in [1.69,2.05,2.37-.07*math.cos(a)]],.018,orange,suit)
    curve('Orange collar rim',[(.692*math.sin(a),.05-.692*.78*math.cos(a),2.37-.07*math.cos(a))
        for a in [.54+(math.tau-1.08)*i/count for i in range(count+1)]],.020,orange,suit)
    for sx in (-1,1):
        panel('Dark collar lapel insert',[(sx*.34,1.68),(sx*.58,1.5),(sx*.34,.97),(sx*.16,1.22)],-.51,.045,web,suit,.03)
        curve('Jacket diagonal tailoring seam',catmull([(sx*.40,-.46,1.83),(sx*.73,-.44,1.48),(sx*.92,-.41,1.10)],10),.009,stitch,suit)
    box('Collar orange fastening tab',(-.39,-.46,1.99),(.18,.10,.25),orange,suit,.025)
    box('Dark central zipper tape',(0,-.487,.60),(.065,.03,1.20),graphite,suit,.012)
    for i in range(24):
        z=.03+i*.048
        for sx in (-1,1):box('Zipper tooth',(sx*.018,-.511,z),(.022,.018,.021),metal,suit,.004)
    box('Zipper slider',(0,-.535,1.08),(.075,.04,.105),metal,suit,.018)
    box('Zipper pull',(0,-.558,1.00),(.045,.02,.12),graphite,suit,.012)

    status('Adding harness buckles and chest equipment')
    box('Compact backpack',(0,.67,1.03),(1.40,.57,1.63),web,gear,.20)
    for sx in (-1,1):
        box('Backpack orange side rail',(sx*.68,.86,1.08),(.11,.13,1.31),orange,gear,.045)
        controls=[(sx*.91,.46,1.85),(sx*1.06,.08,1.90),(sx*1.04,-.38,1.66),
            (sx*1.02,-.54,1.20),(sx*.96,-.51,.62),(sx*.90,-.49,.03)]
        strap,pts,frames=ribbon('Wide graphite shoulder webbing',controls,.26,.047,web,gear)
        for side in (-1,1):
            curve('Harness edge stitching',[tuple(p+f[0]*side*.108+Vector((0,-.026,0))) for p,f in zip(pts,frames)],.005,stitch,gear)
        bx=sx*1.015;z=1.27
        outline=[]
        for k in range(72):
            a=math.tau*k/72
            x=bx+.165*math.copysign(abs(math.cos(a))**.5,math.cos(a))
            zz=z+.115*math.copysign(abs(math.sin(a))**.5,math.sin(a))
            outline.append((x,-.607,zz))
        curve('Metal harness buckle',outline,.024,metal,gear,True)
        box('Harness buckle center bar',(bx,-.615,z),(.26,.035,.028),graphite,gear,.01)
    box('Chest communicator orange casing',(.59,-.56,.57),(.22,.16,.53),orange,gear,.05,rotation=(0,-.11,0))
    box('Communicator dark display',(.59,-.652,.64),(.15,.026,.27),graphite,gear,.025)
    box('Communicator belt clip',(.48,-.63,.53),(.065,.075,.29),metal,gear,.018)
    box('Chest equipment pocket',(.63,-.55,.19),(.39,.15,.33),cream,suit,.045)
    curve('Pocket rolled upper edge',[(.43,-.64,.36),(.63,-.65,.35),(.83,-.64,.36)],.012,cream,suit)

    root.scale=(.28,.28,.28);root['reference']='User-supplied portrait: brown curls, glasses, cream/orange explorer suit'
    root['scope']='Static upper-body character bust; rear surfaces interpreted procedurally'
    bpy.context.view_layer.update()
    status('Lighting portrait studio and exporting master')
    world=bpy.data.worlds.new('Explorer / portrait studio');world.use_nodes=True;scene.world=world
    bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.80,.84,.90,1);bg.inputs[1].default_value=.35
    def area(name,loc,energy,size,color):
        bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name
        o.data.energy=energy;o.data.size=size;o.data.shape='DISK';o.data.color=color
        o.rotation_euler=(Vector((0,0,.85))-o.location).to_track_quat('-Z','Y').to_euler()
    area('Large warm portrait key',(-2.8,-3,3.4),220,2.7,(1,.86,.73))
    area('Soft neutral portrait fill',(2.3,-2.4,2.0),95,2.6,(.80,.89,1))
    area('Warm hair separation light',(.5,2.0,3.2),300,2,(1,.71,.48))
    bpy.ops.object.camera_add(location=(-1.05,-4.6,1.73));camera=bpy.context.object;camera.name='Explorer portrait camera'
    target=Vector((0,0,.79));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=1.69;scene.camera=camera
    scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
    scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
    scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.1
    for screen in bpy.data.screens:
        for a in screen.areas:
            if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA'
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
    objects=set()
    def visit(o):
        objects.add(o)
        for child in o.children:visit(child)
    visit(root);bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(MODEL),export_format='GLB',use_selection=True,use_active_scene=True,
        export_apply=True,export_yup=True,export_cameras=False,export_lights=False)
    deps=bpy.context.evaluated_depsgraph_get();tris=0;coords=[]
    for o in objects:
        if o.type in {'MESH','CURVE'}:
            ev=o.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();tris+=len(me.loop_triangles)
            coords += [o.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
    lo=[min(p[i] for p in coords) for i in range(3)];hi=[max(p[i] for p in coords) for i in range(3)]
    stats=dict(source=str(SOURCE),model=str(MODEL),preview=str(PREVIEW),back_preview=str(BACK),
        model_nodes=len(objects),triangles=tris,dimensions_meters=[round(hi[i]-lo[i],4) for i in range(3)],
        units='meters',gltf_up_axis='Y',animation_clips=[],external_assets=[],
        scope='Stylized editable character bust inspired by the supplied portrait',
        note='Procedural interpretation rather than an exact likeness; detailed master for visual review')
    status('Rendering front portrait',**stats)
    scene.render.filepath=str(PREVIEW);bpy.ops.render.render(write_still=True)
    status('Rendering rear three-quarter portrait',**stats)
    loc=camera.location.copy();rot=camera.rotation_euler.copy()
    camera.location=(1.55,3.5,1.75);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.resolution_x=800;scene.render.resolution_y=1000;scene.render.filepath=str(BACK)
    bpy.ops.render.render(write_still=True)
    camera.location=loc;camera.rotation_euler=rot;scene.render.resolution_x=1200;scene.render.resolution_y=1400
    scene.render.filepath=str(PREVIEW);bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
    status('Complete',**stats)
except Exception:
    status('Failed',traceback=traceback.format_exc())
    raise
