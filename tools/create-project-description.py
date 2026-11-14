"""Create a source-backed, branded project-description PDF and editable Markdown."""
from pathlib import Path
import json,re,html
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,Flowable,KeepTogether
from reportlab.lib.utils import ImageReader
from PIL import Image
import fitz

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/pdf';OUT.mkdir(parents=True,exist_ok=True)
TMP=ROOT/'tmp/pdfs/project-description';TMP.mkdir(parents=True,exist_ok=True)
MIRO='https://miro.com/app/board/uXjVEQ0HwG8=/?share_link_id=199039016859'
REPO='https://github.com/m-thabet/marsastro'
pdfmetrics.registerFont(TTFont('DM',str(ROOT/'output/demo/source/DM-Sans.ttf')))
pdfmetrics.registerFont(TTFont('Manrope',str(ROOT/'output/demo/source/Manrope-Bold.ttf')))
pdfmetrics.registerFontFamily('DM',normal='DM',bold='Manrope',italic='DM',boldItalic='Manrope')
BG=colors.HexColor('#f5f4ef');INK=colors.HexColor('#13272d');MUTED=colors.HexColor('#4c6265')
MINT=colors.HexColor('#8ce0d4');PALE=colors.HexColor('#e4efea');AMBER=colors.HexColor('#d18b46')
PAGE_W,PAGE_H=595.276,841.89;M=43;CW=PAGE_W-2*M
STYLES={
 'body':ParagraphStyle('body',fontName='DM',fontSize=10.7,leading=14.7,textColor=INK,spaceAfter=8),
 'small':ParagraphStyle('small',fontName='DM',fontSize=9.2,leading=12.3,textColor=MUTED,spaceAfter=6),
 'caption':ParagraphStyle('caption',fontName='DM',fontSize=8.7,leading=11.7,textColor=MUTED,spaceAfter=9),
 'h1':ParagraphStyle('h1',fontName='Manrope',fontSize=26,leading=31,textColor=INK,spaceAfter=13),
 'cover':ParagraphStyle('cover',fontName='Manrope',fontSize=36,leading=40,textColor=INK,spaceAfter=10),
 'h2':ParagraphStyle('h2',fontName='Manrope',fontSize=13.4,leading=17,textColor=INK,spaceBefore=7,spaceAfter=6),
 'h3':ParagraphStyle('h3',fontName='Manrope',fontSize=11.2,leading=15,textColor=INK,spaceBefore=5,spaceAfter=4),
 'table':ParagraphStyle('table',fontName='DM',fontSize=9.4,leading=12.4,textColor=INK),
 'tableHead':ParagraphStyle('tableHead',fontName='Manrope',fontSize=9.1,leading=12,textColor=colors.white),
}

def inline(s):
 s=html.escape(s)
 s=re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)',lambda m:f'<link href="{m[2]}" color="#205d5a"><u>{m[1]}</u></link>',s)
 s=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',s)
 s=re.sub(r'`([^`]+)`',r'<font name="Manrope">\1</font>',s)
 return s.replace('\n','<br/>')
def P(s,style='body'):return Paragraph(inline(s),STYLES[style])

class Figure(Flowable):
 def __init__(self,path,height,ai=True):
  super().__init__();self.path=ROOT/path;self.width=CW;self.height=height;self.ai=ai
 def draw(self):
  c=self.canv;c.setFillColor(INK);c.roundRect(0,0,self.width,self.height,8,fill=1,stroke=0)
  iw,ih=Image.open(self.path).size;scale=min(self.width/iw,self.height/ih)
  w,h=iw*scale,ih*scale
  c.drawImage(ImageReader(str(self.path)),(self.width-w)/2,(self.height-h)/2,w,h,mask='auto')
  if self.ai:
   label='AI-GENERATED GAME VISUALS';f=7.6;lw=pdfmetrics.stringWidth(label,'Manrope',f)+14
   c.setFillColor(INK);c.roundRect(self.width-lw-7,7,lw,18,4,fill=1,stroke=0)
   c.setFont('Manrope',f);c.setFillColor(MINT);c.drawString(self.width-lw,13,label)

