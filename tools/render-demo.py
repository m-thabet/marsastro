"""Render the branded, sub-30-second project demo from local game assets.
Run: python tools/render-demo.py [--preview] [--audio-only]
No external stock visuals or music. Fonts and source credits: output/demo/README.md.
"""
from pathlib import Path
import math, json, subprocess, sys, wave, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/demo'; SRC=OUT/'source'; CAP=OUT/'capture'
W,H,FPS,DURATION=1920,1080,30,29.5
BG='#101a20'; PANEL='#12252b'; WHITE='#edf3ef'; MINT='#8ce0d4'; AMBER='#e5a05c'; MUTED='#a4b9b7'
VOICE=Path(r'C:/Users/mahmo/Downloads/ElevenLabs_2026-11-14T06_34_03_Dmitry - Energetic and Confident_pvc_s50_v3.mp3')
SHIFT=.20
CAPTIONS=[
 (0,1.40,"We're plus C."),
 (1.45,2.60,'Our challenge:'),
 (2.67,4.95,'Junior Astronaut Mission Trainer.'),
 (5.15,7.51,'Space survival is hard to teach.'),
 (7.59,9.50,'Meet Mars Mission Commander.'),
 (9.66,10.90,'Explore Mars.'),
 (10.98,13.65,'Balance oxygen, power, and food.'),
 (13.80,16.60,'See every choice change your mission.'),
 (16.83,20.12,"NASA's MOXIE, radiation data, and plant research"),
 (20.12,22.70,'connect decisions to real science.'),
 (22.82,27.40,'Our playable prototype helps young explorers learn by doing.'),
]
FONT={}
def font(n,bold=False):
 key=(int(n),bold)
 if key not in FONT:FONT[key]=ImageFont.truetype(str(SRC/('Manrope-Bold.ttf' if bold else 'DM-Sans.ttf')),int(n))
 return FONT[key]
def clamp(v,a=0,b=1):return min(b,max(a,v))
def ease(v):return 1-(1-clamp(v))**3
def rgb(h):return tuple(bytes.fromhex(h.lstrip('#')))
def text(im,xy,s,size=30,fill=WHITE,bold=False,anchor=None):
 ImageDraw.Draw(im).text(xy,s,font=font(size,bold),fill=fill,anchor=anchor,stroke_width=0)
def tracking(im,xy,s,size=20,fill=MINT,spacing=4):
 x,y=xy;d=ImageDraw.Draw(im);f=font(size,True)
 for c in s:d.text((x,y),c,font=f,fill=fill);x+=d.textlength(c,font=f)+spacing
def line(im,pts,fill=MINT,width=2):ImageDraw.Draw(im).line(pts,fill=fill,width=width)
def rr(im,box,fill=PANEL,outline=None,r=20,width=1):ImageDraw.Draw(im).rounded_rectangle(box,r,fill,outline,width)
def reveal(im,xy,s,size,t,delay=0,fill=WHITE,bold=True):
 a=ease((t-delay)/.65)
 layer=Image.new('RGBA',(W,H));text(layer,(xy[0],xy[1]+int(38*(1-a))),s,size,fill,bold)
 if a<1:layer.putalpha(layer.getchannel('A').point(lambda v:int(v*a)))
 im.alpha_composite(layer)

yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
glow=np.exp(-((xx-1450)**2/(1100**2)+(yy-300)**2/(780**2)))
base=np.empty((H,W,3),np.uint8)
for c,v in enumerate(rgb(BG)):base[:,:,c]=np.clip(v+glow*[3,12,11][c],0,255)
BASE=Image.fromarray(base).convert('RGBA')
rng=np.random.default_rng(73)
STARS=[(float(x),float(y),float(z)) for x,y,z in zip(rng.uniform(0,W,130),rng.uniform(0,H,130),rng.uniform(.15,1,130))]
IMAGES={}
def asset(p):
 p=str(p)
 if p not in IMAGES:IMAGES[p]=Image.open(ROOT/p).convert('RGBA')
 return IMAGES[p]
