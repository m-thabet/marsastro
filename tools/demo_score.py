"""Original space-adventure score and a speech-first stereo mix; no stock samples."""
from pathlib import Path
import json,math,subprocess,wave,shutil
import numpy as np

def build_soundtrack(root,out,voice,shift,duration,scenes):
 src=out/'source';rate=48000;N=round(duration*rate)
 clock=np.arange(N,dtype=np.float32)/rate
 rng=np.random.default_rng(20261114)
 def read(p):
  raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-f','f32le','-ac','2','-ar',str(rate),'pipe:1'])
  return np.frombuffer(raw,dtype='<f4').reshape(-1,2).copy()
 def save(p,a):
  with wave.open(str(p),'wb') as f:
   f.setparams((2,2,rate,0,'NONE','not compressed'))
   f.writeframes((np.clip(a,-1,1)*32767).astype('<i2').tobytes())
 def add(dest,a,start,gain=1,pan=0):
  j=max(0,round(start*rate));n=min(len(a),N-j)
  if n<=0:return
  if a.ndim==1:a=np.stack([a*math.sqrt((1-pan)/2),a*math.sqrt((1+pan)/2)],axis=1)
  dest[j:j+n]+=a[:n]*gain
 def hz(note):return 440*2**((note-69)/12)
 music=np.zeros((N,2),np.float32);effects=np.zeros_like(music);v=np.zeros_like(music)
 recorded=read(voice);offset=round(shift*rate)
 assert offset+len(recorded)<=N,'Voice would be cut off'
 v[offset:offset+len(recorded)]=recorded
 # D minor / B-flat / F / C, followed by G minor / B-flat / C / D minor.
 # Twelve 4/4 bars at 104 BPM end on a suspended D-minor resolution.
 beat=60/104;bar=beat*4
 chords=[[50,57,62,65,69],[46,53,58,62,65],[48,53,57,60,65],[48,55,60,64,67]]*2
 chords += [[43,50,55,58,62],[46,53,58,62,65],[48,55,60,64,67],[50,57,62,65,69]]
 for i,notes in enumerate(chords):
  start=i*bar;length=min(duration-start,bar+1.0)
  tt=np.arange(round(length*rate),dtype=np.float32)/rate
  env=np.minimum(1,tt/.65)*np.minimum(1,np.maximum(0,length-tt)/.8)
  for k,note in enumerate(notes[1:]):
   freq=hz(note)
   for channel in [0,1]:
    phase=math.tau*freq*(1+(.0007 if channel else -.0007))*tt+k*.63
    tone=np.sin(phase)+.16*np.sin(phase*2)+.06*np.sin(phase*3)
    j=round(start*rate);end=min(N,j+len(tt))
    music[j:end,channel]+=.021*env[:end-j]*tone[:end-j]
  bass_t=np.arange(round(min(bar+.3,duration-start)*rate),dtype=np.float32)/rate
  bass_env=np.minimum(1,bass_t/.035)*np.exp(-bass_t*.75)
  add(music,(np.sin(math.tau*hz(notes[0]-12)*bass_t)+.27*np.sin(math.tau*hz(notes[0])*bass_t))*bass_env,start,.070)
  # Bell/pluck arpeggio with alternating stereo echoes; a clear melody, not a drone.
  pattern=[0,2,1,3,2,1,3,2]
  for step,k in enumerate(pattern):
   at=start+step*beat/2
   note=notes[1:][k]+12
   tt=np.arange(round(.68*rate),dtype=np.float32)/rate
   env=(1-np.exp(-tt*360))*np.exp(-tt*8.2)
   f=hz(note);tone=(np.sin(math.tau*f*tt)+.25*np.sin(math.tau*f*2*tt)+.09*np.sin(math.tau*f*3*tt))*env
   gain=.070 if i>=4 else .050;pan=(-.42 if step%2 else .42)
   add(music,tone,at,gain,pan);add(music,tone,at+beat*.75,gain*.22,-pan)
  # Restrained half-time percussion enters with the gameplay and science.
  if i>=4:
   for step in [0,2]:
    at=start+step*beat;tt=np.arange(round(.24*rate),dtype=np.float32)/rate
    kick=np.sin(math.tau*(48*tt+.9*(1-np.exp(-tt*30))))*np.exp(-tt*22)*np.minimum(1,tt/.003)
    add(music,kick,at,.105)
   for step in [1,3]:
    tt=np.arange(round(.11*rate),dtype=np.float32)/rate
    noise=rng.standard_normal(len(tt)).astype(np.float32)
    noise=noise-np.convolve(noise,np.ones(15,dtype=np.float32)/15,'same')
    shaker=noise*np.exp(-tt*42)*np.minimum(1,tt/.003)
    add(music,shaker,start+step*beat,.013,(-.3 if step==1 else .3))
 # A short final resolution gives the ending a musical finish.
 for note in [50,57,62,65,76]:
  at=12*bar;tt=np.arange(round((duration-at)*rate),dtype=np.float32)/rate
  env=np.minimum(1,tt/.025)*np.exp(-tt*1.1)
  add(music,np.sin(math.tau*hz(note)*tt)*env,at,.034)
 voice_env=np.sqrt(np.convolve(np.mean(v*v,axis=1)[::240],np.ones(32)/32,'same')+1e-8)
 voice_env=np.interp(np.arange(N),np.arange(len(voice_env))*240,voice_env)
 active=voice_env>.025
 duck=1-.4*np.clip(voice_env/.075,0,1)
 music*=duck[:,None]
 # Keep the score audible: active-speech music is 15 dB below the voice in RMS.
 voice_rms=float(np.sqrt(np.mean(v[active]**2)))
 bed_rms=float(np.sqrt(np.mean(music[active]**2)))
 music*=voice_rms*10**(-15/20)/max(bed_rms,1e-8)
 ambient=read(root/'Assets/audio/space-ambience.wav')[:N]
 music+=ambient*.055*duck[:,None]
 fade=np.minimum(1,clock/.55)*np.minimum(1,np.maximum(0,duration-clock)/1.10)
 music*=fade[:,None]
 # Match every sweep to an actual edit, keeping them soft under speech.
 for a,b,name in scenes:
  start=max(0,a-.16);length=.45;tt=np.arange(round(length*rate),dtype=np.float32)/rate
  noise=rng.standard_normal(len(tt)).astype(np.float32)
  noise=np.convolve(noise,np.ones(5,dtype=np.float32)/5,'same');noise-=np.roll(noise,13)
  e=np.sin(np.pi*tt/length)**2;pan=np.linspace(0,1,len(tt))
  sweep=np.stack([noise*e*np.sqrt(1-pan),noise*e*np.sqrt(pan)],axis=1)
  add(effects,sweep,start,.075)
 for at,file,gain in [(9.9,'ui-select',.35),(11.3,'ui-select',.30),(12.6,'ui-confirm',.26),(14.15,'ui-confirm',.3),(17.1,'discovery',.17),(20.2,'radio-message',.10),(23.1,'discovery',.15)]:
  add(effects,read(root/f'Assets/audio/{file}.wav'),at,gain)
 effects*=np.minimum(1,np.maximum(0,duration-clock)/.7)[:,None]
 mixed=v+music+effects
 peak=float(np.max(np.abs(mixed)));gain=min(1,.94/max(peak,1e-8));mixed*=gain
 save(src/'submission-music.wav',music)
 save(src/'submission-effects.wav',effects)
 save(src/'submission-mix.wav',mixed)
 shutil.copy2(voice,src/'voiceover-current.mp3')
 music_rms=float(np.sqrt(np.mean(music[active]**2)))
 difference=float(20*np.log10(voice_rms/max(music_rms,1e-8)))
 metrics={'voiceFile':str(voice),'voiceDurationSeconds':len(recorded)/rate,'voiceOffsetSeconds':shift,'voiceEndsSeconds':shift+len(recorded)/rate,'voiceTimeStretch':False,'score':'Original synthesized space-adventure composition, 104 BPM, D minor','speechMusicDifferenceDB':difference,'mixPeakDBFS':float(20*np.log10(max(np.max(np.abs(mixed)),1e-8))),'commonGain':gain}
 (src/'submission-audio.json').write_text(json.dumps(metrics,indent=2))
 print(json.dumps(metrics,indent=2),flush=True)