class Loop(Flowable):
 def __init__(self):super().__init__();self.width=CW;self.height=80
 def draw(self):
  c=self.canv;labels=[('EXPLORE','Find a facility'),('INSPECT','Read the trade-off'),('PLAN','Compare reserves'),('ADVANCE','Commit one turn'),('REFLECT','See the outcome')]
  for i,(a,b) in enumerate(labels):
   x=i*103;c.setFillColor(INK);c.roundRect(x,27,94,42,7,fill=1,stroke=0)
   c.setFillColor(MINT);c.setFont('Manrope',9);c.drawString(x+9,53,a)
   c.setFillColor(colors.white);c.setFont('DM',7.8);c.drawString(x+9,38,b)
   if i<4:
    c.setStrokeColor(AMBER);c.setLineWidth(1.2);c.line(x+96,48,x+102,48);c.line(x+99,51,x+102,48);c.line(x+99,45,x+102,48)
  c.setFillColor(MUTED);c.setFont('DM',7.6);c.drawRightString(CW,9,'AI-GENERATED DIAGRAM / FICTIONAL GAME RULES')

class RadChart(Flowable):
 def __init__(self):super().__init__();self.width=CW;self.height=109
 def draw(self):
  c=self.canv;rows=json.loads((ROOT/'src/data/radlab.json').read_text())['data']
  c.setFillColor(PALE);c.roundRect(0,0,CW,109,7,fill=1,stroke=0)
  c.setFillColor(INK);c.setFont('Manrope',8.6);c.drawString(12,94,'ISS DosTel1 / 1 April 2022 / absorbed dose rate in microgray/hour')
  for n in [6,8,10]:
   y=23+(n-6)*12;c.setStrokeColor(colors.HexColor('#c8dbd2'));c.line(23,y,CW-23,y)
  points=[(34+i*143,23+(r[2]-6)*12) for i,r in enumerate(rows)]
  c.setStrokeColor(colors.HexColor('#207c72'));c.setLineWidth(1.8)
  for a,b in zip(points,points[1:]):c.line(*a,*b)
  for i,((x,y),row) in enumerate(zip(points,rows)):
   c.setFillColor(INK);c.circle(x,y,2.5,fill=1,stroke=0);c.setFont('Manrope',8.6);c.drawCentredString(x,y+8,f'{row[2]:.2f}')
   c.setFont('DM',7.6);c.drawCentredString(x,9,f'Reading {i+1}')