def background(t,grid=True):
 im=BASE.copy();layer=Image.new('RGBA',(W,H));d=ImageDraw.Draw(layer)
 if grid:
  for x in range(-50,W+100,120):d.line((x+int(t*5)%120,140,x+int(t*5)%120,H),fill=(140,224,212,8),width=1)
  for y in range(160,H,120):d.line((0,y,W,y),fill=(140,224,212,7),width=1)
 for x,y,z in STARS:
  val=int((.6+.4*math.sin(t*.6+x))*z*95)
  d.ellipse((x,y,x+z*2,y+z*2),fill=(val+35,val+42,val+39,180))
 im.alpha_composite(layer)
 return im
def brand(im,x=76,y=42,scale=1):
 text(im,(x,y-4),'M',50*scale,'#fff5e3',True)
 text(im,(x+40*scale,y-8),'•',50*scale,AMBER,True)
 tracking(im,(x+81*scale,y+1),'MARS',25*scale,WHITE,4*scale)
 tracking(im,(x+81*scale,y+36*scale),'MISSION COMMANDER',9*scale,MUTED,2*scale)
def chrome(im,t,label):
 brand(im)
 tracking(im,(W-76,56),'',15)
 text(im,(1844,52),'plus c  /  '+label,18,MUTED,True,'ra')
 line(im,[(76,122),(1844,122)],'#284044',1)
 text(im,(1844,1018),'AI-GENERATED VISUALS',18,MUTED,False,'ra')
 line(im,[(76,1050),(1844,1050)],'#284044',2)
 line(im,[(76,1050),(76+1768*t/DURATION,1050)],MINT,3)
def subtitle(im,t):
 for start,end,s in CAPTIONS:
  if start+SHIFT<=t<end+SHIFT:
   f=font(30);d=ImageDraw.Draw(im);length=d.textlength(s,font=f)
   box=(W/2-length/2-28,936,W/2+length/2+28,994)
   rr(im,box,(7,17,23,242),'#3b5557',12)
   text(im,(W/2,948),s,30,WHITE,False,'ma')
   break

# A rotating illustrative globe uses the exact credited game texture.
PLANET_SIZE=880
py,px=np.mgrid[-1:1:complex(PLANET_SIZE),-1:1:complex(PLANET_SIZE)].astype(np.float32)
inside=px*px+py*py<=.99
pz=np.sqrt(np.maximum(0,1-px*px-py*py))
lon=np.arctan2(px,pz);lat=np.arcsin(np.clip(-py,-1,1))
lighting=np.clip(-.5*px-.38*py+.8*pz,.025,1)**.7
texture=np.array(asset('public/assets/mars-color.jpg').convert('RGB'))
GLOBE_CACHE={}
def globe(t):
 key=int(t*8)
 if key not in GLOBE_CACHE:
  angle=key*.008+.55
  u=((lon+angle)/(2*math.pi)+.5)%1;v=.5-lat/math.pi
  col=texture[np.clip((v*(texture.shape[0]-1)).astype(int),0,texture.shape[0]-1),(u*(texture.shape[1]-1)).astype(int)].astype(np.float32)
  col*=lighting[:,:,None];col[:,:,0]*=1.05;col[:,:,1]*=.88;col[:,:,2]*=.78
  arr=np.zeros((PLANET_SIZE,PLANET_SIZE,4),np.uint8);arr[:,:,:3]=np.clip(col,0,255);arr[:,:,3]=inside*255
  GLOBE_CACHE[key]=Image.fromarray(arr)
  if len(GLOBE_CACHE)>4:GLOBE_CACHE.pop(next(iter(GLOBE_CACHE)))
 return GLOBE_CACHE[key]
def planet(im,t,x=1000,y=160,size=880):
 d=ImageDraw.Draw(im)
 d.ellipse((x-80,y+size*.24,x+size+80,y+size*.80),outline='#335557',width=2)
 p=globe(t)
 if size!=PLANET_SIZE:p=p.resize((size,size),Image.Resampling.BICUBIC)
 im.alpha_composite(p,(int(x),int(y)))
 # Moving orbit marker and technical coordinates create true motion.
 a=t*.45
 ox=x+size/2+(size/2+80)*math.cos(a);oy=y+size*.52+size*.28*math.sin(a)
 d=ImageDraw.Draw(im);d.ellipse((ox-7,oy-7,ox+7,oy+7),fill=rgb(MINT))
 line(im,[(x+size*.12,y+size*.9),(x+size*.4,y+size*.9)],'#52716b',1)
