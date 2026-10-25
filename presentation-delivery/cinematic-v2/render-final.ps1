$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$edit = Join-Path $root 'remotion'
$working = Join-Path $root '.working'
New-Item -ItemType Directory -Path $working -Force | Out-Null

Push-Location $edit
try {
    npx remotion render Lastlight62 (Join-Path $working 'remotion-source.mp4') --codec=h264 --crf=17 --x264-preset=slow --pixel-format=yuv420p --audio-codec=aac --audio-bitrate=192k --concurrency=2 --port=3001
    if ($LASTEXITCODE -ne 0) { throw 'Remotion render failed' }
} finally { Pop-Location }

$master = Join-Path $root 'LASTLIGHT_PRODUCT_FILM_62S.mp4'
$speech = Join-Path $root 'LASTLIGHT_PRODUCT_FILM_62S_SPEECH_MIX.mp4'
$muted = Join-Path $root 'LASTLIGHT_PRODUCT_FILM_62S_MUTED.mp4'
$speechAudio = Join-Path $root 'audio/original-speech-safe.wav'

ffmpeg -y -v error -i (Join-Path $working 'remotion-source.mp4') -vf 'scale=in_range=pc:out_range=tv,format=yuv420p' -c:v libx264 -crf 17 -preset slow -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 -af 'atrim=0:62,asetpts=PTS-STARTPTS' -c:a aac -b:a 192k -t 62 -movflags +faststart $master
if ($LASTEXITCODE -ne 0) { throw 'Compatibility master failed' }

ffmpeg -y -v error -i $master -i $speechAudio -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -af 'atrim=0:62,asetpts=PTS-STARTPTS' -t 62 -movflags +faststart $speech
if ($LASTEXITCODE -ne 0) { throw 'Speech mix failed' }

ffmpeg -y -v error -i $master -map 0:v:0 -c:v copy -an -t 62 -movflags +faststart $muted
if ($LASTEXITCODE -ne 0) { throw 'Muted mix failed' }

python (Join-Path $root 'verify_film.py')
if ($LASTEXITCODE -ne 0) { throw 'Film verification failed' }

Write-Output 'LASTLIGHT 62-second film rendered and verified.'
