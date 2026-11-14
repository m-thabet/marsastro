# Current implementation - guided Mars expedition

Updated 14 November 2026. This local implementation follows `solution.md`, `tech plan.md`, `assets.md`, and the user's subsequent implementation requests. The later request replaces the globe-selection opening with a guided arrival and continuous six-turn story. Earlier planning-only restrictions and proposed behavior in those documents are historical. No deployment was performed.

## Current state

The existing React / TypeScript / Vite / React Three Fiber application has a full-viewport, model-based outpost. Its original pure mission resolver, resource values, six-turn event order, NASA evidence, replay validation, and success/safe-return/rescue outcomes remain intact. The world remains an illustrated scientific base, not measured Martian geography.

The new experience is a persistent sequence of small world objectives:

1. Skippable Earth-to-Mars spacecraft flight and animated descent beside the base. Reduced-motion preferences bypass this sequence. Arrival spends no resources.
2. Meet Dr. Maya, then Alex, through world clicks/taps or E at proximity. NOVA introduces the power objective.
3. Inspect power, compare discrete oxygen allocations, check the water tank, power or pause growing lights, and choose lab research or conserving power. Resource HUD items appear as concepts are introduced.
4. Review the exact forecast, advance once, then see short actual benefits and costs.
5. Compare shelter and other crew tasks during the turn-2 radiation warning; rebalance power during turn-3 dust. Dust guidance connects today's generation to energy left by the earlier choice.
6. Mark the rover route and identify a sample. These actions only plan the expedition. Only canonical turn commitment spends supplies and awards research/sample credit. The animated route is illustrative.
7. Consider delayed Earth advice, revisit protection during turn-5 radiation, and choose a final science/survival plan. If an earlier expedition was declined, turn 4 offers another sample opportunity.
8. Compare crew safety, science, and reserves in a short visual debrief. The full chronological record is optional.

A cyan destination ring, floating arrow, world interaction label, and interruptible camera focus identify the current target. Walking retains camera-relative controls, articulated gait, sliding structure collisions, camera clearance, and bounded movement. Touch controls share interaction and movement logic. Overview and the accessible map provide alternatives to walking.

Inactivity produces a contextual hint after 25 seconds without changing choices or advancing time. Recent dialogue can be replayed. Settings can disable guided gates for independent strategies. The guide does not force a winning allocation; alternate tasks remain available in Plan and unsafe decisions retain their actual consequences.

## Decisions and science

Facility panels contain short dialogue, discrete allocations, and numerical forecasts. The global Plan dialog gives access to every canonical task/system, energy allocation, battery capacity/spillage, reserve changes, warnings, research targets, and optional detailed calculations. Nothing spends resources until **Advance turn**. Turn commitment has both guide and stale-turn guards.

Outcome messages derive from the committed history, including actual greenhouse harvests. Earth replies arrive on the original schedule. Dust changes lighting/haze as well as generation. Oxygen and greenhouse equipment reflect the pending allocation; panels label it as planned. Water recycling remains illustrative equipment and adds no unimplemented resource production.

Short contextual science cards lead to explicitly expanded original evidence. All existing evidence identifiers, source links, dates, observations, limitations, and NASA credits are preserved. Resource units, exposure thresholds, harvest timing, and mission events remain fictional training rules. The original audio drafts are not enabled; dialogue is readable text, with no voiceover claim.

## Architecture and persistence

- `src/domain/mission.ts`: unchanged canonical preview/commit simulation.
- `src/domain/guidance.ts`: typed guide nodes, guarded interactions, target catalogue, resource reveals, bounded recent dialogue, and history-derived feedback.
- `src/infrastructure/session.ts`: version-2 guide and pending plan stored atomically with the mission. The authoritative mission is still validated by replay. Legacy saves preserve the mission and compatible pending settings; guidance resumes/restarts appropriately.
- `src/scenes/Outpost.tsx`: retained GLB world, arrival flight/descent, crew interactions, beacons, camera focus, rover route preview, movement/collisions, weather, quality settings, and renderer-loss handling.
- `src/App.tsx`: concise guide and facility overlays, live decision controls, preview/commit, optional science/help/settings, and debrief.

Corrupt saves recover safely. Unavailable storage produces an explicit notice without stopping play. Model/renderer failures offer an explicitly identified accessible mission map; there is no silent replacement of models with images.

## Assets and reproducibility

This storytelling update reuses all 17 runtime GLBs from the preceding visual transformation. It does not claim to have newly modeled another base or crew.