def image_box(im,source,box,zoom=1,pan=.5,r=20):
 x,y,w,h=map(int,box);src=asset(source)
 iw,ih=src.size;sw,sh=int(w*zoom),int(h*zoom)
 pic=ImageOps.fit(src,(sw,sh),method=Image.Resampling.LANCZOS,centering=(pan,.5))
 pic=pic.crop((int((sw-w)*pan),int((sh-h)/2),int((sw-w)*pan)+w,int((sh-h)/2)+h))
 mask=Image.new('L',(w,h));ImageDraw.Draw(mask).rounded_rectangle((0,0,w-1,h-1),r,fill=255)
 im.paste(pic,(x,y),mask);ImageDraw.Draw(im).rounded_rectangle((x,y,x+w,y+h),r,outline='#4a6664',width=2)
def screenshot(im,name,t,box=(520,196,1324,745),zoom=1.0):
 image_box(im,f'output/demo/capture/{name}.png',box,zoom)
def pill(im,x,y,s,color=MINT):
 f=font(18,True);width=int(ImageDraw.Draw(im).textlength(s,font=f))+34
 rr(im,(x,y,x+width,y+38),PANEL,'#3b6361',19)
 text(im,(x+17,y+7),s,18,color,True)

SCENES=[(0,1.65,'crew'),(1.65,5.25,'challenge'),(5.25,9.80,'project'),(9.80,11.15,'explore'),(11.15,13.95,'balance'),(13.95,16.95,'outcome'),(16.95,22.95,'science'),(22.95,27.80,'benefit'),(27.80,29.50,'end')]