PAGES=[
 {'title':'Mars Mission\nCommander','cover':True,'nodes':[
 ('p','**Team:** plus c  |  **Challenge:** Junior Astronaut Mission Trainer'),
 ('small','Playable educational prototype / Cairo 2026 / 14 November 2026'),
 ('image','output/demo/capture/overview.png',242,True,'Current prototype: an illustrated Mars outpost with selectable facilities, crew and resource decisions.'),
 ('h2','What we built'),
 ('p','Mars Mission Commander is a browser game that lets young explorers lead a six-turn Mars training mission. Players explore a 3D outpost, meet their crew, allocate electricity, manage oxygen, water and food, and choose between science and protection. Each committed decision changes the mission and receives a short explanation. NASA observations and research appear in contextual science cards, with clear boundaries between real evidence and fictional game rules.'),
 ('h2','The problem and the challenge'),
 ('p','Space survival is difficult to teach through facts alone: producing oxygen, growing food and protecting a crew compete for limited resources. Our response to the challenge is a place to practise those connected decisions. The intended audience is young learners, especially ages 7-12, with potential use in classrooms, science clubs and family learning. This age range and educational benefit still require learner testing.'),
 ]},
 {'title':'How the experience works','nodes':[
 ('p','The player is the Commander. Dr. Maya introduces science, Alex explains engineering, and NOVA provides guidance. NOVA is a scripted character, not a live AI chatbot. The user chooses the strategy; hints never spend resources or decide for the player.'),
 ('flow',),
 ('caption','A turn is an abstract planning step, not a measured Martian day. Exploring, reading and revising a plan do not advance the mission.'),
 ('steps',[
  ('Arrive and meet the crew','Watch or skip the illustrative Earth-to-Mars arrival. Follow the destination marker and talk to the crew to begin the guided objectives.'),
  ('Inspect the systems','Visit the power station, life-support unit, water storage, greenhouse and lab. Each panel introduces one decision and its cost.'),
  ('Prepare a plan','Power or pause oxygen production and growing lights, then choose one crew task: research, rover sampling, shelter, a shield upgrade, Earth advice or conserving power. Some tasks unlock later.'),
  ('Compare the forecast','See the projected resource changes and warnings before acting. Revise an unsafe or unaffordable plan. Only Advance turn commits the choice.'),
  ('Respond to changing conditions','Solar-radiation warnings make protection important. A dust event lowers solar generation. Rover sampling uses extra water; Earth advice arrives on the next turn.'),
  ('Review and retry','A debrief compares crew safety, research, samples and reserves. Replay to try another strategy or use independent mode after understanding the controls.'),
 ]),
 ('h2','What counts as success?'),
 ('p','Finish six turns with oxygen, water and food above zero, exposure no higher than 12 game points, at least three research objectives and one field sample. Other outcomes distinguish a safe return without all science goals from a mission needing rescue. These thresholds are teaching rules, not astronaut health limits.'),
 ]},
 {'title':'One decision, a visible result','nodes':[
 ('p','**Input:** on turn 1, keep oxygen production and growing lights powered, and assign the crew to lab research. **Processing:** the game calculates generation, battery capacity, system costs, consumption and the crew task. **Output:** it commits one history record and explains the changed reserves.'),
 ('image','output/demo/capture/allocate.png',166,True,'Before acting: the power controls compare planned oxygen settings. A preview is not a completed action.'),
 ('table',['Measure','Before','After','Explanation'],[
  ['Energy','12','5','10 generated; storage capped at 20; 15 spent.'],
  ['Oxygen','48','48','12 produced and 12 consumed.'],
  ['Water','12','10','One for the crew, one for plant growth.'],
  ['Food packs','5','4','One consumed; the first growth turn has no harvest.'],
  ['Research','0','1','The lab completes one objective.'],
  ['Exposure','0','1','One fictional game exposure point is added.'],
 ],[82,54,54,319]),
 ('p','This outcome was captured from the running prototype and matches its saved turn record. Keeping oxygen stable still costs electricity. Growing plants spends water now for a later harvest. Research also consumes energy, making the trade-off visible.'),
 ('small','Evidence: captured result and saved state in the local demo evidence; simulation logic in src/domain/mission.ts. All numerical values above are game units, not NASA instrument data.'),
 ('h2','What the player can learn'),
 ('p','The goal is to connect a choice to its consequence and explain why survival and science cannot be planned separately. The example demonstrates software behaviour; it does not prove improved learning or real-world mission safety.'),
 ]},
 {'title':'Implementation, progress and limits','nodes':[
 ('h2','Working in the local prototype'),
 ('p','The current build includes guided arrival and crew conversations, walking and overview cameras, selectable facilities, resource forecasts, a six-turn mission, radiation and dust events, rover-route planning and sample collection, delayed Earth hints, save/resume, a debrief and a science library. Camera and rover routes are illustrative. Water-recycling equipment is visible but does not produce an extra water resource.'),
 ('table',['Layer','Tools and purpose'],[
  ['Interface','React and TypeScript: contextual panels, readable dialogue and guided objectives.'],
  ['3D world','Three.js, React Three Fiber and Drei: models, cameras, lighting and interactions.'],
  ['Rules and saving','Pure TypeScript calculations; browser local storage; Zod checks save and evidence structure.'],
  ['Assets','Blender and Python: original procedural geometry; portable GLB model exports.'],
  ['Development','Vite and Node.js 24; Vitest tests; Playwright browser automation; ESLint and GitHub Actions.'],
 ],[95,414]),
 ('h2','Evidence and accessibility'),
 ('p','All 44 local unit, data and asset checks passed on 14 November 2026. They cover mission logic, guidance, exploration and source/model consistency. A documented earlier browser run passed 14 desktop/mobile-emulation checks; the final recovery-message patch has an outstanding browser rerun. We do not claim a completely verified final browser suite.'),
 ('p','Keyboard and touch controls, large interaction targets, reduced-motion support, lower rendering quality, an alternative 2D mission map and replayable guidance are implemented. Mobile emulation and automated accessibility checks do not establish real-device performance or full screen-reader accessibility.'),
 ('h2','Limits and next steps'),
 ('p','The prototype has no explorable building interiors, free rover driving, live space-weather feed or measured Mars terrain. Crew models share an articulated suit design. Mission timings and balances are authored, and current game dialogue is text rather than the demo narrator.'),
 ('p','Next steps are supervised learner sessions, manual keyboard and screen-reader checks, testing on ordinary phones and laptops and other browsers, and publishing a stable version. We would evaluate whether learners can explain one resource trade-off before and after playing, then revise the guidance. These are planned evaluations, not completed results.'),
 ]},
 {'title':'NASA science used in the game','nodes':[
 ('small','The project stores selected, archived evidence locally. Source records were acquired/reviewed on 13 November 2026; no live NASA API is required while playing.'),
 ('h2','1. MOXIE: producing oxygen on Mars'),
 ('p','**Source:** NASA/JPL-Caltech, MOXIE mission-completion article, 6 September 2023. The demonstration aboard Perseverance separated oxygen from atmospheric carbon dioxide. **Use:** the life-support explanation connects oxygen production to spending electricity. **Boundary:** the game is not a MOXIE performance model; its crew-scale plant, energy costs and oxygen yields are fictional.'),
 ('link','MOXIE mission-completion article','https://www.nasa.gov/missions/mars-2020-perseverance/perseverance-rover/nasas-oxygen-generating-experiment-moxie-completes-mars-mission/'),
 ('h2','2. RadLab: archived radiation observations'),
 ('p','**Source:** NASA OSDR RadLab, ISS DosTel1 absorbed-dose-rate records from 1 April 2022, 23:00-23:05. A dosimeter measures radiation exposure. **Use:** four archived readings appear in a contextual chart to show that radiation changes over time. **Boundary:** these are ISS readings in microgray/hour, not Mars measurements, medical risk estimates or game exposure points.'),
 ('chart',),
 ('caption','Chart labels are rounded to two decimals. Stored observations: 9.815504, 9.835079, 7.949537 and 6.228811 microgray/hour. Equal spacing shows observation order, not elapsed time. Chart generated with AI assistance; measurements are unchanged.'),
 ('link','RadLab data API and instrument contributor information','https://visualization.osdr.nasa.gov/radlab/gui/data-api/'),
 ('h2','3. OSD-314: plant responses to light and gravity'),
 ('p','**Source:** NASA Open Science Data Repository (OSDR), OSD-314 version 7, and Villacampa et al. (2021), DOI 10.3390/ijms22020899. Researchers studied Arabidopsis seedlings under controlled spaceflight and reduced-gravity conditions. **Use:** the greenhouse lesson explains why lighting matters and competes for power. **Boundary:** the game does not analyse raw gene-expression files or predict edible crop yields. A two-turn harvest is a teaching rule.'),
 ('link','OSD-314 study','https://osdr.nasa.gov/bio/repo/data/studies/OSD-314'),
 ('link','Villacampa et al. - peer-reviewed research paper','https://www.mdpi.com/1422-0067/22/2/899'),
 ]},
 {'title':'Space context and responsible use','nodes':[
 ('h2','4. DONKI: an archived solar warning'),
 ('p','**Source:** NASA CCMC / Moon to Mars Space Weather Analysis Office, DONKI event 2024-05-10T06:27:00-FLR-001. GOES-P EXIS recorded an X3.9 flare on 10 May 2024; its listed peak was 06:54 UTC. **Use:** an archived example supports the solar-warning explanation. **Boundary:** flare class does not establish radiation dose or arrival at the Mars outpost. The game event schedule and exposure points are fictional.'),
 ('link','DONKI event and GOES observation record','https://ccmc.gsfc.nasa.gov/DONKI/events/30666/2/'),
 ('h2','5. Perseverance: a real view of Jezero Crater'),
 ('p','**Source:** image PIA24485, Perseverance Mastcam-Z, acquired 22 February 2021 and added to the catalogue on 5 March 2021. **Use:** the local image in the science library gives real geological context to a fictional rover sample task. It does not define the outpost terrain, route or landing location.'),
 ('image','public/assets/jezero-delta.jpg',132,False,'Real Mars image: Jezero delta remnant. Credit NASA/JPL-Caltech/ASU/MSSS, PIA24485. This photograph is not AI-generated.'),
 ('link','NASA image record and credit','https://images.nasa.gov/details/PIA24485'),
 ('h2','Other agency resource: Canadian Space Agency'),
 ('p','The CSA toolkit Food production on the Moon and in remote areas informs the food-planning explanation: astronauts need food systems that work away from Earth. It is an educational resource, not a crop-performance dataset. We wrote a short game summary; the greenhouse costs and meal yields are original teaching rules.'),
 ('link','CSA food-production toolkit','https://www.asc-csa.gc.ca/eng/youth-educators/toolkits/food-production/'),
 ('h2','How the evidence was prepared'),
 ('p','We retained source names, links, record IDs, dates, units, credits and limitations. Four RadLab rows were stored as structured text data (JSON) without changing their measurement values. OSD-314 metadata and its paper support a bounded explanation. A small NASA image derivative is loaded locally. Scientific observations remain separate from the game rules; no synthetic NASA dataset or live forecast is claimed.'),
 ]},
 {'title':'Brainstorming and AI/SI disclosure','nodes':[
 ('h2','Miro: our brainstorming and planning workspace'),
 ('p','We used Miro to brainstorm and organize the project concept. The board connects the Commander role, crew introductions, base facilities, starting resources, protection and player decisions. Its scenario flowchart helped make the relationship between survival, food, research and exploration visible. We used it as a planning reference, not as scientific data or evidence that every proposed feature works.'),
 ('link','Open the team brainstorming board',MIRO),
 ('p','The board retains early Moon-base wording and exploratory ideas such as extra zones and repair activities. The current deliverable is the Mars prototype described here. Those planning notes are not claims of a playable Moon mission, a repair system or unlocked multi-region exploration. The current mission rules and observed behaviour define this document.'),
 ('h2','Tools that used AI or SI'),
 ('table',['Tool','Task and affected work'],[
  ['OpenAI Codex','Assisted workflow and interface iteration, game code, dialogue drafts, procedural Blender/Python asset scripts, tests, documentation and demo motion graphics/music scripts. Code, artwork, explanatory text and presentation files are affected.'],
  ['ElevenLabs','Generated the supplied English demo narration, using Dmitry - Energetic and Confident. It appears in the demo, not as a live in-game voice.'],
  ['OpenAI Whisper','Local speech recognition helped align demo captions to the supplied narration. On-screen spelling follows the approved script; low-confidence transcription errors were excluded.'],
 ],[97,412]),
 ('p','Blender produced the procedural models; Python and FFmpeg synthesized the score and composited the demo; Miro organized planning. The background score and effects were created from original code with AI assistance, with no imported stock music samples.'),
 ('h2','What is generated, and what is observed?'),
 ('p','AI assistance is acknowledged for generated code, scripts, prose, procedural artwork and demo audio/graphics. Screenshots and diagrams in this PDF carry visible labels where applicable. The supplied demo has a visible AI-visuals label and audio acknowledgements in its description and metadata. Real NASA/partner observations are credited and have not been replaced by invented measurements. No NASA logos or flags were added to generated artwork.'),
 ('small','This PDF records the known tool uses. The accompanying disclosure JSON provides a machine-readable record of the affected work, source data and prototype status.'),
 ]},
 {'title':'Credits and how to review the project','nodes':[
 ('h2','Other resources and tools'),
 ('table',['Resource','Use and credit'],[
  ['Solar System Scope / INOVE','[Earth and Mars maps](https://www.solarsystemscope.com/textures/), CC BY 4.0. Resized to 1K Earth / 2K Mars and used on illustrative globes. Colours and gap-filling reflect the provider\'s artistic processing; these are not precision terrain data.'],
  ['Blender and Python','[Blender](https://www.blender.org/) and [Python](https://www.python.org/) were used for procedural game assets and preparation scripts. GLB is the portable 3D model format used by the browser.'],
  ['Web implementation','[React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Three.js](https://threejs.org/), [React Three Fiber](https://github.com/pmndrs/react-three-fiber), [Drei](https://github.com/pmndrs/drei), [Zod](https://zod.dev/) and [Lucide](https://lucide.dev/) support the interface, 3D world, validation and icons. Retain their distributed notices.'],
  ['Build and verification','[Vite](https://vite.dev/), [Node.js](https://nodejs.org/), [Vitest](https://vitest.dev/), [Playwright](https://playwright.dev/), [ESLint](https://eslint.org/) and [GitHub Actions](https://github.com/features/actions) support builds and checks.'],
  ['Fonts and demo export','Manrope / Manrope Project Authors and DM Sans / DM Sans Project Authors, SIL Open Font License 1.1. [FFmpeg](https://ffmpeg.org/), NumPy and Pillow support the demo score, compositing and export. Font licence copies are supplied with the demo sources.'],
  ['Paper and photo credits','Villacampa, Ciska, Manzano, Vandenbrink, Kiss, Herranz and Medina (2021), OSD-314 paper. NASA/JPL-Caltech/ASU/MSSS, Jezero image PIA24485. NASA OSDR/DosTel and NASA CCMC/M2M/GOES observation contributors.'],
 ],[112,397]),
 ('h2','Project links and access status'),
 ('p',f'**Brainstorming:** [Miro board]({MIRO}). **Source repository:** [m-thabet/marsastro]({REPO}). A source repository does not open a running game; ensure its published revision includes the current local changes before using it for review.'),
 ('p','**Not supplied for this document:** a public playable-game URL, the public 29.5-second demo link and the NASA Project-page URL. The local video and local browser address are not public judge-access links. Add and test these links before submitting; check guest access to the Miro board too.'),
 ('h2','Run the supplied current project files'),
 ('p','Install Node.js 24. In the project folder, run `npm ci`, then `npm run dev`, and open `http://127.0.0.1:5173`. Walk with WASD/arrows, drag to look and press E near a marker, or use tap controls and Overview. Use Plan to compare choices. Open Science library for source details; Settings offers lower quality, guided/independent mode and the alternative mission map.'),
 ('small','Before submission: publish and test the current game, upload the demo and this PDF with viewing access that requires no sign-in, include the generated-audio description/credits, and keep the project-page, demo, PDF and actual game consistent. This document reports the local prototype; hosting and learner validation are separate pending steps.'),
 ]},
]

