"""Inspect the delivered film, extract final frames and build a contact sheet."""
from __future__ import annotations
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
STILLS = ROOT / 'stills'
STILLS.mkdir(exist_ok=True)
NAMES = [
    'LASTLIGHT_PRODUCT_FILM_62S.mp4',
    'LASTLIGHT_PRODUCT_FILM_62S_SPEECH_MIX.mp4',
    'LASTLIGHT_PRODUCT_FILM_62S_MUTED.mp4',
]
FRAMES = [(2,'HOOK'),(6,'SCHOOL'),(8.8,'ROOF DETAIL'),(16,'BLACKOUT'),(28,'FIRST FAILURE'),(35,'COMPARISON'),(45,'32 kWh'),(52,'FRONTIER'),(57,'REPORT'),(60.8,'LASTLIGHT')]

def run(*args:str)->str:
    result=subprocess.run(args,capture_output=True,text=True,check=True)
    return result.stdout

def probe(path:Path)->dict:
    return json.loads(run('ffprobe','-v','error','-show_entries','format=duration,size,bit_rate','-show_entries','stream=index,codec_type,codec_name,width,height,pix_fmt,avg_frame_rate,duration,nb_frames,sample_rate,channels','-of','json',str(path)))

def sha(path:Path)->str:
    digest=hashlib.sha256()
    with path.open('rb') as file:
        while block:=file.read(1024*1024):digest.update(block)
    return digest.hexdigest()

report=json.loads((ROOT/'assets/actual-live-report.json').read_text(encoding='utf-8'))
search=report['design_search']
assert report['physics_source']=='Live local Physics API'
assert report['site']['input_category']=='synthetic'
assert search['selected_capacity_kwh']==32 and search['physics_verified'] is True
assert [(int(x['capacity_kwh']),bool(x['survived_target'])) for x in search['candidates']]==[(24,False),(30,False),(32,True),(36,True)]
assert search['candidates'][0]['first_critical_failure_hours']==9.12
assert search['candidates'][0]['first_critical_failure_utc'].endswith('09:07:12Z')

results={}
for name in NAMES:
    path=ROOT/name
    info=probe(path)
    video=next(s for s in info['streams'] if s['codec_type']=='video')
    audio=[s for s in info['streams'] if s['codec_type']=='audio']
    assert video['codec_name']=='h264' and video['width']==1920 and video['height']==1080
    assert video['avg_frame_rate']=='30/1' and video['nb_frames']=='1860'
    assert abs(float(video['duration'])-62)<.001
    assert abs(float(info['format']['duration'])-62)<.001
    assert video['pix_fmt']=='yuv420p'
    assert (len(audio)==0)==('MUTED' in name)
    if audio:assert audio[0]['codec_name']=='aac'
    subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','null','NUL'],check=True)
    results[name]={'container_duration_seconds':float(info['format']['duration']),'video_duration_seconds':float(video['duration']),'video_frames':int(video['nb_frames']),'resolution':'1920x1080','frame_rate':'30/1','video_codec':'h264','pixel_format':video['pix_fmt'],'audio_codec':audio[0]['codec_name'] if audio else None,'bytes':path.stat().st_size,'sha256':sha(path),'full_decode':'passed'}

fontpath=Path('C:/Windows/Fonts/consola.ttf')
font=ImageFont.truetype(str(fontpath),25) if fontpath.exists() else ImageFont.load_default()
contact=Image.new('RGB',(1920,532),(5,18,23))
draw=ImageDraw.Draw(contact)
for index,(second,label) in enumerate(FRAMES):
    path=STILLS/f'{index+1:02d}_{label.lower().replace(" ","_")}.png'
    subprocess.run(['ffmpeg','-y','-v','error','-ss',str(second),'-i',str(ROOT/NAMES[0]),'-frames:v','1',str(path)],check=True)
    with Image.open(path) as frame:
        thumb=frame.convert('RGB').resize((384,216),Image.Resampling.LANCZOS)
    x=(index%5)*384;y=(index//5)*266
    contact.paste(thumb,(x,y))
    draw.text((x+13,y+226),f'{second:04.1f}s  {label}',font=font,fill=(231,228,215))
contact.save(ROOT/'CONTACT_SHEET.png',optimize=True)

evidence={'source_commit':'24b43f99a4c4d561a9ec32ea14170c9e6c27ff69','physics_model_version':report['model_version'],'school_input_category':report['site']['input_category'],'capacity_outcomes':[(x['capacity_kwh'],x['survived_target']) for x in search['candidates']],'first_failure_24_kwh':'09:07:12','smallest_passing_tested_capacity_kwh':32,'frontier_cells':273,'frontier_physical_runs':13,'files':results}
(ROOT/'verification.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
print(json.dumps(evidence,indent=2))
