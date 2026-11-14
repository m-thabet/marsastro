"""Build an editable Mars outpost inspired by the user's supplied reference.

Run in Blender 5.3. Creates its own scene and never deletes existing scenes.
No image-generation services, downloaded models, or application code are used.
"""
import bpy
import json
import math
import random
import time
import traceback
from pathlib import Path
from mathutils import Vector, noise

ASSETS = Path(__file__).resolve().parents[1]
STEM = 'mars-reference-outpost'
SOURCE = ASSETS / 'source' / (STEM + '.blend')
EXPORT = ASSETS / 'world' / (STEM + '.glb')
PREVIEW = ASSETS / 'previews' / (STEM + '.png')
REPORT = ASSETS / 'previews' / (STEM + '-report.json')
random.seed(3107)
START = time.time()
for folder in (SOURCE.parent, EXPORT.parent, PREVIEW.parent):
    folder.mkdir(parents=True, exist_ok=True)


def status(stage, **extra):
    REPORT.write_text(json.dumps(dict(stage=stage, elapsed_seconds=round(time.time()-START, 1), **extra), indent=2))


def mat(name, color, metallic=0, rough=.55, emission=0, alpha=1, transmission=0):
    m = bpy.data.materials.new('Outpost / ' + name)
    m.diffuse_color = (*color, alpha)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, alpha)
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = rough
    p.inputs['Alpha'].default_value = alpha
    p.inputs['Transmission Weight'].default_value = transmission
    if emission:
        p.inputs['Emission Color'].default_value = (*color, 1)
        p.inputs['Emission Strength'].default_value = emission
    if alpha < 1:
        m.surface_render_method = 'DITHERED'
    return m


def assign(o, name, material, root=None, smooth=False):
    o.name = name
    if material:
        o.data.materials.append(material)
    if root:
        o.parent = root
    if smooth and o.type == 'MESH':
        for p in o.data.polygons:
            p.use_smooth = True
    return o


def group(name):
    o = bpy.data.objects.new(name, None)
    scene.collection.objects.link(o)
    o['asset_role'] = name
    return o