def table_node(headers,rows,widths):
 widths=[x*CW/sum(widths) for x in widths]
 data=[[Paragraph(inline(x),STYLES['tableHead']) for x in headers]]+[[Paragraph(inline(x),STYLES['table']) for x in row] for row in rows]
 t=Table(data,colWidths=widths,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),INK),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#c6d4cd'))]))
 return [t,Spacer(1,9)]

def page_chrome(c,doc):
 c.saveState();c.setFillColor(BG);c.rect(0,0,PAGE_W,PAGE_H,fill=1,stroke=0)
 c.setFillColor(INK);c.rect(0,PAGE_H-65,PAGE_W,65,fill=1,stroke=0)
 c.setFillColor(colors.HexColor('#fff5e3'));c.setFont('Manrope',24);c.drawString(M,PAGE_H-43,'M')
 c.setFillColor(AMBER);c.circle(M+24,PAGE_H-34,3,fill=1,stroke=0)
 c.setFillColor(colors.white);c.setFont('Manrope',11);c.drawString(M+38,PAGE_H-34,'MARS')
 c.setFont('DM',6.9);c.drawString(M+38,PAGE_H-45,'MISSION COMMANDER')
 c.setFillColor(MINT);c.setFont('DM',8.3);c.drawRightString(PAGE_W-M,PAGE_H-35,'plus c / PROJECT DESCRIPTION')
 c.setStrokeColor(colors.HexColor('#cbd8d2'));c.line(M,46,PAGE_W-M,46)
 c.setFillColor(MUTED);c.setFont('DM',8.2);c.drawString(M,30,'Cairo 2026 / Playable prototype / 14 November 2026')
 c.setFont('Manrope',9);c.drawRightString(PAGE_W-M,29,f'{doc.page:02}')
 c.restoreState()

