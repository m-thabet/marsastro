# Mars cinematic scene

Open [mars-cinematic-scene.blend](mars-cinematic-scene.blend) in Blender 5.3. The active scene is **Mars / Cinematic Planet**. Numpad `0` shows the saved hero composition. The Blender file packs its three texture images.

- [Rendered preview](../previews/mars-cinematic-scene.png): 1600×900.
- [Complete scene GLB](../world/mars-cinematic-scene.glb): 7.37 MB, including the textured globe, surrounding rock meshes, modeled stars, and baked nebula backdrop.
- [Planet-only GLB](../world/mars-textured-planet.glb): 6.27 MB, one sphere mesh with embedded 4K color and 2K tangent normal maps.
- [Validation report](../previews/mars-cinematic-scene-validation.json).
- [Texture attribution and license](../world/mars-texture-credits.md).

The complete GLB has 20 meshes, 10 materials, and 43,500 evaluated triangles. Both GLBs are self-contained and use Y-up coordinates. They passed structural checks and actual reimport tests in separate Blender scenes, including texture dimensions, scale, and axis conversion.

The display globe has a diameter of 6.4 meters. This is an illustrative model scale, rather than the physical size of Mars. The surrounding rocks and nebula are artistic composition elements inspired by the supplied reference. The baked backdrop is a presentation plane behind the 3D objects; use the planet-only file for unrestricted globe reuse.

The Blender source includes warm sunlight, cool fill lighting, a view-dependent atmospheric limb shader, and compositor bloom. Portable GLBs provide the geometry, PBR textures, and emissive presentation elements; lighting and view-dependent atmospheric effects are handled by the viewing application.

Surface credit: **Solar System Scope / INOVE**, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), [source](https://www.solarsystemscope.com/textures/). The preserved 8K map was resized to 4K. The normal map was derived from color contrast for visual relief and is not measured elevation. Attribution and the license link are embedded in the planet nodes' GLB extras.

Production sources: `build_cinematic_mars.py`, followed by `refine_cinematic_mars.py`. Open the delivered Blender file for edits; choose a new output stem before regeneration to preserve this version. There are no animation clips. The scene has not been integrated into the application.
