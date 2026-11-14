# Mars Mission Commander

**Team:** plus c  |  **Challenge:** Junior Astronaut Mission Trainer

Playable educational prototype / Cairo 2026 / 14 November 2026

Figure: Current prototype: an illustrated Mars outpost with selectable facilities, crew and resource decisions.

## What we built

Mars Mission Commander is a browser game that lets young explorers lead a six-turn Mars training mission. Players explore a 3D outpost, meet their crew, allocate electricity, manage oxygen, water and food, and choose between science and protection. Each committed decision changes the mission and receives a short explanation. NASA observations and research appear in contextual science cards, with clear boundaries between real evidence and fictional game rules.

## The problem and the challenge

Space survival is difficult to teach through facts alone: producing oxygen, growing food and protecting a crew compete for limited resources. Our response to the challenge is a place to practise those connected decisions. The intended audience is young learners, especially ages 7-12, with potential use in classrooms, science clubs and family learning. This age range and educational benefit still require learner testing.


---

# How the experience works

The player is the Commander. Dr. Maya introduces science, Alex explains engineering, and NOVA provides guidance. NOVA is a scripted character, not a live AI chatbot. The user chooses the strategy; hints never spend resources or decide for the player.

Explore -> Inspect -> Plan -> Advance -> Reflect

A turn is an abstract planning step, not a measured Martian day. Exploring, reading and revising a plan do not advance the mission.

1. **Arrive and meet the crew.** Watch or skip the illustrative Earth-to-Mars arrival. Follow the destination marker and talk to the crew to begin the guided objectives.

2. **Inspect the systems.** Visit the power station, life-support unit, water storage, greenhouse and lab. Each panel introduces one decision and its cost.

3. **Prepare a plan.** Power or pause oxygen production and growing lights, then choose one crew task: research, rover sampling, shelter, a shield upgrade, Earth advice or conserving power. Some tasks unlock later.

4. **Compare the forecast.** See the projected resource changes and warnings before acting. Revise an unsafe or unaffordable plan. Only Advance turn commits the choice.

5. **Respond to changing conditions.** Solar-radiation warnings make protection important. A dust event lowers solar generation. Rover sampling uses extra water; Earth advice arrives on the next turn.

6. **Review and retry.** A debrief compares crew safety, research, samples and reserves. Replay to try another strategy or use independent mode after understanding the controls.

## What counts as success?

Finish six turns with oxygen, water and food above zero, exposure no higher than 12 game points, at least three research objectives and one field sample. Other outcomes distinguish a safe return without all science goals from a mission needing rescue. These thresholds are teaching rules, not astronaut health limits.


---

# One decision, a visible result

**Input:** on turn 1, keep oxygen production and growing lights powered, and assign the crew to lab research. **Processing:** the game calculates generation, battery capacity, system costs, consumption and the crew task. **Output:** it commits one history record and explains the changed reserves.

Figure: Before acting: the power controls compare planned oxygen settings. A preview is not a completed action.

| Measure | Before | After | Explanation |
| --- | --- | --- | --- |
| Energy | 12 | 5 | 10 generated; storage capped at 20; 15 spent. |
| Oxygen | 48 | 48 | 12 produced and 12 consumed. |
| Water | 12 | 10 | One for the crew, one for plant growth. |
| Food packs | 5 | 4 | One consumed; the first growth turn has no harvest. |
| Research | 0 | 1 | The lab completes one objective. |
| Exposure | 0 | 1 | One fictional game exposure point is added. |

This outcome was captured from the running prototype and matches its saved turn record. Keeping oxygen stable still costs electricity. Growing plants spends water now for a later harvest. Research also consumes energy, making the trade-off visible.

Evidence: captured result and saved state in the local demo evidence; simulation logic in src/domain/mission.ts. All numerical values above are game units, not NASA instrument data.

## What the player can learn

The goal is to connect a choice to its consequence and explain why survival and science cannot be planned separately. The example demonstrates software behaviour; it does not prove improved learning or real-world mission safety.


---

# Implementation, progress and limits

## Working in the local prototype

The current build includes guided arrival and crew conversations, walking and overview cameras, selectable facilities, resource forecasts, a six-turn mission, radiation and dust events, rover-route planning and sample collection, delayed Earth hints, save/resume, a debrief and a science library. Camera and rover routes are illustrative. Water-recycling equipment is visible but does not produce an extra water resource.

| Layer | Tools and purpose |
| --- | --- |
| Interface | React and TypeScript: contextual panels, readable dialogue and guided objectives. |
| 3D world | Three.js, React Three Fiber and Drei: models, cameras, lighting and interactions. |
| Rules and saving | Pure TypeScript calculations; browser local storage; Zod checks save and evidence structure. |
| Assets | Blender and Python: original procedural geometry; portable GLB model exports. |
| Development | Vite and Node.js 24; Vitest tests; Playwright browser automation; ESLint and GitHub Actions. |

## Evidence and accessibility

All 44 local unit, data and asset checks passed on 14 November 2026. They cover mission logic, guidance, exploration and source/model consistency. A documented earlier browser run passed 14 desktop/mobile-emulation checks; the final recovery-message patch has an outstanding browser rerun. We do not claim a completely verified final browser suite.

