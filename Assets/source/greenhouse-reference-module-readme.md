# Greenhouse reference module

Open [greenhouse-reference-module.blend](greenhouse-reference-module.blend) in Blender 5.3. The active scene is **Greenhouse / Reference Hydroponics**. Numpad `0` shows the saved reference camera.

- [Front preview](../previews/greenhouse-reference-module.png): 1536×1024.
- [Rear preview](../previews/greenhouse-reference-module-rear.png): 1200×800.
- [GLB model](../buildings/greenhouse-reference-module.glb): 2.96 MB, self-contained, Y-up, meters.
- [Validation report](../previews/greenhouse-reference-module-validation.json).

The editable interpretation includes six continuous curved glass panels, ivory arch ribs, an armored end airlock and ramp, six hydroponic trays with 48 modeled crop clusters, a central walkway, three suspended magenta grow fixtures, roof HVAC and antenna, an external water tank and pump, rounded pipework, and rear service detailing. Beds, foliage, glazing, frame, fixtures, door, and equipment have separate named objects or groups.

Overall dimensions are approximately 13.54 m wide, 6.2517 m deep, and 7.5579 m tall, including the ramp and antenna. The origin is at the greenhouse building center on Z=0. The review master has 201 meshes, 108,026 evaluated triangles, and 14 portable PBR materials. No image textures or external models are required. The model is static, with no animation clips.

The glazing uses portable `BLEND` transparency. The foliage is actual leaf and stem geometry, and the grow-light fixtures use emission materials. Blender additionally retains grow-illumination area lights, the neutral studio, and compositor bloom; these lighting effects are excluded from the GLB and can be recreated by the viewing application.

The sill is an open perimeter rather than an opaque block covering the planting beds. Its hidden construction cutter remains editable in Blender and is excluded from the export. The source includes the raised floor and clear central walkway.

The actual GLB passed structural and finite-geometry checks and was reimported successfully in a separate Blender scene. Tests verified all six glazing panels, six eight-plant trays, three grow fixtures, transparency, emission, dimensions, and axis conversion. Raycasts confirmed the open sill interior and walkway at Z=0.8875. The rear preview framing was checked to include the complete antenna.

Creation used local Python modeling in Blender 5.3.0 from the user-supplied reference. Production sources are `build_reference_greenhouse.py` followed by `refine_reference_greenhouse.py`. Open the delivered `.blend` for ordinary edits; regenerate in a fresh file under a new output stem to preserve this version. Application integration and final runtime optimization remain separate production steps.