def scene(name,t,start):
 u=t-start;im=background(t)
 if name=='crew':
  planet(im,t,1110,175,780)
  tracking(im,(84,284),'MEET THE TEAM',22,MINT,5)
  reveal(im,(76,331),'plus c',190,u,.05)
  reveal(im,(84,565),'Small crew. Big mission.',42,u,.25,MUTED,False)
  line(im,[(84,682),(84+260*ease(u/.7),682)],AMBER,5)
 elif name=='challenge':
  planet(im,t,1230,300,720)
  tracking(im,(84,248),'THE CHALLENGE',22,MINT,5)
  reveal(im,(76,307),'JUNIOR',110,u)
  reveal(im,(76,424),'ASTRONAUT',110,u,.08)
  reveal(im,(76,541),'MISSION TRAINER',94,u,.16,AMBER)
  reveal(im,(84,712),'Learning to live beyond Earth.',36,u,.25,MUTED,False)
  pill(im,84,803,'CAIRO 2026')
 elif name=='project':
  # Runtime assets are shown here, rather than an unimplemented concept outpost.
  source='overview' if (CAP/'overview.png').exists() else 'power'
  image_box(im,f'output/demo/capture/{source}.png',(770,190,1074,700),1.13+.015*u,.55)
  shade=Image.new('RGBA',(W,H))
  for x in range(690,1260):ImageDraw.Draw(shade).line((x,190,x,890),fill=(*rgb(BG),int(255*(1-(x-690)/570))))
  im.alpha_composite(shade)
  tracking(im,(84,224),'SPACE SURVIVAL IS HARD TO TEACH.',19,MUTED,2)
  text(im,(84,263),'Young explorers need hands-on practice.',25,MUTED)
  reveal(im,(76,316),'MARS',138,u)
  reveal(im,(80,463),'MISSION',91,u,.10)
  reveal(im,(80,566),'COMMANDER',87,u,.20,AMBER)
  reveal(im,(84,740),'A space-science learning game.',32,u,.3,MINT,False)
 elif name in ['explore','balance','outcome']:
  labels={'explore':('01','EXPLORE','Step into','your outpost.'),'balance':('02','BALANCE','Power has','a purpose.'),'outcome':('03','DISCOVER','Every choice','has a result.')}
  n,cap,a,b=labels[name]
  tracking(im,(80,209),n+' / '+cap,21,MINT,4)
  reveal(im,(76,307),a,48,u)
  reveal(im,(76,368),b,48,u,.08,AMBER)
  if name=='explore':
   screenshot(im,'walk',t,zoom=1.02+.025*u)
   pill(im,82,533,'YOUR MARS OUTPOST')
   # The character and camera move in the captured footage when available.
   frame=video_frame('walk',(t-start)*1.3/1.35,1.3)
   if frame is not None:paste_video(im,frame,(520,196,1324,745))
  elif name=='balance':
   screen='allocate' if u<1.1 else 'allocation-stored'
   screenshot(im,screen,t,zoom=1.015+.013*u)
   frame=video_frame('balance',u*2.3/2.8,2.3)
   if frame is not None:paste_video(im,frame,(520,196,1324,745))
   for j,(label,val) in enumerate([('OXYGEN',.72),('POWER',.52),('FOOD',.40)]):
    yy=538+j*87;tracking(im,(83,yy),label,17,MUTED,3)
    rr(im,(84,yy+36,413,yy+44),'#2a4043',r=3)
    v=val+(math.sin(u*2+j)*.09)
    rr(im,(84,yy+36,84+329*v*ease(u/.6),yy+44),MINT if j!=1 else AMBER,r=3)
   # A small cursor ripple highlights the real input region in the game UI.
   d=ImageDraw.Draw(im);cx,cy=1750,565;r=20+int(22*(u%1))
   d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=MINT,width=3)
  else:
   screenshot(im,'result' if (CAP/'result.png').exists() else 'allocation-stored',t,zoom=1.02+.009*u)
   pill(im,82,535,'PLAN / ACT / LEARN')
   text(im,(84,632),'Oxygen. Energy. Food.',24,MUTED)
   text(im,(84,673),'Connected by your decisions.',23,MUTED)
   if u>.26:
    for k,(label,value,color) in enumerate([('ENERGY','12 to 5',AMBER),('WATER','12 to 10',AMBER),('RESEARCH','0 to 1',MINT)]):
     x=1010+k*266;yy=822+int(24*(1-ease((u-.26)/.45)))
     rr(im,(x,yy,x+246,yy+93),'#12252b','#658781',12)
     tracking(im,(x+18,yy+12),label,15,MUTED,1.8)
     text(im,(x+18,yy+37),value,32,color,True)
 elif name=='science':
  tracking(im,(84,189),'REAL SOURCES. PLAYABLE DECISIONS.',21,MINT,4)
  reveal(im,(78,236),'Science behind the mission.',68,u)
  specs=[('01','MOXIE','Oxygen from Mars air','NASA / JPL-Caltech','Life support','life-support-reference-module.png'),('02','RADLAB','Real ISS radiation readings','NASA OSDR / DosTel','Crew protection',None),('03','PLANT RESEARCH','Light affects space seedlings','NASA OSDR · OSD-314','Growing food','greenhouse-reference-module.png')]
  for j,(idx,title,desc,credit,usage,pic) in enumerate(specs):
   a=ease((u-j*.18)/.7);x=84+j*592;y=358+int(40*(1-a))
   rr(im,(x,y,x+568,y+501),PANEL,'#3b5557',22)
   tracking(im,(x+28,y+24),idx+' / '+title,19,MINT,2)
   if pic:
    image_box(im,'Assets/previews/'+pic,(x+22,y+73,524,263),1.04)
    rr(im,(x+36,y+88,x+291,y+120),'#12252b',None,8)
    text(im,(x+49,y+94),'IN-GAME LIFE SUPPORT' if j==0 else 'IN-GAME GREENHOUSE',14,MINT,True)
   else:
    # Plot the game's four archived RadLab values in observation order.
    data=json.loads((ROOT/'src/data/radlab.json').read_text())['data']
    d=ImageDraw.Draw(im)
    text(im,(x+29,y+80),'ISS / DosTel1 / 1 APR 2022',17,MUTED,True)
    for n in [4,6,8,10]:
     yy=y+298-(n-4)*26;line(im,[(x+55,yy),(x+522,yy)],'#29484b',1)
    pts=[(x+64+k*143,y+298-(row[2]-4)*26) for k,row in enumerate(data)]
    progress=clamp((u-.4)/1.5)*3
    visible=[pts[0]]
    for k in range(3):
     q=clamp(progress-k)
     if q>0:visible.append((pts[k][0]+(pts[k+1][0]-pts[k][0])*q,pts[k][1]+(pts[k+1][1]-pts[k][1])*q))
    if len(visible)>1:line(im,visible,MINT,4)
    for k,((xx,yy),row) in enumerate(zip(pts,data)):
     if k<=progress:
      d.ellipse((xx-6,yy-6,xx+6,yy+6),fill=MINT)
      text(im,(xx,yy-38),f'{row[2]:.2f}',22,WHITE,True,'ma')
    text(im,(x+29,y+311),'microgray/hour | observation order',17,MUTED)
   text(im,(x+28,y+354),desc,26,WHITE,True)
   text(im,(x+28,y+397),credit,20,MUTED)
   line(im,[(x+28,y+441),(x+515,y+441)],'#36504f',1)
   text(im,(x+28,y+457),'IN GAME: '+usage.upper(),17,MINT,True)
  text(im,(84,881),'Archived science informs the learning. Resource rates are fictional training rules.',23,MUTED)
 elif name=='benefit':
  source='overview' if (CAP/'overview.png').exists() else 'power'
  image_box(im,f'output/demo/capture/{source}.png',(720,190,1124,702),1.02+.012*u,.52)
  tracking(im,(84,227),'BUILT FOR YOUNG EXPLORERS',19,MINT,2.4)
  reveal(im,(76,315),'LEARN',112,u)
  reveal(im,(76,440),'BY',112,u,.12)
  reveal(im,(76,565),'DOING.',112,u,.24,AMBER)
  pill(im,84,761,'SCIENCE THROUGH PLAY')
  nova=asset('public/assets/nova.png').resize((176,221),Image.Resampling.LANCZOS)
  im.alpha_composite(nova,(1600,672+int(math.sin(t*2)*6)))
 elif name=='end':
  planet(im,t,1240,222,680)
  tracking(im,(84,211),'MARS MISSION COMMANDER  /  TEAM plus c',18,MINT,2)
  reveal(im,(76,274),'YOUR OUTPOST.',91,u)
  reveal(im,(76,387),'YOUR DECISIONS.',91,u,.10,AMBER)
  text(im,(84,537),'Explore Mars. Learn by doing.',32,MUTED)
  line(im,[(84,626),(1090,626)],'#3b5557',2)
  tracking(im,(84,687),'EXPLORE / BALANCE / LEARN',27,MINT,3)
 if name in ['benefit','end']:
  text(im,(84,902),'Globe maps: Solar System Scope / INOVE · CC BY 4.0',20,MUTED)
 chrome(im,t,{'crew':'TEAM INTRODUCTION','challenge':'JUNIOR ASTRONAUT MISSION TRAINER','project':'THE PROJECT','explore':'EXPLORE','balance':'BALANCE','outcome':'SEE THE RESULT','science':'THE SCIENCE','benefit':'THE BENEFIT','end':'CAIRO 2026'}[name])
 subtitle(im,t)
 return im