Keyboard and touch controls, large interaction targets, reduced-motion support, lower rendering quality, an alternative 2D mission map and replayable guidance are implemented. Mobile emulation and automated accessibility checks do not establish real-device performance or full screen-reader accessibility.

## Limits and next steps

The prototype has no explorable building interiors, free rover driving, live space-weather feed or measured Mars terrain. Crew models share an articulated suit design. Mission timings and balances are authored, and current game dialogue is text rather than the demo narrator.

Next steps are supervised learner sessions, manual keyboard and screen-reader checks, testing on ordinary phones and laptops and other browsers, and publishing a stable version. We would evaluate whether learners can explain one resource trade-off before and after playing, then revise the guidance. These are planned evaluations, not completed results.


---

# NASA science used in the game

The project stores selected, archived evidence locally. Source records were acquired/reviewed on 13 November 2026; no live NASA API is required while playing.

## 1. MOXIE: producing oxygen on Mars

**Source:** NASA/JPL-Caltech, MOXIE mission-completion article, 6 September 2023. The demonstration aboard Perseverance separated oxygen from atmospheric carbon dioxide. **Use:** the life-support explanation connects oxygen production to spending electricity. **Boundary:** the game is not a MOXIE performance model; its crew-scale plant, energy costs and oxygen yields are fictional.