def box(name, loc, size, material, root=None, bevel=.08, rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        b = o.modifiers.new('Rounded manufactured edges', 'BEVEL')
        b.width = bevel
        b.segments = 2
        o.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
    if rotation:
        o.rotation_euler = rotation
    return assign(o, name, material, root)


def cyl(name, loc, radius, depth, material, root=None, vertices=32, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    o = bpy.context.object
    if rotation:
        o.rotation_euler = rotation
    return assign(o, name, material, root, True)


def sphere(name, loc, scale, material, root=None, segments=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=12, location=loc)
    o = bpy.context.object
    o.scale = scale
    return assign(o, name, material, root, True)


def mesh(name, vertices, faces, material, root=None, smooth=False):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    o = bpy.data.objects.new(name, data)
    scene.collection.objects.link(o)
    return assign(o, name, material, root, smooth)


def line(name, points, radius, material, root=None, closed=False):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.resolution_u = 1
    data.bevel_depth = radius
    data.bevel_resolution = 2
    s = data.splines.new('POLY')
    s.points.add(len(points)-1)
    for p, co in zip(s.points, points):
        p.co = (*co, 1)
    s.use_cyclic_u = closed
    o = bpy.data.objects.new(name, data)
    scene.collection.objects.link(o)
    return assign(o, name, material, root)


def rod(name, a, b, radius, material, root=None, vertices=12):
    a, b = Vector(a), Vector(b)
    o = cyl(name, (a+b)/2, radius, (b-a).length, material, root, vertices)
    o.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    return o


def ring(name, center, radius, tube, material, root=None, rotation=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=tube,
                                   major_segments=48, minor_segments=8, location=center)
    o = bpy.context.object
    if rotation:
        o.rotation_euler = rotation
    return assign(o, name, material, root, True)


def label(text, loc, size, material, root, rotation=(math.pi/2, 0, 0)):
    data = bpy.data.curves.new('Decal ' + text, 'FONT')
    data.body = text
    data.align_x = 'CENTER'
    data.size = size
    data.extrude = .001
    o = bpy.data.objects.new('Decal ' + text, data)
    scene.collection.objects.link(o)
    o.location, o.rotation_euler = loc, rotation
    return assign(o, o.name, material, root)


def deck(x, y, sx, sy, root):
    box('Landing / foundation slab', (x, y, .15), (sx, sy, .3), stone, root, .25)
    box('Foundation upper surface', (x, y, .32), (sx-.4, sy-.4, .08), trim, root, .15)


def antenna(x, y, z, root, h=2.8):
    cyl('Antenna foot', (x, y, z), .18, .15, dark, root)
    rod('Antenna mast', (x, y, z), (x, y, z+h), .035, metal, root)
    cyl('Antenna collar', (x, y, z+h*.65), .075, .18, shell, root)
    sphere('Antenna tip', (x, y, z+h), (.065, .065, .065), amber, root, 12)


def airlock(x, y, z, root, text='01'):
    box('Airlock reinforced outer shell', (x, y, z+1.15), (2.25, 1.25, 2.8), shell, root, .45)
    box('Airlock charcoal gasket', (x, y-.648, z+1.05), (1.52, .08, 2.1), dark, root, .28)
    box('Airlock inset door', (x, y-.70, z+1.03), (1.2, .06, 1.83), trim, root, .18)
    box('Airlock window', (x, y-.747, z+1.42), (.76, .025, .45), window, root, .08)
    box('Airlock status', (x+.88, y-.70, z+1.35), (.1, .06, .35), mint, root, .03)
    label(text, (x, y-.75, z+2.2), .23, dark, root)
    for i in range(3):
        box('Entrance steps', (x, y-1-i*.35, z-.02-i*.13), (2.25, .85, .25), trim, root, .04)
    for sign in (-1, 1):
        rod('Entrance rail', (x+sign*1.1, y-.8, z+.8), (x+sign*1.1, y-2, z+.45), .045, metal, root)


def crate(x, y, z=0, scale=1):
    box('Supply crate', (x, y, z+.53*scale), (scale, scale*.82, scale), shell, props, .07)
    for sx in (-1, 1):
        box('Crate corner reinforcement', (x+sx*.4*scale, y-.424*scale, z+.53*scale), (.12*scale, .035, .82*scale), trim, props, .015)
    box('Crate recess', (x, y-.434*scale, z+.53*scale), (.3*scale, .02, .23*scale), dark, props, .03)
    box('Crate yellow seal', (x+.24*scale, y-.45*scale, z+.8*scale), (.12*scale, .025, .1*scale), orange, props, .01)


def tunnel(a, b):
    a, b = Vector(a), Vector(b)
    root = connectors
    rod('Pressurized connecting tunnel', a, b, .95, trim, root, 24)
    direction = (b-a).normalized()
    length = (b-a).length
    for i in range(int(length/.8)+1):
        p = a+direction*(i/max(1,int(length/.8)))*length
        o = ring('Tunnel compression hoop', p, .98, .10, shell, root)
        o.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    rod('Tunnel crown conduit', a+Vector((0,0,.97)), b+Vector((0,0,.97)), .06, orange, root)


def lathe(name, x, y, profile, material, root, segments=64):
    verts = [(x+r*math.cos(a*math.tau/segments), y+r*math.sin(a*math.tau/segments), z)
             for r,z in profile for a in range(segments)]
    faces = [(j*segments+i, j*segments+(i+1)%segments, (j+1)*segments+(i+1)%segments, (j+1)*segments+i)
             for j in range(len(profile)-1) for i in range(segments)]
    faces += [tuple(reversed(range(segments))), tuple((len(profile)-1)*segments+i for i in range(segments))]
    return mesh(name, verts, faces, material, root, True)


def round_windows(x, y, r, z, root, count=18, height=1.05, width=.74, material=None):
    for i in range(count):
        angle = math.tau*i/count
        pos = (x+r*math.sin(angle), y-r*math.cos(angle), z)
        o = box('Window dark frame', pos, (width+.17,.12,height+.15), dark, root, .08)
        o.rotation_euler.z = angle
        pos = (x+(r+.074)*math.sin(angle), y-(r+.074)*math.cos(angle), z)
        o = box('Window pane', pos, (width,.05,height), material or window, root, .05)
        o.rotation_euler.z = angle


try:
    if SOURCE.exists() or EXPORT.exists():
        raise FileExistsError('Output exists. Choose a new STEM to preserve the previous scene.')
    status('Creating materials')
    scene = bpy.data.scenes.new('Mars / Reference Outpost')
    bpy.context.window.scene = scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1
    shell = mat('Warm ceramic hull', (.79,.72,.59), .18, .32)
    roofmat = mat('Clean roof panels', (.91,.84,.70), .1, .36)
    trim = mat('Titanium frame', (.33,.38,.38), .55, .4)
    dark = mat('Graphite seals', (.055,.075,.08), .35, .47)
    metal = mat('Brushed aluminium', (.58,.65,.65), .8, .28)
    orange = mat('Safety ochre', (.84,.31,.065), .3, .42)
    window = mat('Blue laboratory glazing', (.19,.48,.56), .3,.16, .1)
    warmwindow = mat('Habitat amber glazing', (1,.39,.065), .15,.25, 1.4)
    glass = mat('Greenhouse transparent glass', (.57,.79,.82), .06,.12, alpha=.19, transmission=.18)
    mint = mat('Cyan power status', (.19,.88,1), .1,.25, 3)
    amber = mat('Amber indicator', (1,.32,.035), .1,.3, 2)
    blue = mat('Photovoltaic cobalt', (.025,.10,.245), .45,.24)
    cellgrid = mat('Solar cell silver traces', (.32,.49,.62), .6,.4)
    soil = mat('Terracotta sand', (.49,.135,.045), rough=.88)
    stone = mat('Red sandstone', (.38,.092,.032), rough=.91)
    rockmats = [mat('Sandstone stratum %d'%i, c, rough=.91) for i,c in enumerate([
        (.47,.12,.045),(.55,.17,.064),(.62,.22,.085),(.42,.102,.04),(.58,.19,.065)])]
    roadmat = mat('Compacted ochre paths', (.58,.198,.075), rough=.96)
    trackmat = mat('Wheel impressions', (.35,.095,.034), rough=1)
    leaves = [mat('Green foliage %d'%i, c, rough=.75) for i,c in enumerate([
        (.13,.29,.032),(.25,.43,.046),(.37,.52,.07)])]
    greenbed = mat('Hydroponic growing medium', (.10,.14,.046), rough=.9)
    tire = mat('Rover rubber wheels', (.025,.03,.03), rough=.85)

    # Ground material with fine procedural roughness, rather than a flat orange plane.
    nt = soil.node_tree
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 3.8
    n.inputs['Detail'].default_value = 4
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .2
    ramp.color_ramp.elements[0].color = (.28,.055,.016,1)
    ramp.color_ramp.elements[1].position = .8
    ramp.color_ramp.elements[1].color = (.66,.23,.085,1)
    nt.links.new(n.outputs['Fac'],ramp.inputs[0])
    nt.links.new(ramp.outputs[0],nt.nodes.get('Principled BSDF').inputs['Base Color'])
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.19
    bump.inputs['Distance'].default_value=.13
    nt.links.new(n.outputs['Fac'],bump.inputs['Height'])
    nt.links.new(bump.outputs[0],nt.nodes.get('Principled BSDF').inputs['Normal'])

    terrain = group('Terrain | illustrative Mars landscape')
    props = group('Props | logistics and rocks')
    connectors = group('Connectors | pressurized passageways')
    status('Sculpting terrain and mesas')
    N = 126
    verts=[]
    for j in range(N+1):
        y=-95+j*255/N
        for i in range(N+1):
            x=-145+i*290/N
            distance = math.sqrt((x/1.2)**2+(y-5)**2)
            amplitude = .10+min(2.4,max(0,(distance-38)/24))
            z = -.18 + amplitude*noise.fractal(Vector((x*.05,y*.05,1.2)),1.0,2,3)
            verts.append((x,y,z))
    faces=[(j*(N+1)+i,j*(N+1)+i+1,(j+1)*(N+1)+i+1,(j+1)*(N+1)+i) for j in range(N) for i in range(N)]
    mesh('Continuous undulating terrain',verts,faces,soil,terrain,True)

    def mesa(x,y,r,h):
        seg=36
        phases=[random.uniform(.85,1.18) for _ in range(seg)]
        vs=[]
        for k,(height,rad) in enumerate([(0,1.65),(.08,1.5),(.22,1.24),(.40,1.05),(.52,1.03),(.73,.85),(.93,.77),(1,.7)]):
            for i in range(seg):
                a=math.tau*i/seg
                rr=r*rad*phases[i]*(1+.045*math.sin(i*3+k))
                vs.append((x+rr*math.cos(a),y+rr*math.sin(a),-.3+height*h+random.uniform(-.2,.2)))
        fs=[(k*seg+i,k*seg+(i+1)%seg,(k+1)*seg+(i+1)%seg,(k+1)*seg+i) for k in range(7) for i in range(seg)]
        fs.append(tuple(7*seg+i for i in range(seg)))
        o=mesh('Eroded layered mesa',vs,fs,rockmats[0],terrain)
        for m in rockmats[1:]:o.data.materials.append(m)
        for p in o.data.polygons:p.material_index=(p.index//seg+random.choice([0,0,1]))%len(rockmats)
        # Broken rock scree at the foot makes the silhouette less geometric.
        for i in range(9):
            a=random.uniform(0,math.tau)
            rock(x+math.cos(a)*r*1.35,y+math.sin(a)*r*1.35,random.uniform(.6,1.9),terrain)

    rock_meshes=[]
    for k in range(6):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1)
        o=bpy.context.object
        for v in o.data.vertices:
            v.co *= random.uniform(.76,1.25)
            v.co.z=max(-.3,v.co.z)
        o.data.materials.append(rockmats[k%5])
        rock_meshes.append(o.data)
        bpy.data.objects.remove(o,do_unlink=True)
    def rock(x,y,s,root=props):
        o=bpy.data.objects.new('Weathered sandstone boulder',random.choice(rock_meshes))
        scene.collection.objects.link(o);o.parent=root
        o.location=(x,y,s*.23-.1)
        o.scale=(s*random.uniform(.8,1.5),s*random.uniform(.7,1.1),s*random.uniform(.65,1.1))
        o.rotation_euler.z=random.uniform(0,math.tau)
        return o

    for args in [(-58,50,16,17),(-38,76,16,15),(46,59,19,19),(76,81,23,17),
                 (-86,93,22,23),(0,92,12,11),(25,117,20,15),(-61,139,28,18),
                 (79,137,30,19),(-67,-3,13,10),(66,8,13,10)]:mesa(*args)
    for _ in range(390):
        x,y=random.uniform(-80,85),random.uniform(-40,105)
        if -38<x<38 and -24<y<37:continue
        rock(x,y,random.choices([random.uniform(.10,.45),random.uniform(.5,1.4),random.uniform(2,4)],[.68,.27,.05])[0])
    for x,y,s in [(-37,-24,4.1),(-31,-32,2.6),(42,-24,3.7),(51,-31,5),(-47,3,3.8),(4,-21,1.9)]:rock(x,y,s)
    # A continuous looping drive with two wheel ruts; curves stay separate from terrain.
    path=[]
    for i in range(105):
        a=math.tau*i/104
        path.append((5+39*math.cos(a),4+27*math.sin(a),.01))
    road = line('Compacted loop road',path,1.15,roadmat,terrain,True)
    road.scale.z = .035
    for d in (-.55,.55):
        pts=[(5+(39+d)*math.cos(math.tau*i/104),4+(27+d)*math.sin(math.tau*i/104),.075) for i in range(105)]
        line('Rover wheel rut',pts,.035,trackmat,terrain,True)

    status('Building habitat, command tower and connecting modules')
    habitat=group('Habitat | warm residential dome')
    hx,hy=-20,9
    deck(hx,hy,14,13,habitat)
    lathe('Habitat segmented pressure hull',hx,hy,[(5.7,.5),(5.9,1.2),(5.5,2.4),(4.6,3.9),(3.1,4.9),(2.4,5.15)],shell,habitat)
    for r,z in [(5.75,.8),(5.2,3),(2.45,5.13)]:ring('Habitat horizontal hull seam',(hx,hy,z),r,.055,trim,habitat)
    cyl('Habitat roof cap',(hx,hy,5.13),2.4,.20,trim,habitat)
    ring('Roof amber perimeter',(hx,hy,5.25),2.05,.035,amber,habitat)
    round_windows(hx,hy,5.58,2.12,habitat,18,1.02,1.05,warmwindow)
    for i in range(12):
        a=math.tau*i/12
        pts=[(hx+r*math.cos(a),hy+r*math.sin(a),z+.02) for r,z in [(5.85,.75),(5.65,1.8),(4.6,3.9),(3.1,4.9),(2.4,5.2)]]
        line('Habitat radial roof panel joint',pts,.025,trim,habitat)
        box('Habitat anchoring foot',(hx+6*math.cos(a),hy+6*math.sin(a),.6),(.65,.65,.6),trim,habitat,.08)
    airlock(hx,hy-5.4,.5,habitat,'HAB / 01')
    antenna(hx+.6,hy,5.3,habitat,2.2)

    command=group('Command | communications tower')
    x,y=-17,23
    deck(x,y,9,8,command)
    box('Command lower module',(x,y,2),(8,6,3.4),shell,command,.8)
    box('Command roof',(x,y,3.9),(8.2,6.2,.35),roofmat,command,.35)
    for xx in (-2.5,0,2.5):box('Command window',(x+xx,y-3.05,2.3),(1.25,.08,.9),warmwindow,command,.13)
    box('Tapered communications tower',(x+1.5,y+1,6.1),(3.6,3.2,6.5),shell,command,.5)
    for z in (5,7.1,8.5):box('Tower equipment slot',(x+1.5,y-.65,z),(1.3,.08,.6),dark,command,.1)
    box('Control tower observation deck',(x+1.5,y+1,9.4),(5,4.7,.8),trim,command,.2)
    box('Control tower cap',(x+1.5,y+1,9.9),(5.1,4.8,.2),roofmat,command,.15)
    for dx,dy in [(-1,-1),(1,1),(-1,1)]:antenna(x+1.5+dx,y+1+dy,10,command,random.uniform(2,4.2))
    sphere('Tower small radome',(x+1.5,y+1,10.6),(.9,.9,.26),shell,command)
    tunnel((-20,14,1.8),(-19,20,1.8))

    status('Constructing glass greenhouse and plants')
    greenhouse=group('Greenhouse | geodesic botanical dome')
    gx,gy=-1,13
    deck(gx,gy,16,16,greenhouse)
    cyl('Greenhouse lower pressure ring',(gx,gy,1.25),7,1.85,shell,greenhouse,64)
    round_windows(gx,gy,7.02,1.35,greenhouse,28,.96,.94)
    for z in (.5,2.2):ring('Greenhouse rim',(gx,gy,z),7.06,.13,trim,greenhouse)
    radius=6.8;base=2.2; rings=7; seg=24
    vs=[]
    for j in range(rings):
        phi=(math.pi/2)*j/rings
        rr=radius*math.cos(phi)
        for i in range(seg):
            a=math.tau*(i+.5*(j%2))/seg
            vs.append((gx+rr*math.cos(a),gy+rr*math.sin(a),base+radius*math.sin(phi)))
    top=len(vs);vs.append((gx,gy,base+radius))
    fs=[]
    for j in range(rings-1):
        for i in range(seg):
            a=j*seg+i;b=j*seg+(i+1)%seg;c=(j+1)*seg+i;d=(j+1)*seg+(i+1)%seg
            if j%2:fs.extend([(a,b,d),(a,d,c)])
            else:fs.extend([(a,b,c),(b,d,c)])
    fs += [((rings-1)*seg+i,(rings-1)*seg+(i+1)%seg,top) for i in range(seg)]
    mesh('Individual triangular transparent dome panes',vs,fs,glass,greenhouse)
    edges=set()
    for f in fs:
        for a,b in zip(f,f[1:]+f[:1]):edges.add(tuple(sorted((a,b))))
    for a,b in edges:line('Geodesic aluminium glazing bar',[vs[a],vs[b]],.045,roofmat,greenhouse)
    for x in (-4,-1.4,1.4,4):
        yy=gy+(.6 if abs(x)>3 else 0)
        box('Hydroponic growing trough',(gx+x,yy,.9),(1.7,6.5,.65),roofmat,greenhouse,.12)
        box('Trough growing medium',(gx+x,yy,1.25),(1.5,6.2,.08),greenbed,greenhouse,.02)
        for k in range(6):
            px,py=gx+x,yy-2.7+k*1.05
            h=random.uniform(.8,2.2)
            rod('Botanical stem',(px,py,1.25),(px,py,1.25+h),.045,leaves[0],greenhouse)
            for n in range(4):
                a=n*2.4
                o=sphere('Crop leaf',(px+.32*math.cos(a),py+.32*math.sin(a),1.5+h*(n+1)/5),(.58,.21,.15),leaves[n%3],greenhouse,12)
                o.rotation_euler=(0,.25,a)
    airlock(gx,gy-6.8,.5,greenhouse,'BIO / 02')
    antenna(gx,gy,9.1,greenhouse,1.9)
    tunnel((-14.2,10,1.7),(-8,12,1.7))
    tunnel((-13,22,1.7),(-5,19,1.7))

    status('Building research laboratory and utility hangar')
    lab=group('Laboratory | panoramic research facility')
    lx,ly=18,0
    deck(lx,ly,17,11,lab)
    box('Laboratory lower hull',(lx,ly,1.0),(15,9,1.3),shell,lab,.7)
    box('Laboratory upper shell',(lx,ly,4.45),(15,9,.65),shell,lab,.7)
    box('Laboratory overhanging roof',(lx,ly,4.9),(15.8,9.7,.35),roofmat,lab,.55)
    box('Laboratory rear wall',(lx,ly+4.05,2.8),(14.6,.7,3),shell,lab,.35)
    for xx in (-6.6,6.6):box('Laboratory side casing',(lx+xx,ly,2.8),(1.25,8.2,3.2),shell,lab,.35)
    # Windows reveal benches and equipment while retaining blue reflections.
    labglass=mat('Panoramic translucent glazing',(.21,.5,.56),.15,.15,alpha=.37,transmission=.12)
    box('Laboratory panoramic glazing',(lx,ly-4.12,2.85),(12.4,.07,2.4),labglass,lab,.02)
    for xx in (-5.9,-3.9,-1.9,.1,2.1,4.1,5.9):
        box('Panoramic window mullion',(lx+xx,ly-4.2,2.85),(.10,.12,2.55),trim,lab,.015)
    for xx in (-4,0,4):
        box('Science bench',(lx+xx,ly-1.8,1.75),(2.7,1.3,.18),roofmat,lab,.08)
        for s in (-1,1):box('Bench support',(lx+xx+s*.85,ly-1.8,1.12),(.15,.6,1.2),trim,lab,.02)
        box('Bench monitor',(lx+xx,ly-1.5,2.2),(.8,.13,.6),dark,lab,.05)
        box('Monitor illuminated screen',(lx+xx,ly-1.58,2.2),(.65,.025,.45),mint,lab,.02)
        cyl('Research canister',(lx+xx+.8,ly-2,2.03),.13,.4,metal,lab)
    for dx in (-5.6,5.6):
        for yy in (-3.8,3.8):box('Laboratory buttress',(lx+dx,ly+yy,2.4),(.4,.8,3.8),shell,lab,.13,rotation=(0,.15 if dx<0 else -.15,0))
    line('Lab perimeter running light',[(lx-7.6,ly-4.8,.65),(lx+7.6,ly-4.8,.65),(lx+7.6,ly+4.8,.65)],.055,mint,lab)
    for x in (-3,2):
        box('Roof HVAC enclosure',(lx+x,ly+1,5.65),(2.4,2.3,1.2),shell,lab,.2)
        for k in range(5):box('HVAC vent slat',(lx+x-.8+k*.4,ly-.18,5.7),(.15,.03,.7),dark,lab,.02)
        cyl('Roof fan',(lx+x,ly+1,6.3),.75,.12,trim,lab)
    antenna(lx+5,ly+2,5.15,lab,2.6)
    label('ARES  /  RESEARCH',(lx,ly-4.22,4.18),.32,dark,lab)
    tunnel((5.1,9.2,1.6),(13,4.3,1.6))

    hangar=group('Hangar | equipment workshop')
    x,y=31,14
    deck(x,y,12,12,hangar)
    # Barrel-vault shell, open at the front, with a dark interior and visible ribs.
    profile=[(5.2*math.cos(i*math.pi/24),.55+5.2*math.sin(i*math.pi/24)) for i in range(25)]
    vs=[(x+xx,y+yy,z) for yy in (-5,5) for xx,z in profile]
    fs=[(i,i+1,25+i+1,25+i) for i in range(24)]
    mesh('Workshop vaulted ceramic roof',vs,fs,shell,hangar,True)
    box('Hangar shadow interior',(x,y+4.9,2.6),(9.5,.2,4.4),dark,hangar,.1)
    box('Hangar floor',(x,y,.45),(10,10,.2),trim,hangar,.05)
    for yy in (-5,-1.7,1.7,5):
        line('Workshop arched rib',[(x+xx,y+yy,z+.05) for xx,z in profile],.12,trim if abs(yy)<4 else roofmat,hangar)
    for xx in (-3.7,-1.8,0,1.8,3.7):
        z=.55+math.sqrt(max(0,5.2**2-xx**2))
        line('Workshop longitudinal panel seam',[(x+xx,y-5,z+.03),(x+xx,y+5,z+.03)],.028,trim,hangar)
    box('Workshop access ramp',(x,y-6.2,.31),(6,2.5,.22),roofmat,hangar,.05)
    for xx in (-4.7,4.7):box('Hangar doorway ochre marker',(x+xx,y-5.13,1.2),(.22,.09,1.2),orange,hangar,.03)
    antenna(x-2,y+1,5.4,hangar,2.4)
    tunnel((22,4,1.4),(28,9,1.4))

    status('Building solar field and life support systems')
    solar=group('SolarArray | twelve individually framed panels')
    for row in range(3):
        for col in range(4):
            x,y=-31+col*4.1,-12+row*3.6
            pivot=group('Solar panel %d-%d'%(row+1,col+1));pivot.parent=solar
            pivot.location=(x,y,1.4)
            # All geometry begins in panel-local coordinates.
            panel=box('Solar panel aluminium back',(0,0,0),(3.7,2.7,.16),metal,pivot,.05)
            panel=box('Photovoltaic panel face',(0,0,.105),(3.48,2.48,.055),blue,pivot,.015)
            for k in range(1,9):box('Solar vertical cell trace',(-1.74+k*3.48/9,0,.14),(.012,2.48,.012),cellgrid,pivot,0)
            for k in range(1,5):box('Solar horizontal cell trace',(0,-1.24+k*2.48/5,.14),(3.48,.012,.012),cellgrid,pivot,0)
            pivot.rotation_euler.x=math.radians(23)
            for sx in (-1.35,1.35):
                rod('Solar mounting A-frame',(x+sx,y-1,.35),(x+sx,y,1.4),.085,trim,solar)
                rod('Solar mounting A-frame',(x+sx,y+1,.35),(x+sx,y,1.4),.085,trim,solar)
                box('Solar ground shoe',(x+sx,y,.13),(.55,2.3,.16),shell,solar,.04)
    line('Solar power cable',[(-17,-11,.12),(-13,-6,.12),(-8,-5,.12)],.075,dark,solar)

    life=group('LifeSupport | oxygen and water processing')
    x,y=-4,-9
    deck(x,y,12,9,life)
    cyl('Primary oxygen pressure vessel',(x,y,3.6),2.65,5.8,shell,life,48)
    sphere('Pressure vessel upper dome',(x,y,6.45),(2.65,2.65,.72),shell,life)
    sphere('Pressure vessel bottom dome',(x,y,.75),(2.65,2.65,.5),trim,life)
    for z in (1.1,2,5.8,6.4):ring('Pressure vessel reinforcing band',(x,y,z),2.68,.13,orange if z==2 else trim,life)
    for xx in (-2.75,2.75):
        for yy in (-1.6,1.6):rod('Vessel support cage',(x+xx,y+yy,.6),(x+xx,y+yy,7.1),.09,trim,life)
    ring('Upper maintenance railing',(x,y,7.05),2.9,.07,metal,life)
    for i in range(10):
        a=math.tau*i/10
        rod('Rail baluster',(x+2.9*math.cos(a),y+2.9*math.sin(a),6.6),(x+2.9*math.cos(a),y+2.9*math.sin(a),7.05),.035,metal,life)
    for xx,yy,r,h in [(3.9,.8,.9,4.6),(-3.8,.2,.72,3.5),(3.8,-2,.6,3.2)]:
        cyl('Auxiliary processing tank',(x+xx,y+yy,.65+h/2),r,h,trim,life)
        sphere('Auxiliary tank cap',(x+xx,y+yy,.65+h),(r,r,.3),shell,life)
        ring('Auxiliary ochre band',(x+xx,y+yy,2),r+.03,.08,orange,life)
        line('Process pipe',[(x+xx,y+yy,2.5),(x+xx,y+yy-1,2.5),(x+xx,y+yy-1,.65),(x,y-2.8,.65)],.085,metal,life)
    for side in (-1,1):rod('Ladder rail',(x+side*.34,y-2.77,.7),(x+side*.34,y-2.77,6.4),.04,metal,life)
    for k in range(16):rod('Ladder rung',(x-.34,y-2.8,.8+k*.35),(x+.34,y-2.8,.8+k*.35),.035,metal,life)
    box('Process control cabinet',(x-3.7,y-2.6,1.1),(1.5,1,1.7),shell,life,.12)
    box('Process control display',(x-3.7,y-3.12,1.5),(.85,.03,.5),mint,life,.04)
    label('O2',(x,y-2.72,4.1),.8,orange,life)
    antenna(x,y,7.1,life,2.8)

    status('Constructing dish and six-wheeled rover')
    dish=group('Communications | parabolic dish')
    dx,dy=18,33
    deck(dx,dy,12,11,dish)
    cyl('Dish pedestal',(dx,dy,1.4),3.7,2,shell,dish)
    cyl('Dish rotating mount',(dx,dy,2.65),2.3,.65,trim,dish)
    box('Dish elevation yoke',(dx,dy,4),(1.4,2.2,3),trim,dish,.2)
    pivot=group('Dish elevation assembly');pivot.parent=dish;pivot.location=(dx,dy,5)
    pivot.rotation_euler=(math.radians(30),math.radians(-19),0)
    rr=4.5;segs=48;nr=10
    vs=[(0,0,0)]
    for j in range(1,nr+1):
        r=rr*j/nr
        for i in range(segs):
            a=math.tau*i/segs;vs.append((r*math.cos(a),r*math.sin(a),r*r/9))
    fs=[(0,1+i,1+(i+1)%segs) for i in range(segs)]
    fs += [(1+(j-1)*segs+i,1+(j-1)*segs+(i+1)%segs,1+j*segs+(i+1)%segs,1+j*segs+i) for j in range(1,nr) for i in range(segs)]
    mesh('Concave parabolic reflector',vs,fs,roofmat,pivot,True)
    ring('Dish outer rim',(0,0,rr*rr/9),rr,.085,metal,pivot)
    for i in range(12):
        a=math.tau*i/12
        line('Dish radial segmentation',[(r*math.cos(a),r*math.sin(a),r*r/9+.012) for r in [rr*j/12 for j in range(13)]],.018,trim,pivot)
    for a in (0,math.tau/3,2*math.tau/3):rod('Dish feed support',(rr*.85*math.cos(a),rr*.85*math.sin(a),1.63),(0,0,4.2),.055,trim,pivot)
    cyl('Dish receiver feed',(0,0,4.2),.28,.55,orange,pivot)
    for i in range(12):
        a=math.tau*i/12
        rod('Dish platform safety railing',(dx+4.7*math.cos(a),dy+4.7*math.sin(a),.55),(dx+4.7*math.cos(a),dy+4.7*math.sin(a),1.2),.035,trim,dish)
    line('Dish platform continuous rail',[(dx+4.7*math.cos(i*math.tau/48),dy+4.7*math.sin(i*math.tau/48),1.2) for i in range(48)],.045,metal,dish,True)

    rover=group('Rover | six-wheel exploration vehicle')
    rx,ry=26,-18
    box('Rover chassis',(rx,ry,1.13),(3.8,2.1,.65),trim,rover,.2)
    box('Rover crew cabin',(rx-.15,ry,2),(2.8,1.85,1.45),shell,rover,.38)
    box('Rover roof',(rx-.15,ry,2.78),(2.9,1.95,.16),roofmat,rover,.12)
    box('Rover windshield',(rx-.2,ry-1,2.2),(1.9,.08,.78),window,rover,.17)
    box('Windshield central mullion',(rx-.2,ry-1.05,2.2),(.085,.05,.83),shell,rover,.02)
    for sx in (-1,1):
        box('Rover side glazing',(rx+sx*1.43,ry,2.22),(.06,1.1,.65),window,rover,.1)
    for xx in (-1.45,0,1.45):
        for sign in (-1,1):
            x,y=rx+xx,ry+sign*1.18
            rod('Rocker bogie suspension',(rx+xx*.6,ry,.95),(x,y,.8),.10,orange,rover)
            cyl('Rover all-terrain tire',(x,y,.73),.67,.43,tire,rover,24,(math.pi/2,0,0))
            cyl('Rover wheel alloy hub',(x,y+sign*.24,.73),.34,.05,metal,rover,20,(math.pi/2,0,0))
            for k in range(12):
                a=math.tau*k/12
                o=box('Wheel tread block',(x+.66*math.sin(a),y,.73+.66*math.cos(a)),(.15,.47,.06),dark,rover,.015)
                o.rotation_euler.y=a
    for xx in (-1.1,1.1):box('Rover headlight',(rx+xx,ry-1.06,1.56),(.35,.08,.19),mint,rover,.05)
    antenna(rx+.6,ry+.5,2.85,rover,1.5)
    antenna(rx-.8,ry+.4,2.85,rover,.85)
    box('Rover roof instrument',(rx,ry,3),(1,.7,.35),trim,rover,.1)
    # Rotate the complete vehicle subtly along the drive by transforming its parent.
    for o in list(rover.children):o.location.x-=rx;o.location.y-=ry
    rover.location=(rx,ry,0);rover.rotation_euler.z=math.radians(-23)

    for x,y,s in [(-12,3,1.3),(-11,1.5,1),(-9,3,1.1),(-11,3,1.1),(-10,4.4,.85),
                  (29,-6,1.1),(30.5,-5.8,1.2),(32,-6,1),(37,9,1.4),(38.5,9,1.1),
                  (-11,-13,1.1),(-12,-12,1),(-8,-14,.8)]:crate(x,y,scale=s)
    for x,y in [(-30,11),(8,20),(29,24)]:
        box('Remote utility cabinet',(x,y,1.2),(1.6,1.1,2),shell,props,.12)
        for k in range(4):box('Utility cabinet vent',(x,y-.57,.8+k*.25),(1.05,.03,.09),trim,props,.015)
    for _ in range(85):
        x,y=random.uniform(-35,39),random.uniform(-21,35)
        if any((x-a)**2+(y-b)**2<r*r for a,b,r in [(hx,hy,8),(gx,gy,9),(lx,ly,10),(-4,-9,7),(-17,23,7),(31,14,9)]):continue
        if -34<x<-15 and -14<y<0:continue
        rock(x,y,random.uniform(.1,.38))

    status('Setting camera and lighting')
    world=bpy.data.worlds.new('Mars / apricot atmosphere');scene.world=world;world.use_nodes=True
    world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.28,.17,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.5
    bpy.ops.object.light_add(type='SUN',location=(-40,-30,60))
    sun=bpy.context.object;sun.name='Warm late-afternoon sun';sun.data.energy=3
    sun.data.color=(1,.71,.46);sun.data.angle=math.radians(8)
    sun.rotation_euler=(math.radians(29),math.radians(-28),math.radians(-38))
    bpy.ops.object.light_add(type='AREA',location=(10,-25,35))
    fill=bpy.context.object;fill.name='Large soft sky fill';fill.data.energy=3800
    fill.data.shape='DISK';fill.data.size=40;fill.data.color=(.68,.82,1)
    fill.rotation_euler=(Vector((0,8,0))-fill.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(46,-88,53))
    camera=bpy.context.object;camera.name='Reference composition / hero camera'
    camera.rotation_euler=(Vector((0,10,2.5))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='PERSP';camera.data.lens=44;camera.data.clip_end=600
    scene.camera=camera
    scene.render.engine='CYCLES';scene.cycles.samples=40
    scene.cycles.use_denoising=True
    scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.filepath=str(PREVIEW)
    scene.view_settings.view_transform='AgX'
    scene.view_settings.look='AgX - Medium High Contrast'
    scene.render.film_transparent=False
    # Start the saved viewport at the same useful composition.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_perspective='CAMERA'
                area.spaces.active.clip_end=1000

    status('Saving Blender source')
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
    status('Exporting editable scene to GLB')
    bpy.ops.object.select_all(action='DESELECT')
    for obj in scene.objects:
        if obj.type in {'MESH','CURVE','FONT','EMPTY'}:obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(EXPORT),export_format='GLB',use_selection=True,
                              export_apply=True,export_cameras=False,export_lights=False,
                              export_yup=True,export_materials='EXPORT')
    deps=bpy.context.evaluated_depsgraph_get()
    tris=0
    for obj in scene.objects:
        if obj.type in {'MESH','CURVE','FONT'}:
            evaluated=obj.evaluated_get(deps)
            data=evaluated.to_mesh();data.calc_loop_triangles();tris+=len(data.loop_triangles)
            evaluated.to_mesh_clear()
    stats=dict(objects=len(scene.objects),triangles=tris,units='meters',gltf_up_axis='Y',
               source=str(SOURCE),export=str(EXPORT),preview=str(PREVIEW),
               style='Original procedural interpretation of user-provided reference',
               scientific_data=False,ui_included=False,external_assets=[],
               animation_clips=[],texture_images=[],
               note='Review scene; detailed assembly requires optimization before runtime integration.')
    status('Rendering preview',**stats)
    bpy.ops.render.render(write_still=True)
    status('Complete',**stats)
except Exception:
    status('Failed',traceback=traceback.format_exc())
    raise
