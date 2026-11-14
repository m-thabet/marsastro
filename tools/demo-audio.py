import asyncio,json
from pathlib import Path
import edge_tts

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/demo'
LINES=[
 (0.25,2.7,"We're plus C."),
 (2.85,6,"Our challenge: Junior Astronaut Mission Trainer."),
 (6.15,10,"Space survival is hard to teach. Meet Mars Mission Commander."),
 (10.15,15,"Explore, balance oxygen and power, and see your choices change the mission."),
 (15.15,19,"Protect your crew. Grow food. Discover Mars."),
 (19.15,24.6,"NASA's MOXIE, RadLab, and plant research connect decisions to real science."),
 (24.75,29.35,"A playable prototype helping young explorers learn by doing."),
]
async def main():
 for i,(a,b,line) in enumerate(LINES):
  target=OUT/'source'/f'voice-{i}.mp3'
  if not target.exists():
   await edge_tts.Communicate(line,'en-US-GuyNeural',rate='+8%',pitch='-3Hz').save(str(target))
  print(i,line,flush=True)
 (OUT/'source'/'narration.json').write_text(json.dumps(LINES,indent=2))
asyncio.run(main())
