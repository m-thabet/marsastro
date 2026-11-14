# Landing-pad reference module

Open [landing-pad-reference-module.blend](landing-pad-reference-module.blend) in Blender 5.3. The active scene is **Landing Pad / Reference Circular Platform**. Numpad `0` shows the saved reference camera.

- [Main preview](../previews/landing-pad-reference-module.png): 1600×900.
- [Top layout preview](../previews/landing-pad-reference-module-top.png): 1200×1200.
- [GLB model](../buildings/landing-pad-reference-module.glb): 5.96 MB, self-contained, Y-up, meters.
- [Validation report](../previews/landing-pad-reference-module-validation.json).

The editable interpretation includes 48 metal deck plates across 12 sectors, segmented orange guidance rings, four inset deck grilles, ivory perimeter armor, side ventilation slots, warm approach lights, four amber beacon assemblies, fasteners, restrained wear marks, and a sloped access ramp with traction ribs, guidance strips, side rails, and paired foot lights. The deck, perimeter, guidance rings, beacons, grilles, hardware, and ramp have named groups.

Overall dimensions are 14.56 m wide, 16.91 m deep, and 1.9275 m tall, including the ramp and beacons. The origin is at the platform center on Z=0, with approximately 0.035 m clearance below the lowest geometry. The review master contains 434 meshes, 144,632 evaluated triangles, and 13 portable PBR materials. No image textures or external models are required. This is a static model with no animation clips.

The actual GLB passed structural and finite-geometry checks and was reimported successfully in a separate Blender scene. Tests confirmed all 48 deck plates, four beacons and four deck grilles, portable emissive markers, concentric guide-ring geometry, dimensions, and axis conversion. Raycasts against the imported ramp confirmed its real slope rather than a flat surface.

The Blender source retains the neutral studio floor, lights, cameras, and restrained marker-light bloom. These studio elements are excluded from the GLB; emissive materials remain in the export. Dimensions describe an illustrative visual asset, rather than a rated aircraft load specification.

Creation used local Python modeling in Blender 5.3.0 from the user-supplied reference. Production sources are `build_reference_landing_pad.py` followed by `refine_reference_landing_pad.py`. Open the delivered `.blend` for normal edits; use a fresh file and a new output stem for regeneration. Application integration and final runtime optimization remain separate production steps.
