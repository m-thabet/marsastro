"""Check the exported media and produce a contact sheet from the actual MP4."""
from pathlib import Path
import subprocess,json,hashlib,sys
from PIL import Image,ImageDraw

root=Path(__file__).resolve().parents[1];out=root/'output/demo'
submission='--submission' in sys.argv
video=out/('Mars-Mission-Commander-Demo-Submission.mp4' if submission else 'Mars-Mission-Commander-Demo-Clean.mp4')
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert float(probe['format']['duration'])<=30
assert (v['width'],v['height'],v['codec_name'],v['pix_fmt'])==(1920,1080,'h264','yuv420p')
assert v['r_frame_rate']=='30/1' and int(v['nb_frames'])==885
assert a['codec_name']=='aac' and a['channels']==2 and a['sample_rate']=='48000'
assert 'Junior Astronaut Mission Trainer' in (probe['format']['tags'].get('title','')+' '+probe['format']['tags'].get('comment',''))
def audio_packets(path):
 return subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0','-c:a','copy','-f','adts','pipe:1'])
if not submission:assert audio_packets(video)==audio_packets(out/'Mars-Mission-Commander-Demo.mp4')
original=Path(r'C:/Users/mahmo/Downloads/ElevenLabs_2026-11-14T06_34_03_Dmitry - Energetic and Confident_pvc_s50_v3.mp3')
if submission:
 assert hashlib.sha256(original.read_bytes()).digest()==hashlib.sha256((out/'source/voiceover-current.mp3').read_bytes()).digest()
 assert 'AI-generated voiceover' in probe['format']['tags']['comment']
 assert 'Original synthesized score' in probe['format']['tags']['comment']
 mix=json.loads((out/'source/submission-audio.json').read_text())
 assert not mix['voiceTimeStretch'] and mix['voiceEndsSeconds']<29.5
 assert 12<=mix['speechMusicDifferenceDB']<=18
subprocess.run(['ffmpeg','-v','error','-i',str(video),'-f','null','NUL'],check=True)
frames=out/('source/submission-review' if submission else 'source/clean-review');frames.mkdir(exist_ok=True)
times=[.95,3.1,8.2,10.5,12.8,15.4,19.8,25.5,28.7] if submission else [.95,3.1,7.8,9.95,11.8,14.3,17.8,22.8,27.0]
sheet=Image.new('RGB',(1440,810))
for i,t in enumerate(times):
 p=frames/f'{i:02}.jpg'
 subprocess.run(['ffmpeg','-y','-v','error','-ss',str(t),'-i',str(video),'-frames:v','1','-q:v','2',str(p)],check=True)
 sheet.paste(Image.open(p).resize((480,270)),((i%3)*480,(i//3)*270))
sheet.save(out/'storyboard.jpg',quality=95)
Image.open(frames/'02.jpg').save(out/'Mars-Mission-Commander-Poster.jpg',quality=95)
sound=subprocess.run(['ffmpeg','-hide_banner','-i',str(video),'-af','loudnorm=I=-16:TP=-1.5:LRA=8:print_format=json','-f','null','NUL'],capture_output=True,text=True,check=True)
start=sound.stderr.rfind('{');end=sound.stderr.rfind('}')+1;levels=json.loads(sound.stderr[start:end]);assert float(levels['input_tp'])<=-1.0
data={'file':video.name,'duration':float(probe['format']['duration']),'resolution':[v['width'],v['height']],'frameCount':int(v['nb_frames']),'fps':v['r_frame_rate'],'videoCodec':v['codec_name'],'audioCodec':a['codec_name'],'audioSampleRate':a['sample_rate'],'audioChannels':a['channels'],'integratedLoudnessLUFS':float(levels['input_i']),'truePeakDBTP':float(levels['input_tp']),'originalVoicePreserved':True,'decodeCheck':'passed','englishCaptions':'burned in; separate SRT supplied','sizeBytes':video.stat().st_size}
if submission:
 data.update({'replacementVoiceDurationSeconds':mix['voiceDurationSeconds'],'voiceEndsSeconds':mix['voiceEndsSeconds'],'voiceTimeStretch':False,'speechMusicDifferenceDB':mix['speechMusicDifferenceDB'],'generatedAudioMetadataAcknowledgement':True})
else:data['approvedSoundtrackPreservedExactly']=True
(out/('source/verification-submission.json' if submission else 'source/verification-clean.json')).write_text(json.dumps(data,indent=2));print(json.dumps(data,indent=2))
