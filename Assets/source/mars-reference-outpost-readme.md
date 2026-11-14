# Mars reference outpost

Open [mars-reference-outpost.blend](mars-reference-outpost.blend) in Blender 5.3.
The active scene is **Mars / Reference Outpost**. Numpad `0` shows its saved hero camera; middle-drag orbits the model.

- [Preview](../previews/mars-reference-outpost.png): 1600×900 Cycles render.
- [GLB model](../world/mars-reference-outpost.glb): self-contained scene, 6.8 MB, Y-up, meters.
- Named assemblies: habitat, greenhouse, lab, hangar, control tower, oxygen plant, solar field, communications dish, rover, tunnels, props, and terrain.
- The whole landscape measures about 290×285 m. Total evaluated geometry is 226,706 triangles, including repeated rock instances.

This is an editable procedural interpretation of the supplied reference. The UI and portrait are excluded. It is an illustrative landscape, with no NASA terrain data or external model downloads.

The Blender source includes lighting, camera, transparent greenhouse glazing, and procedural sand shading. The GLB carries portable PBR materials and sandstone vertex colors; Blender-specific procedural sand detail is not baked into texture images.

The GLB passed structural checks and was reimported successfully in a disposable Blender scene. Reports live beside the preview. This detailed review assembly has not been integrated into the application or optimized for its target devices.

To regenerate, use a fresh Blender session and a new output stem, then run `build_reference_outpost.py`, `refine_reference_outpost.py`, and `polish_reference_outpost.py` in that order. The build script refuses to replace an existing base scene; the two finishing scripts operate on that generated scene. Open the delivered `.blend` for ordinary edits.
