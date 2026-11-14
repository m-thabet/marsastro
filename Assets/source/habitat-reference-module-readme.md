# Habitat reference module

Open [habitat-reference-module.blend](habitat-reference-module.blend) in Blender 5.3. The active scene is **Habitat / Reference Exterior**. Numpad `0` shows the saved reference camera.

- [Front preview](../previews/habitat-reference-module.png): 1536×1024.
- [Rear preview](../previews/habitat-reference-module-rear.png): 1200×800.
- [GLB model](../buildings/habitat-reference-module.glb): 4.04 MB, self-contained, Y-up, meters.
- [Validation report](../previews/habitat-reference-module-validation.json).

The model is an editable exterior interpretation of the user-supplied habitat image. Named assemblies include the paneled pressure hull, lower skirt and feet, curved windows, airlock surround and armored door leaf, ramp, skylight, orange roof bridge, antennas, vents, communications dish, and rear service cabinets. Rear detailing completes the unseen side in the reference style.

Overall dimensions are 13.9304 m wide, 11.1825 m deep, and 8.0492 m tall, including the ramp and antennas. The assembly origin is at the building center on Z=0. The detailed review master has 211 meshes, 188,132 evaluated triangles, and 10 materials. It is static, with separately editable door and equipment geometry.

All surface appearance uses portable PBR colors and modeled details. No external textures, models, or image-generation services were used. The Blender source retains the neutral studio floor, lighting, and cameras; those studio objects are excluded from the GLB.

The actual GLB passed structural and finite-geometry checks and was successfully reimported into a separate Blender scene, confirming named assemblies, scale, and axis conversion. This is a visual exterior master for review; runtime simplification and application integration are separate steps.

Production sources are `build_reference_habitat.py` followed by `refine_reference_habitat.py`. Open the delivered Blender file for edits. Regeneration should use a fresh file and a new output stem to preserve this version.
