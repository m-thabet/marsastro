# Life-support reference module

Open [life-support-reference-module.blend](life-support-reference-module.blend) in Blender 5.3. The active scene is **Life Support / Reference Processing Module**. Numpad `0` shows the saved reference camera.

- [Front preview](../previews/life-support-reference-module.png): 1536×1024.
- [Rear preview](../previews/life-support-reference-module-rear.png): 1200×800.
- [GLB model](../buildings/life-support-reference-module.glb): 2.42 MB, self-contained, Y-up, meters.
- [Validation report](../previews/life-support-reference-module-validation.json).

The editable interpretation includes a paneled filtration cabinet, actual recessed window cavity, transparent blue glazing, three cyan-banded cartridges, a nine-blade fan with its own rotor pivot, yoke, twin pressure vessels, rounded pipe elbows, orange couplings, low transfer manifold, compressor cassette, vents, antennas, running lights, and a linked foundation. Rear service detailing completes the unseen side in the supplied reference's style.

Overall dimensions are 10.4085 m wide, 6.1082 m deep, and 6.2235 m tall. The assembly origin is at Z=0, with approximately 0.04 m clearance below the lowest geometry. The review master has 229 meshes, 84,932 evaluated triangles, and 11 portable PBR materials. No image textures or external models are required.

The fan assembly and **Rotor | nine blades local-Z pivot** are separately editable; rotate the rotor's local Z axis to pose the blades. The tanks, filters, cabinet, and plumbing have named groups. This is a static model with no animation clips.

The Blender source retains a hidden construction cutter for the window cavity. Its Boolean modifier remains editable. The GLB contains the evaluated cut geometry and excludes the cutter, studio floor, lighting, and cameras. Its window uses a portable `BLEND` transparency material, and its status bands use emission.

The actual GLB passed structural and finite-geometry checks and was reimported successfully in a separate Blender scene. Tests verified the named assemblies, blade/filter counts, transparency, dimensions, and axis conversion. A raycast against the imported shell confirmed the genuine recessed opening rather than a window placed over a solid front wall.

Creation used local Python modeling in Blender 5.3.0 from the user-supplied image. The production source is `build_reference_life_support.py`. Open the delivered `.blend` for normal editing; use a fresh file and a new output stem for regeneration. Application integration and final runtime optimization remain separate production steps.
