"""Build an editable Mars-in-space presentation inspired by the supplied image.

The planet uses the project's credited Solar System Scope map. Relief normals,
nebula, stars, and surrounding rocks are illustrative rather than measured data.
"""
import bpy
import math
import random
import json
import time
import traceback
from pathlib import Path
from mathutils import Vector,noise

ASSETS=Path(__file__).resolve().parents[1]
STEM='mars-cinematic-scene'
SOURCE=ASSETS/'source'/(STEM+'.blend')
MODEL=ASSETS/'world'/(STEM+'.glb')
PLANET_MODEL=ASSETS/'world/mars-textured-planet.glb'
PREVIEW=ASSETS/'previews'/(STEM+'.png')
REPORT=ASSETS/'previews'/(STEM+'-report.json')
COLOR=ASSETS/'world/mars-global-color-4k.jpg'
NORMAL=ASSETS/'world/mars-illustrative-normal-2k.png'
NEBULA=ASSETS/'world/mars-cinematic-nebula-2k.png'
START=time.time();random.seed(8128)
for p in (SOURCE.parent,MODEL.parent,PREVIEW.parent):p.mkdir(parents=True,exist_ok=True)

def status(stage,**data):
    REPORT.write_text(json.dumps(dict(stage=stage,elapsed_seconds=round(time.time()-START,2),**data),indent=2))

def material(name,color,rough=.7,metal=0,emission=0):
    m=bpy.data.materials.new('Mars Cinema / '+name);m.use_nodes=True;m.diffuse_color=(*color,1)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    if emission:
        p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    return m

def group(name,parent=None):
    o=bpy.data.objects.new(name,None);scene.collection.objects.link(o);o.parent=parent;return o

def sphere(name,r,mat,parent,segments=160,rings=80):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=r)
    o=bpy.context.object;o.name=name;o.parent=parent;o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    return o

def mesh(name,verts,faces,mat,parent):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.parent=parent
    if mat:data.materials.append(mat)
    return o

def mathnode(nt,operation,*args):
    n=nt.nodes.new('ShaderNodeMath');n.operation=operation
    for i,arg in enumerate(args):
        if isinstance(arg,(int,float)):n.inputs[i].default_value=arg
        else:nt.links.new(arg,n.inputs[i])
    return n.outputs[0]

def bake_image(obj,material,image,kind):
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    nt=material.node_tree
    for n in nt.nodes:n.select=False
    target=nt.nodes.new('ShaderNodeTexImage');target.image=image;target.select=True;nt.nodes.active=target
    scene.render.bake.margin=12;scene.cycles.samples=8
    bpy.ops.object.bake(type=kind,use_clear=True)
    image.file_format='PNG';image.save();nt.nodes.remove(target)

def select_only(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)