- Runtime: `public/assets/models/` (17 GLBs, 7,866,136 bytes).
- Editable originals and optimized Blender sources: `Assets/source/`, including `game-runtime-catalogue.blend`, `game-commander.blend`, `game-lander.blend`, `game-terrain.blend`, `game-paths.blend`, and equipment sources. Detailed earlier reference masters remain available.
- Reproduction scripts: `build_game_assets.py`, `build_game_equipment.py`, `refine_game_commander.py`, `finish_game_terrain_source.py`, and `optimize_game_images.py` in `Assets/source/`. See `Assets/asset-manifest.md` for provenance.
- The world includes terrain, paths, 220 instanced rocks, eight distinct facilities, power/storage equipment, landing pad, lander, articulated astronaut with crew suit variants, and a rover/sample site.
- Added `public/assets/earth-color.jpg`: 1K Earth day texture for arrival, Solar System Scope / INOVE, CC BY 4.0. Existing Mars texture is 2K. Source and adaptation credits appear in the asset manifest and game science library. Globe distances and flight duration are illustrative.

Runtime material clones share vertex-colored surfaces and disable expensive physical refraction while retaining tinted alpha glazing. Low quality removes shadows and reduces pixel ratio. The scene uses demand rendering with capped animation scheduling and slower updates behind dialogs. Diagnostics require `?debug=1`; counters include rendering/shadow passes and are not a device-FPS certification.

## Running and reviewing

Use Node 24 (see `.nvmrc` and `package.json`):

```powershell
npm.cmd ci
npm.cmd run dev
```

Open http://127.0.0.1:5173. Watch or skip arrival. Walk with WASD/arrows, drag to look, press E near crew/facilities, or tap world labels. **Find** focuses the destination in Overview; **Walk** returns to the commander. Use **Plan** to compare allocations and **Advance turn** to act. Sources and optional detailed science are in the flask menu. Settings provide quality, map mode, guided/independent play, and restart. Direct accessible map: `/?view=map`.

If the global Node is older, the cached Node 24 alternative is:

```powershell
npm.cmd exec --package=node@24 -- node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173
```

Checks:

```powershell
npm.cmd run typecheck
npm.cmd run lint
npm.cmd test
npm.cmd run build
$env:PLAYWRIGHT_PREVIEW='1'
npm.cmd run test:e2e -- --workers=1
```

The browser suite covers the full six-turn mission and exact committed state, wrong-target guards, pending-plan/outcome/route recovery, delayed advice, independent unsafe strategy, accessible controls, inactivity without automatic decisions, storage failures, actual WebGL walking/E conversations, camera focus, quality changes, context loss, skipped/reduced-motion/natural arrival, and an explicit missing-model fallback. Desktop Chromium and a mobile Chromium viewport are used. Render captures in `docs/review/*-arrival.png`, `*-guided-base.png`, `*-crew.png`, `*-objective.png`, `*-allocation.png`, and `*-guided-low.png` support visual review. Older screenshots are retained as earlier review artifacts.

## Remaining work before a public demonstration

- Test physical ordinary laptops and phones, Firefox/WebKit, keyboard-only exploration, and manual screen readers. Automated mobile emulation is not real-device validation.
- Observe children aged 7-12 playing without adult explanation; tune dialogue, timing, target visibility, and allocation comprehension from those observations.
- Review/author audio before enabling it. A unique Maya portrait and optional recorded dialogue remain art/audio refinements.
- The base has no explorable interiors, free rover driving, production skeletal animation, or mesh-accurate terrain physics. Crew use articulated shared models with suit variants. Collision uses conservative bounds in a mostly flat playable basin.
- Verify distribution/deployment separately; this work is local and retains Vite's generic warning about the lazy 3D chunk size.

## Verification result for this update

TypeScript, ESLint, the production build, and all 44 unit/data/asset checks passed. The completed production browser run passed 14 desktop/mobile checks, including the full six-turn mission, exact canonical results, pending-plan/outcome/route recovery, accessibility checks, storage failure, world walking/E interaction, camera focus, quality changes, renderer loss, natural arrival, and reduced motion. Actual desktop/mobile renders were captured and inspected.

The two initial missing-model checks exposed automatic map recovery before the error-panel click. The implementation now provides a clear recovery notice and the tests accept both explicit-panel and automatic-map paths. The final isolated rerun could not complete because local runner processes repeatedly timed out; verification of this last recovery-message patch remains outstanding. Do not interpret this as an all-green 16-check final suite. Rerun `npm.cmd run test:e2e -- --workers=1` against the production preview when the local runner is responsive.

## Background music update

Background music is now integrated: *Adrift Among Infinite Stars* by Scott Buckley (CC BY 4.0), a licensed cinematic piano/synth/string track. See `public/assets/audio/CREDITS.md` for the source, license and adaptations. Settings and Science library include credits. Earlier statements that all audio is inactive are superseded for this soundtrack only; draft effects/ambiences and voiceover remain inactive.

Music starts after the player's first tap or keypress at 24% volume, loops without resetting between mission steps, pauses in hidden tabs, and has a header mute/play button plus a persistent volume/enable setting. Audio loads on demand and fails independently from gameplay. Browser checks exercise actual MP3 decoding, volume, mute, reload preferences, loop boundary, visibility handling, and missing-file recovery on desktop and mobile Chromium.
