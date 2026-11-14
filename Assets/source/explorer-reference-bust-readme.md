# Explorer reference bust

Open [explorer-reference-bust.blend](explorer-reference-bust.blend) in Blender. Its active scene is **Explorer / Reference Character Bust**. Numpad `0` shows the saved portrait camera.

- [GLB model](../characters/explorer-reference-bust.glb): 5.93 MB, self-contained, Y-up, meters.
- [Front portrait](../previews/explorer-reference-bust.png): 1200×1400 transparent PNG.
- [Back view](../previews/explorer-reference-bust-back.png): 800×1000 transparent PNG.
- [Validation report](../previews/explorer-reference-bust-validation.json).

This is a stylized editable interpretation of the user-provided character portrait. Facial likeness and the swept hairstyle are approximate. The upper-body model includes a continuous facial sculpt, separate eyes and expression details, rectangular glasses, modeled hair and groom strands, raised suit collar, orange trim, shoulder harness, buckles, backpack, and chest equipment. The rear details complete the 3D interpretation.

The model measures 1.1088 m wide, 0.5989 m deep, and 1.5294 m tall. It has 402 meshes, 24 materials, and 257,644 evaluated triangles. Its named root controls the overall size, and a separate head pose group provides the slight tilt. This is a static review master; character rigging and runtime optimization remain separate production steps.

The GLB carries portable PBR materials and skin/iris vertex colors. It needs no image textures or downloaded models. Blender additionally retains procedural fabric shading, studio lights, and cameras; those studio objects are excluded from the GLB. Front and back previews were rendered in Cycles.

Validation checked the actual GLB structure, named assemblies, materials, axis conversion, and dimensions, then successfully reimported the file into a disposable Blender scene. Creation used Blender 5.3.0 and local Python modeling based on the supplied reference.

Open the `.blend` for ordinary editing. Production scripts are retained in build → refine → finish → groom order. Regeneration should use a fresh Blender file and a new output stem to preserve this deliverable.