READERS={}
def video_frame(name,t,duration):
 path=SRC/f'{name}-clip.mp4'
 if not path.exists():return None
 frame_idx=min(int(t*FPS),int(duration*FPS)-1)
 if name not in READERS:
  p=subprocess.Popen(['ffmpeg','-v','quiet','-threads','2','-i',str(path),'-f','rawvideo','-pix_fmt','rgb24','-vf','scale=1324:745','-threads','2','pipe:1'],stdout=subprocess.PIPE)
  READERS[name]={'p':p,'idx':-1,'im':None}
 r=READERS[name]
 while r['idx']<frame_idx:
  data=r['p'].stdout.read(1324*745*3)
  if len(data)!=1324*745*3:break
  r['im']=Image.frombytes('RGB',(1324,745),data).convert('RGBA');r['idx']+=1
 return r['im']
def paste_video(im,frame,box):
 x,y,w,h=box;mask=Image.new('L',(w,h));ImageDraw.Draw(mask).rounded_rectangle((0,0,w-1,h-1),20,fill=255)
 im.paste(frame,(x,y),mask);ImageDraw.Draw(im).rounded_rectangle((x,y,x+w,y+h),20,outline='#4a6664',width=2)

def render(t):
 for i,(a,b,name) in enumerate(SCENES):
  if a<=t<b:
   im=scene(name,t,a)
   # Fast brand-colored diagonal sweep; image remains readable before and after.
   if i>0 and t-a<.23:
    q=(t-a)/.23;center=-400+(W+800)*q
    d=ImageDraw.Draw(im);d.polygon([(center-220,0),(center+60,0),(center-170,H),(center-450,H)],fill=(*rgb(MINT),255))
    d.polygon([(center+65,0),(center+90,0),(center-140,H),(center-165,H)],fill=(*rgb(AMBER),255))
   return im.convert('RGB')
 return scene('end',t,24.5).convert('RGB')