try:
    if SOURCE.exists() or MODEL.exists() or PLANET_MODEL.exists():raise FileExistsError('Choose a new scene stem to preserve prior output.')
    scene=bpy.data.scenes.new('Mars / Cinematic Planet');bpy.context.window.scene=scene
    scene.unit_settings.system='METRIC';scene.render.engine='CYCLES';scene.cycles.use_denoising=True
    root=group('MarsScene | cinematic reference composition')
    globe_root=group('Planet | textured Mars globe',root)
    rocks_root=group('Rocks | illustrative surrounding asteroids',root)
    stars_root=group('Stars | modeled distant lights',root)
    backdrop_root=group('Backdrop | baked procedural nebula',root)
    effects_root=group('Atmosphere | Blender-only limb glow')

    status('Preparing planet material and illustrative relief')
    color_image=bpy.data.images.load(str(COLOR),check_existing=True)
    color_image.name='Mars 4K / Solar System Scope CC BY 4.0'
    planetmat=material('Mars 4K surface',(1,1,1),.89)
    nt=planetmat.node_tree;p=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Specular IOR Level'].default_value=.18
    tex=nt.nodes.new('ShaderNodeTexImage');tex.image=color_image;tex.interpolation='Linear'
    nt.links.new(tex.outputs['Color'],p.inputs['Base Color'])
    gray=nt.nodes.new('ShaderNodeRGBToBW');nt.links.new(tex.outputs['Color'],gray.inputs[0])
    bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.36;bump.inputs['Distance'].default_value=.10
    nt.links.new(gray.outputs[0],bump.inputs['Height']);nt.links.new(bump.outputs[0],p.inputs['Normal'])
    globe=sphere('Mars | UV sphere with portable 4K surface',3.2,planetmat,globe_root,192,96)
    globe['texture_credit']='Solar System Scope / INOVE — CC BY 4.0 — https://www.solarsystemscope.com/textures/'
    globe['scale_note']='Display globe radius 3.2 m; illustrative model scale, not physical Mars radius'
    globe['normal_note']='Illustrative tangent normal map derived from color-map contrast, not elevation measurements'
    normal_image=bpy.data.images.new('Mars illustrative relief normals',width=2048,height=1024,alpha=False)
    normal_image.colorspace_settings.name='Non-Color';normal_image.filepath_raw=str(NORMAL)
    bake_image(globe,planetmat,normal_image,'NORMAL')
    nt.nodes.remove(gray);nt.nodes.remove(bump)
    normaltex=nt.nodes.new('ShaderNodeTexImage');normaltex.image=normal_image
    normalmap=nt.nodes.new('ShaderNodeNormalMap');normalmap.inputs['Strength'].default_value=.65
    nt.links.new(normaltex.outputs['Color'],normalmap.inputs['Color']);nt.links.new(normalmap.outputs['Normal'],p.inputs['Normal'])
    # Bring the map's canyon-rich western hemisphere into the hero view.
    uv=globe.data.uv_layers.active.data
    closest=min(globe.data.loops,key=lambda loop:(uv[loop.index].uv.x-.325)**2+(uv[loop.index].uv.y-.5)**2)
    vertex=globe.data.vertices[closest.vertex_index].co
    globe.rotation_euler.z=-math.pi/2-math.atan2(vertex.y,vertex.x)

    status('Baking original purple and blue nebula backdrop')
    nebmat=bpy.data.materials.new('Mars Cinema / Original nebula');nebmat.use_nodes=True
    nt=nebmat.node_tree;nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial');em=nt.nodes.new('ShaderNodeEmission');em.inputs['Strength'].default_value=1
    nt.links.new(em.outputs[0],out.inputs['Surface'])
    coords=nt.nodes.new('ShaderNodeTexCoord');split=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(coords.outputs['UV'],split.inputs[0])
    # A diagonal, slightly meandering luminous band, broken into wispy clouds.
    u=split.outputs['X'];v=split.outputs['Y']
    wave=mathnode(nt,'SINE',mathnode(nt,'MULTIPLY',u,8))
    path=mathnode(nt,'ADD',mathnode(nt,'MULTIPLY',u,.55),mathnode(nt,'ADD',.17,mathnode(nt,'MULTIPLY',wave,.055)))
    dist=mathnode(nt,'SUBTRACT',v,path)
    band=mathnode(nt,'EXPONENT',mathnode(nt,'MULTIPLY',mathnode(nt,'MULTIPLY',dist,dist),-100))
    cloud=nt.nodes.new('ShaderNodeTexNoise');cloud.inputs['Scale'].default_value=7.5;cloud.inputs['Detail'].default_value=6;cloud.inputs['Roughness'].default_value=.75
    nt.links.new(coords.outputs['UV'],cloud.inputs['Vector'])
    fine=nt.nodes.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=32;fine.inputs['Detail'].default_value=4
    nt.links.new(coords.outputs['UV'],fine.inputs['Vector'])
    mask=mathnode(nt,'MULTIPLY',band,mathnode(nt,'MULTIPLY',cloud.outputs['Fac'],mathnode(nt,'MULTIPLY',fine.outputs['Fac'],2.2)))
    ramp=nt.nodes.new('ShaderNodeValToRGB')
    elements=ramp.color_ramp.elements
    elements[0].position=.04;elements[0].color=(.0008,.0012,.005,1)
    elements[1].position=.92;elements[1].color=(.15,.035,.20,1)
    for position,color in [(.24,(.002,.004,.018,1)),(.46,(.012,.007,.050,1)),(.64,(.045,.009,.12,1)),(.80,(.08,.035,.17,1))]:
        el=elements.new(position);el.color=color
    nt.links.new(mask,ramp.inputs[0]);nt.links.new(ramp.outputs[0],em.inputs['Color'])
    backdrop=mesh('Nebula | original baked presentation sky',[(-11,8,-6),(11,8,-6),(11,8,6),(-11,8,6)],[(0,1,2,3)],nebmat,backdrop_root)
    uv=backdrop.data.uv_layers.new(name='Backdrop UV')
    for loop,co in zip(uv.data,[(0,0),(1,0),(1,1),(0,1)]):loop.uv=co
    nebula_image=bpy.data.images.new('Original cinematic nebula 2K',width=2048,height=1152,alpha=False)
    nebula_image.filepath_raw=str(NEBULA)
    bake_image(backdrop,nebmat,nebula_image,'EMIT')
    nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');em=nt.nodes.new('ShaderNodeEmission')
    em.inputs['Strength'].default_value=1
    tex=nt.nodes.new('ShaderNodeTexImage');tex.image=nebula_image
    nt.links.new(tex.outputs['Color'],em.inputs['Color']);nt.links.new(em.outputs[0],out.inputs['Surface'])

    status('Modeling asteroid silhouettes and distant stars')
    rockmats=[material('Asteroid sandstone %d'%i,c,.93) for i,c in enumerate([
        (.19,.07,.028),(.29,.12,.052),(.12,.052,.033),(.36,.16,.07)])]
    placements=[(-5.6,1,1.1,.18),(-5.0,.4,-1.25,.22),(-7.15,-1,-2.3,.65),(-6.9,-2,-4.2,1.05),
        (-5.75,1,-3.2,.15),(-4.5,2,-2.0,.07),(5.7,1,1.2,.25),(4.65,2,-2.95,.33),
        (6.4,-1,-3.9,.9),(5.35,1,-1.35,.25),(4.7,2,-.8,.11),(4.3,1,-2.7,.07),
        (-6.7,1.2,2.6,.075),(6.0,2,3.0,.06)]
    for index,(x,y,z,r) in enumerate(placements):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(x,y,z))
        obj=bpy.context.object;obj.name='Asteroid / illustrative rock %02d'%index;obj.parent=rocks_root
        for vertex in obj.data.vertices:
            original=vertex.co.copy();vertex.co*=1+.15*noise.noise_vector(original*2+Vector((index,0,0)))[0]
        obj.scale=(r*random.uniform(.9,1.4),r*random.uniform(.65,1),r)
        obj.rotation_euler=(random.random(),random.random(),random.random()*math.tau)
        for m in rockmats:obj.data.materials.append(m)
        for face in obj.data.polygons:face.material_index=random.choices([0,1,2,3],[.45,.30,.20,.05])[0]
        bevel=obj.modifiers.new('Soft eroded stone edges','BEVEL');bevel.width=.025;bevel.segments=2
        obj.modifiers.new('Weighted rock normals','WEIGHTED_NORMAL')
    star_mats=[material('Starlight %d'%i,c,.4,emission=6) for i,c in enumerate([( .75,.84,1),(1,.66,.35),(.53,.63,1)])]
    for bucket in range(3):
        verts=[];faces=[]
        for i in range(150 if bucket==0 else 75):
            x=random.uniform(-9.3,9.3);z=random.uniform(-5.4,5.4);y=random.uniform(5,6.5)
            r=random.uniform(.005,.014)*(2.1 if i<3 else 1)
            start=len(verts)
            verts += [(x+r,y,z),(x-r,y,z),(x,y+r,z),(x,y-r,z),(x,y,z+r),(x,y,z-r)]
            faces += [tuple(start+j for j in f) for f in [(0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5)]]
        mesh('Starfield | batched light points %d'%bucket,verts,faces,star_mats[bucket],stars_root)
    sunmat=material('Off-frame warm sun',(1,.36,.065),.5,emission=30)
    sun=sphere('Sun | corner glow source',.20,sunmat,backdrop_root,32,16);sun.location=(-7.2,4.0,4.35)

    status('Creating sunset lighting and thin atmospheric limb')
    # This view-dependent shader is kept in Blender, separate from portable PBR exports.
    atmo=bpy.data.materials.new('Mars Cinema / warm thin limb');atmo.use_nodes=True
    nt=atmo.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial')
    geo=nt.nodes.new('ShaderNodeNewGeometry');dot=nt.nodes.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT'
    nt.links.new(geo.outputs['Normal'],dot.inputs[0]);nt.links.new(geo.outputs['Incoming'],dot.inputs[1])
    edge=mathnode(nt,'POWER',mathnode(nt,'SUBTRACT',1,mathnode(nt,'ABSOLUTE',dot.outputs['Value'])),4)
    lightdot=nt.nodes.new('ShaderNodeVectorMath');lightdot.operation='DOT_PRODUCT';lightdot.inputs[1].default_value=(-.70,-.48,.53)
    nt.links.new(geo.outputs['Normal'],lightdot.inputs[0])
    factor=mathnode(nt,'MULTIPLY',edge,mathnode(nt,'MAXIMUM',lightdot.outputs['Value'],.025))
    transparent=nt.nodes.new('ShaderNodeBsdfTransparent');emit=nt.nodes.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value=(1,.19,.025,1);emit.inputs['Strength'].default_value=4
    mix=nt.nodes.new('ShaderNodeMixShader');nt.links.new(factor,mix.inputs[0]);nt.links.new(transparent.outputs[0],mix.inputs[1]);nt.links.new(emit.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],out.inputs['Surface'])
    atmosphere=sphere('Atmospheric limb | render effect',3.228,atmo,effects_root,160,80)
    world=bpy.data.worlds.new('Mars / deep space');world.use_nodes=True;scene.world=world
    bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.012,.016,.05,1);bg.inputs[1].default_value=.09
    bpy.ops.object.light_add(type='SUN',location=(-10,-8,9));key=bpy.context.object;key.name='Warm upper-left solar key'
    key.data.energy=3.2;key.data.color=(1,.64,.36);key.data.angle=math.radians(1)
    key.rotation_euler=Vector((.70,.48,-.53)).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.light_add(type='AREA',location=(7,-7,1.5));fill=bpy.context.object;fill.name='Very soft cool shadow fill'
    fill.data.energy=95;fill.data.size=7;fill.data.color=(.29,.38,1)
    fill.rotation_euler=(-fill.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(0,-20,.65));camera=bpy.context.object;camera.name='Mars reference hero camera'
    camera.rotation_euler=(-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=14.4
    scene.camera=camera;scene.render.resolution_x=1600;scene.render.resolution_y=900;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    scene.cycles.samples=64;scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.25
    # Blender 5.3's compositor uses a scene-level node group.
    comp=bpy.data.node_groups.new('Mars / restrained cinematic bloom','CompositorNodeTree')
    comp.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
    layers=comp.nodes.new('CompositorNodeRLayers');layers.scene=scene
    glare=comp.nodes.new('CompositorNodeGlare')
    glare.inputs['Type'].default_value='Fog Glow';glare.inputs['Quality'].default_value='High'
    glare.inputs['Threshold'].default_value=1.5;glare.inputs['Size'].default_value=.6
    glare.inputs['Strength'].default_value=.45
    groupout=comp.nodes.new('NodeGroupOutput')
    comp.links.new(layers.outputs['Image'],glare.inputs['Image']);comp.links.new(glare.outputs['Image'],groupout.inputs['Image'])
    scene.compositing_node_group=comp
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'

    status('Exporting planet and complete portable scene')
    portable=set()
    def visit(obj):
        portable.add(obj)
        for child in obj.children:visit(child)
    visit(root)
    select_only(portable)
    bpy.ops.export_scene.gltf(filepath=str(MODEL),export_format='GLB',use_selection=True,use_active_scene=True,
        export_apply=True,export_yup=True,export_cameras=False,export_lights=False,export_extras=True)
    select_only([globe_root,globe])
    bpy.ops.export_scene.gltf(filepath=str(PLANET_MODEL),export_format='GLB',use_selection=True,use_active_scene=True,
        export_apply=True,export_yup=True,export_cameras=False,export_lights=False,export_extras=True)
    for image in (color_image,normal_image,nebula_image):image.pack()
    deps=bpy.context.evaluated_depsgraph_get();tris=0
    for obj in portable:
        if obj.type=='MESH':
            ev=obj.evaluated_get(deps);data=ev.to_mesh();data.calc_loop_triangles();tris+=len(data.loop_triangles);ev.to_mesh_clear()
    stats=dict(source=str(SOURCE),model=str(MODEL),planet_model=str(PLANET_MODEL),preview=str(PREVIEW),
        model_nodes=len(portable),triangles=tris,planet_radius_display_meters=3.2,
        planet_dimensions_display_meters=[6.4,6.4,6.4],texture_dimensions=[4096,2048],normal_dimensions=[2048,1024],
        nebula_dimensions=[2048,1152],gltf_up_axis='Y',animation_clips=[],
        texture_credit='Solar System Scope / INOVE, CC BY 4.0, https://www.solarsystemscope.com/textures/',
        texture_changes='Resized 8192x4096 source to 4096x2048; color-map contrast used for illustrative normals',
        scientific_limitations='Processed visualization map; color-derived normals are not measured elevation; surrounding rocks and nebula are illustrative',
        render_only=['View-dependent atmosphere shader','Solar key and cool fill','Camera','Compositor bloom'],
        external_files_required_by_glb=[])
    scene.render.filepath=str(PREVIEW);bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
    status('Rendering Mars scene',**stats)
    bpy.ops.render.render(write_still=True)
    status('Complete',**stats)
except Exception:
    status('Failed',traceback=traceback.format_exc())
    raise