[MOXIE mission-completion article](https://www.nasa.gov/missions/mars-2020-perseverance/perseverance-rover/nasas-oxygen-generating-experiment-moxie-completes-mars-mission/)

## 2. RadLab: archived radiation observations

**Source:** NASA OSDR RadLab, ISS DosTel1 absorbed-dose-rate records from 1 April 2022, 23:00-23:05. A dosimeter measures radiation exposure. **Use:** four archived readings appear in a contextual chart to show that radiation changes over time. **Boundary:** these are ISS readings in microgray/hour, not Mars measurements, medical risk estimates or game exposure points.

RadLab observations: 9.815504; 9.835079; 7.949537; 6.228811 microgray/hour.

Chart labels are rounded to two decimals. Stored observations: 9.815504, 9.835079, 7.949537 and 6.228811 microgray/hour. Equal spacing shows observation order, not elapsed time. Chart generated with AI assistance; measurements are unchanged.

[RadLab data API and instrument contributor information](https://visualization.osdr.nasa.gov/radlab/gui/data-api/)

## 3. OSD-314: plant responses to light and gravity

**Source:** NASA Open Science Data Repository (OSDR), OSD-314 version 7, and Villacampa et al. (2021), DOI 10.3390/ijms22020899. Researchers studied Arabidopsis seedlings under controlled spaceflight and reduced-gravity conditions. **Use:** the greenhouse lesson explains why lighting matters and competes for power. **Boundary:** the game does not analyse raw gene-expression files or predict edible crop yields. A two-turn harvest is a teaching rule.

[OSD-314 study](https://osdr.nasa.gov/bio/repo/data/studies/OSD-314)

[Villacampa et al. - peer-reviewed research paper](https://www.mdpi.com/1422-0067/22/2/899)


---

# Space context and responsible use

## 4. DONKI: an archived solar warning

**Source:** NASA CCMC / Moon to Mars Space Weather Analysis Office, DONKI event 2024-05-10T06:27:00-FLR-001. GOES-P EXIS recorded an X3.9 flare on 10 May 2024; its listed peak was 06:54 UTC. **Use:** an archived example supports the solar-warning explanation. **Boundary:** flare class does not establish radiation dose or arrival at the Mars outpost. The game event schedule and exposure points are fictional.

[DONKI event and GOES observation record](https://ccmc.gsfc.nasa.gov/DONKI/events/30666/2/)

## 5. Perseverance: a real view of Jezero Crater

**Source:** image PIA24485, Perseverance Mastcam-Z, acquired 22 February 2021 and added to the catalogue on 5 March 2021. **Use:** the local image in the science library gives real geological context to a fictional rover sample task. It does not define the outpost terrain, route or landing location.

Figure: Real Mars image: Jezero delta remnant. Credit NASA/JPL-Caltech/ASU/MSSS, PIA24485. This photograph is not AI-generated.

[NASA image record and credit](https://images.nasa.gov/details/PIA24485)

## Other agency resource: Canadian Space Agency

The CSA toolkit Food production on the Moon and in remote areas informs the food-planning explanation: astronauts need food systems that work away from Earth. It is an educational resource, not a crop-performance dataset. We wrote a short game summary; the greenhouse costs and meal yields are original teaching rules.

[CSA food-production toolkit](https://www.asc-csa.gc.ca/eng/youth-educators/toolkits/food-production/)

## How the evidence was prepared

We retained source names, links, record IDs, dates, units, credits and limitations. Four RadLab rows were stored as structured text data (JSON) without changing their measurement values. OSD-314 metadata and its paper support a bounded explanation. A small NASA image derivative is loaded locally. Scientific observations remain separate from the game rules; no synthetic NASA dataset or live forecast is claimed.


---

# Brainstorming and AI/SI disclosure

## Miro: our brainstorming and planning workspace

We used Miro to brainstorm and organize the project concept. The board connects the Commander role, crew introductions, base facilities, starting resources, protection and player decisions. Its scenario flowchart helped make the relationship between survival, food, research and exploration visible. We used it as a planning reference, not as scientific data or evidence that every proposed feature works.

[Open the team brainstorming board](https://miro.com/app/board/uXjVEQ0HwG8=/?share_link_id=199039016859)

The board retains early Moon-base wording and exploratory ideas such as extra zones and repair activities. The current deliverable is the Mars prototype described here. Those planning notes are not claims of a playable Moon mission, a repair system or unlocked multi-region exploration. The current mission rules and observed behaviour define this document.

## Tools that used AI or SI

| Tool | Task and affected work |
| --- | --- |
| OpenAI Codex | Assisted workflow and interface iteration, game code, dialogue drafts, procedural Blender/Python asset scripts, tests, documentation and demo motion graphics/music scripts. Code, artwork, explanatory text and presentation files are affected. |
| ElevenLabs | Generated the supplied English demo narration, using Dmitry - Energetic and Confident. It appears in the demo, not as a live in-game voice. |
| OpenAI Whisper | Local speech recognition helped align demo captions to the supplied narration. On-screen spelling follows the approved script; low-confidence transcription errors were excluded. |

Blender produced the procedural models; Python and FFmpeg synthesized the score and composited the demo; Miro organized planning. The background score and effects were created from original code with AI assistance, with no imported stock music samples.

## What is generated, and what is observed?

AI assistance is acknowledged for generated code, scripts, prose, procedural artwork and demo audio/graphics. Screenshots and diagrams in this PDF carry visible labels where applicable. The supplied demo has a visible AI-visuals label and audio acknowledgements in its description and metadata. Real NASA/partner observations are credited and have not been replaced by invented measurements. No NASA logos or flags were added to generated artwork.

This PDF records the known tool uses. The accompanying disclosure JSON provides a machine-readable record of the affected work, source data and prototype status.


---

# Credits and how to review the project

## Other resources and tools

| Resource | Use and credit |
| --- | --- |
| Solar System Scope / INOVE | [Earth and Mars maps](https://www.solarsystemscope.com/textures/), CC BY 4.0. Resized to 1K Earth / 2K Mars and used on illustrative globes. Colours and gap-filling reflect the provider's artistic processing; these are not precision terrain data. |
| Blender and Python | [Blender](https://www.blender.org/) and [Python](https://www.python.org/) were used for procedural game assets and preparation scripts. GLB is the portable 3D model format used by the browser. |
| Web implementation | [React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Three.js](https://threejs.org/), [React Three Fiber](https://github.com/pmndrs/react-three-fiber), [Drei](https://github.com/pmndrs/drei), [Zod](https://zod.dev/) and [Lucide](https://lucide.dev/) support the interface, 3D world, validation and icons. Retain their distributed notices. |
| Build and verification | [Vite](https://vite.dev/), [Node.js](https://nodejs.org/), [Vitest](https://vitest.dev/), [Playwright](https://playwright.dev/), [ESLint](https://eslint.org/) and [GitHub Actions](https://github.com/features/actions) support builds and checks. |
| Fonts and demo export | Manrope / Manrope Project Authors and DM Sans / DM Sans Project Authors, SIL Open Font License 1.1. [FFmpeg](https://ffmpeg.org/), NumPy and Pillow support the demo score, compositing and export. Font licence copies are supplied with the demo sources. |
| Paper and photo credits | Villacampa, Ciska, Manzano, Vandenbrink, Kiss, Herranz and Medina (2021), OSD-314 paper. NASA/JPL-Caltech/ASU/MSSS, Jezero image PIA24485. NASA OSDR/DosTel and NASA CCMC/M2M/GOES observation contributors. |

## Project links and access status

**Brainstorming:** [Miro board](https://miro.com/app/board/uXjVEQ0HwG8=/?share_link_id=199039016859). **Source repository:** [m-thabet/marsastro](https://github.com/m-thabet/marsastro). A source repository does not open a running game; ensure its published revision includes the current local changes before using it for review.

**Not supplied for this document:** a public playable-game URL, the public 29.5-second demo link and the NASA Project-page URL. The local video and local browser address are not public judge-access links. Add and test these links before submitting; check guest access to the Miro board too.

## Run the supplied current project files

Install Node.js 24. In the project folder, run `npm ci`, then `npm run dev`, and open `http://127.0.0.1:5173`. Walk with WASD/arrows, drag to look and press E near a marker, or use tap controls and Overview. Use Plan to compare choices. Open Science library for source details; Settings offers lower quality, guided/independent mode and the alternative mission map.

Before submission: publish and test the current game, upload the demo and this PDF with viewing access that requires no sign-in, include the generated-audio description/credits, and keep the project-page, demo, PDF and actual game consistent. This document reports the local prototype; hosting and learner validation are separate pending steps.


---