def wav_read(path,rate=48000):
 raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-f','f32le','-ac','2','-ar',str(rate),'pipe:1'])
 return np.frombuffer(raw,dtype=np.float32).reshape(-1,2).copy()
def write_wav(path,a,rate=48000):
 with wave.open(str(path),'wb') as f:f.setparams((2,2,rate,0,'NONE','not compressed'));f.writeframes((np.clip(a,-1,1)*32767).astype('<i2').tobytes())
def audio():
 from demo_score import build_soundtrack
 build_soundtrack(ROOT,OUT,VOICE,SHIFT,DURATION,SCENES)

def subtitles():
 def stamp(t):
  ms=int(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
 (OUT/'Mars-Mission-Commander-Submission.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(a+SHIFT)} --> {stamp(b+SHIFT)}\n{s}' for i,(a,b,s) in enumerate(CAPTIONS))+'\n',encoding='utf-8')

if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True);SRC.mkdir(exist_ok=True);subtitles()
 if '--audio-only' in sys.argv:audio();sys.exit()
 if '--preview' in sys.argv:
  times=[.95,3.1,8.2,10.5,12.8,15.4,19.8,25.5,28.7]
  sheet=Image.new('RGB',(1440,810))
  for i,t in enumerate(times):
   im=render(t);im.save(SRC/f'preview-{i:02}.jpg',quality=91);sheet.paste(im.resize((480,270)),((i%3)*480,(i//3)*270))
  sheet.save(OUT/'storyboard.jpg',quality=94);print('Saved storyboard',flush=True);sys.exit()
 target=SRC/'picture-submission.mp4'
 cmd=['ffmpeg','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-threads','4','-movflags','+faststart',str(target)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 try:
  for i in range(int(DURATION*FPS)):
   p.stdin.write(render(i/FPS).tobytes())
   if i%90==0:print(f'Picture {i}/{int(DURATION*FPS)}',flush=True)
 finally:
  p.stdin.close()
  for r in READERS.values():r['p'].terminate()
 if p.wait():raise RuntimeError('Video encoding failed')
 final=OUT/'Mars-Mission-Commander-Demo-Submission.mp4'
 audio()
 subprocess.run(['ffmpeg','-y','-v','warning','-i',str(target),'-i',str(SRC/'submission-mix.wav'),'-map','0:v','-map','1:a','-map_metadata','-1','-c:v','copy','-af','loudnorm=I=-16:TP=-1.5:LRA=8','-c:a','aac','-ar','48000','-b:a','256k','-metadata','title=Mars Mission Commander | plus c | Junior Astronaut Mission Trainer','-metadata','artist=plus c','-metadata','comment=AI-generated voiceover supplied by user: ElevenLabs / Dmitry - Energetic and Confident. Original synthesized score and sound design created with AI assistance; no third-party music samples. AI-generated motion graphics and illustrative game visuals. Science: NASA/JPL-Caltech, NASA OSDR/DosTel, Villacampa et al. (2021), OSD-314. Globe maps: Solar System Scope / INOVE, CC BY 4.0; adapted with resizing, rotation, lighting and color treatment. Playable educational prototype; fictional training rules; no NASA endorsement.','-t',str(DURATION),'-movflags','+faststart',str(final)],check=True)
 print('Finished',final,flush=True)