def create():
 story=[];md=[]
 for pi,page in enumerate(PAGES):
  if pi:story.append(PageBreak())
  story.append(P(page['title'],'cover' if page.get('cover') else 'h1'))
  md.append('# '+page['title'].replace('\n',' ')+'\n')
  for node in page['nodes']:
   kind=node[0]
   if kind in ['p','small','caption','h2']:
    story.append(P(node[1], 'body' if kind=='p' else kind))
    md.append(('## ' if kind=='h2' else '')+node[1]+'\n')
   elif kind=='link':
    story.append(P(f'[{node[1]}]({node[2]})','small'));md.append(f'[{node[1]}]({node[2]})\n')
   elif kind=='image':
    story += [Figure(node[1],node[2],node[3]),Spacer(1,5),P(node[4],'caption')]
    md.append('Figure: '+node[4]+'\n')
   elif kind=='table':
    story+=table_node(node[1],node[2],node[3]);md.append('| '+' | '.join(node[1])+' |\n| '+' | '.join(['---']*len(node[1]))+' |')
    md += ['| '+' | '.join(row)+' |' for row in node[2]];md.append('')
   elif kind=='steps':
    for i,(title,desc) in enumerate(node[1]):
     story.append(P(f'**{i+1}. {title}.** {desc}'));md.append(f'{i+1}. **{title}.** {desc}\n')
   elif kind=='flow':
    story.append(Loop());md.append('Explore -> Inspect -> Plan -> Advance -> Reflect\n')
   elif kind=='chart':
    story += [RadChart(),Spacer(1,5)];md.append('RadLab observations: 9.815504; 9.835079; 7.949537; 6.228811 microgray/hour.\n')
  md.append('\n---\n')
 file=OUT/'Mars-Mission-Commander-Project-Description.pdf'
 doc=SimpleDocTemplate(str(file),pagesize=(PAGE_W,PAGE_H),rightMargin=M,leftMargin=M,topMargin=86,bottomMargin=62,title='Mars Mission Commander - Project Description',author='plus c',subject='Junior Astronaut Mission Trainer. AI-assisted document, code and procedural game art; ElevenLabs demo narration; Whisper caption alignment. NASA observational values unchanged.',creator='plus c / AI-assisted preparation with OpenAI Codex',pageCompression=1)
 doc.build(story,onFirstPage=page_chrome,onLaterPages=page_chrome)
 (OUT/'Mars-Mission-Commander-Project-Description.md').write_text('\n'.join(md),encoding='utf-8')
 disclosure={'project':'Mars Mission Commander','team':'plus c','challenge':'Junior Astronaut Mission Trainer','reviewDate':'2026-11-14','brainstormingBoard':MIRO,'sourceRepository':REPO,'status':'local playable prototype','aiTools':[{'tool':'OpenAI Codex','affectedWork':['design iteration','application code','dialogue and explanations','procedural Blender/Python asset scripts','tests','documentation','demo graphics and music scripts']},{'tool':'ElevenLabs','affectedWork':['demo narration'],'voice':'Dmitry - Energetic and Confident'},{'tool':'OpenAI Whisper','affectedWork':['local demo caption timing']}],'nasaObservationsAIGenerated':False,'gameResourceRules':'fictional teaching rules, not calibrated NASA mission or medical data','evidence':{'localChecks':44,'localCheckResult':'passed','browserStatus':'earlier 14-check run documented; final recovery patch rerun outstanding','learnerImpact':'not yet validated'},'publicLinksPending':['playable game','demo video','NASA Project page'],'noNASAEndorsement':True}
 (OUT/'Mars-Mission-Commander-disclosure.json').write_text(json.dumps(disclosure,indent=2))
 document=fitz.open(file);texts=[]
 for i,page in enumerate(document):
  page.get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(TMP/f'page-{i+1:02}.png');texts.append(page.get_text())
 widths=420;thumbs=[]
 for i in range(len(document)):
  im=Image.open(TMP/f'page-{i+1:02}.png').convert('RGB');im.thumbnail((widths,594));thumbs.append(im.copy())
 sheet=Image.new('RGB',(widths*4,614*((len(thumbs)+3)//4)),'#bfcac4')
 for i,im in enumerate(thumbs):sheet.paste(im,((i%4)*widths,(i//4)*614))
 sheet.save(TMP/'contact.jpg',quality=92)
 (TMP/'extracted.txt').write_text('\n\n'.join(texts),encoding='utf-8')
 links=sum(len(p.get_links()) for p in document)
 print(json.dumps({'pdf':str(file),'pages':len(document),'words':sum(len(x.split()) for x in texts),'links':links,'renderedPages':str(TMP),'pageWordCounts':[len(x.split()) for x in texts]},indent=2))

if __name__=='__main__':create()
