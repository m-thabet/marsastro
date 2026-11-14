# Mars Mission Commander — demo

Team: **plus c**. Challenge: **Junior Astronaut Mission Trainer**.

The current deliverable is `Mars-Mission-Commander-Demo-Submission.mp4`: 29.5 seconds, 1920×1080, 16:9, 30 fps, H.264 video with stereo AAC audio. It uses the replacement 27.402-second voiceover, an original space-adventure score, and captions retimed to the new speech. The voice runs at its original speed. Music is approximately 15 dB below speech during narration and rises in pauses. The bottom progress bar is retained without timer numbers. A small AI-visuals label and generated-audio metadata acknowledgement meet the supplied guide's disclosure requirements. English captions are burned into the picture; `Mars-Mission-Commander-Submission.srt` is the separate caption file. The MP4 is optimized for streaming. Previous exports are retained.

Use `Submission-description.txt` when uploading and see `Guidelines-check.md` for the content check and remaining public-link steps.

## Upload description

Team plus c presents Mars Mission Commander, a playable educational prototype for the Junior Astronaut Mission Trainer challenge. Players explore an illustrated Mars outpost, balance limited resources, and see the results of their choices. NASA's MOXIE demonstration, archived ISS radiation observations, and plant research inform the learning content. Mission timings, resource rates and exposure points are fictional training rules, not measurements of a real Mars mission.

AI disclosure: AI-generated narration was supplied by the team using ElevenLabs, voice “Dmitry — Energetic and Confident.” The demo includes AI-assisted motion graphics and procedural game artwork. The score and sound effects are original procedural compositions; they are not recordings of space or of Mars. No NASA endorsement is implied.

Science credits: NASA/JPL-Caltech (MOXIE); NASA OSDR / DosTel contributors (RadLab); Villacampa, Ciska, Manzano, Vandenbrink, Kiss, Herranz and Medina (2021), OSD-314. Globe textures: Solar System Scope / INOVE, CC BY 4.0, adapted with resizing, rotation, lighting and color treatment. Game buildings, characters and terrain are illustrative project assets. Manrope and DM Sans fonts are licensed under SIL OFL 1.1.

## Sources used in the video

- Game evidence records: `src/data/evidence.ts`; radiation values: `src/data/radlab.json`.
- [NASA / JPL-Caltech — MOXIE mission completion](https://www.nasa.gov/missions/mars-2020-perseverance/perseverance-rover/nasas-oxygen-generating-experiment-moxie-completes-mars-mission/).
- [NASA OSDR RadLab](https://visualization.osdr.nasa.gov/radlab/gui/data-api/). The plotted values are the game's four archived ISS DosTel1 readings from 1 April 2022: 9.815504, 9.835079, 7.949537, and 6.228811 microgray/hour. Points are equally spaced by observation order, not elapsed time. These are ISS readings, not Mars radiation measurements.
- [NASA OSDR — OSD-314](https://osdr.nasa.gov/bio/repo/data/studies/OSD-314); [Villacampa et al. (2021)](https://www.mdpi.com/1422-0067/22/2/899). The study concerns seedlings in controlled space experiments, not edible crops grown on Mars.
- [Solar System Scope / INOVE textures](https://www.solarsystemscope.com/textures/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Local Earth and Mars game textures appear in captured footage; the rotating planet uses the game's Mars texture.
- Original reference renders: `Assets/previews/life-support-reference-module.png` and `greenhouse-reference-module.png`. They are labeled as illustrative game assets and are not photographs of NASA hardware.
- Original game audio: `Assets/audio/space-ambience.wav`, `ui-select.wav`, `ui-confirm.wav`, `radio-message.wav`, and `discovery.wav`.
- Fonts: Manrope / Manrope Project Authors; DM Sans / DM Sans Project Authors. License copies are included under `source/`.

## Edit and timing

0–1.65: team introduction and rotating Mars. 1.65–5.25: challenge. 5.25–9.80: problem and project. 9.80–16.95: explore, allocation and actual turn result. 16.95–22.95: scientific sources and archived radiation chart. 22.95–27.80: intended learning benefit. 27.80–29.50: closing brand. Globe-map attribution is visible for the final 6.55 seconds.

The replacement user-supplied 27.402-second narration starts at 0.20 seconds and ends at 27.602 seconds. Speech timing was checked against local transcription and silence boundaries. On-screen spelling follows the approved script, correcting transcription errors in proper names. The voice has not been time-stretched. The low-confidence, zero-duration transcription hallucinations after the last sentence were excluded from captions.

Gameplay is captured from the running local application. Short camera/UI clips are accelerated for the edit; still captures have gentle framing motion. The turn-result callouts match the saved state produced by a real turn: energy 12 to 5, water 12 to 10, and research 0 to 1. The camera clips and illustrations are editorial presentation, not additional game features.

## Reproduce or revise

- `tools/render-demo.py`: editable timeline, graphics, captions and final export. `tools/demo_score.py` creates the original music, effects and voice mix. Requires Python, NumPy, Pillow and FFmpeg. Font files are under `source/`.
- `python tools/render-demo.py --preview` renders a storyboard and full-size frame previews.
- `python tools/render-demo.py --audio-only` rebuilds the narration/effects mix.
- `python tools/render-demo.py` rebuilds the complete submission MP4 from the supplied voice path. A copy of the replacement source is kept as `source/voiceover-current.mp3`; the earlier source is preserved separately.
- `python tools/verify-demo.py --submission` checks the exported submission video, replacement voice, music balance, disclosure metadata and audio levels, and creates a contact sheet from actual video frames.
- `tools/capture-demo-details.mjs` captures the overview, a real plan change, an actual turn outcome and the science library through Playwright. The original capture and state evidence are retained in `capture/`.

Publishing is not part of this export. After uploading, use a publicly viewable link and test it without signing in before submission.
