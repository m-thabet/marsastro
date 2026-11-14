# Solar array reference module

Open [solar-array-reference-module.blend](solar-array-reference-module.blend) in Blender 5.3. The active scene is **Solar / Reference Twin Array**. Numpad `0` shows the saved reference camera.

- [Front preview](../previews/solar-array-reference-module.png): 1536×1024.
- [Rear preview](../previews/solar-array-reference-module-rear.png): 1200×800.
- [GLB model](../buildings/solar-array-reference-module.glb): 2.22 MB, self-contained, Y-up, meters.
- [Validation report](../previews/solar-array-reference-module-validation.json).

The model is an editable interpretation of the supplied solar-array reference. It includes two four-panel banks, 512 individually delineated cell faces, fine silver grid traces, chamfered ivory frames, orange corner guards, hinges, bolted A-frames, connected foundation decks, running lights, a control pedestal, antenna, rear reinforcing rails, junction boxes, and cable loops.

Both banks have separately named hinge-pivot empties. Rotate a bank's **local X axis** to change its tilt from the saved 30° position. The supports and foundation remain separate, and individual panels are children of their bank pivot. This is a static asset with no animation clips.

Overall dimensions are 12.12 m wide, 4.5875 m deep, and 3.8996 m tall. The assembly origin is at Z=0, with approximately 0.035 m clearance below the lowest geometry. The review master contains 274 meshes, 57,072 evaluated triangles, and 12 PBR materials. All cell grids are modeled geometry; no image textures or external assets are required.

The GLB passed structural and finite-geometry checks and was successfully reimported in a separate Blender scene. Verification confirmed all eight panels, their eight 8×8 cell grids, both 30° bank pivots, dimensions, and axis conversion. The Blender source retains the studio floor, lights, and camera; these are excluded from the GLB.

Creation used local Python modeling in Blender 5.3.0 from the user-supplied image. Production sources are `build_reference_solar_array.py` followed by `refine_reference_solar_array.py`. Open the delivered `.blend` for ordinary edits; use a fresh file and new output stem for regeneration. Application integration and final runtime optimization remain separate production steps.
