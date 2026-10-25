"""Render the jury cut from the unedited 1920x1080 Chromium recording."""

from pathlib import Path
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
WORK = ROOT / ".working"
SOURCE = WORK / "native-1080-full.webm"
FINAL = ROOT / "LASTLIGHT_FINAL_DEMO_90S.mp4"

# Each source span is an authentic, continuous section of the single browser run.
# Playback speed is adjusted only to give every jury chapter 15 seconds.
CHAPTERS = [
    (9.000, 27.394, "District to school"),
    (27.394, 39.000, "The blackout"),
    (39.000, 49.000, "First critical failure"),
    (49.000, 63.500, "36 kWh comparison"),
    (63.500, 75.000, "Capacity search"),
    (75.000, 94.000, "Frontier and report"),
]

assert SOURCE.exists(), SOURCE
shutil.copyfile(SOURCE, ROOT / "LASTLIGHT_SOURCE_WEBGL_1920x1080.webm")
shutil.copyfile(ROOT.parent / "evidence/final-demo/after/final-demo-walkthrough.webm", ROOT / "original-final-demo-walkthrough.webm")
shutil.copyfile(WORK / "actual-live-report.json", ROOT / "verified-live-school-report.json")

names = [
    ("01-the-school", "01_THE_SCHOOL.png"),
    ("02-the-blackout", "02_THE_BLACKOUT.png"),
    ("03-first-failure", "03_FIRST_FAILURE.png"),
    ("04-upgrade", "04_36_KWH_TEST.png"),
    ("05-capacity-search", "05_CAPACITY_SEARCH.png"),
    ("06-failure-frontier", "06_FAILURE_FRONTIER.png"),
]
for original, labeled in names:
    shutil.copyfile(WORK / f"{original}.png", ROOT / labeled)
shutil.copyfile(WORK / "07-report-export.png", ROOT / "report-export-evidence.png")

# ASS subtitles are brief editorial labels over the captured app. They make no
# numerical claim beyond what appears in the official live physics UI.
ass = r"""[Script Info]
Title: LASTLIGHT jury demo titles
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Chapter,Segoe UI,40,&H00F3EBDF,&H00F3EBDF,&H000B1316,&H98081216,1,0,0,0,100,100,1,0,3,1,0,8,60,60,76,1
Style: Truth,Segoe UI,18,&H00C7D5D2,&H00C7D5D2,&H00101819,&H8A081216,0,0,0,0,100,100,0,0,3,0,0,2,60,60,17,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:03.50,Chapter,,0,0,0,,THE CITY  /  THE SCHOOL
Dialogue: 0,0:00:20.00,0:00:23.00,Chapter,,0,0,0,,THE BLACKOUT
Dialogue: 0,0:00:24.00,0:00:28.00,Chapter,,0,0,0,,ORDINARY LIGHTS OFF  /  CRITICAL LOAD ON
Dialogue: 0,0:00:36.00,0:00:41.00,Chapter,,0,0,0,,FIRST FAILURE  09:07:12
Dialogue: 0,0:00:54.00,0:00:58.00,Chapter,,0,0,0,,36 kWh  /  12-HOUR TEST PASSED
Dialogue: 0,0:01:05.00,0:01:09.00,Chapter,,0,0,0,,SMALLEST PASSING TESTED CAPACITY  32 kWh
Dialogue: 0,0:01:19.00,0:01:23.00,Chapter,,0,0,0,,273 PHYSICS-VERIFIED FRONTIER CELLS
Dialogue: 0,0:01:26.00,0:01:30.00,Chapter,,0,0,0,,EXPORT ASSUMPTIONS AND RESULTS
Dialogue: 0,0:00:00.00,0:01:30.00,Truth,,0,0,0,,Synthetic school scenario / physics-verified
"""
(ROOT / "titles.ass").write_text(ass, encoding="utf-8")

streams = []
for index, (start, end, _) in enumerate(CHAPTERS):
    factor = 15 / (end - start)
    streams.append(
        f"[0:v]trim=start={start:.3f}:end={end:.3f},"
        f"setpts=(PTS-STARTPTS)*{factor:.9f},fps=30,"
        f"tpad=stop_mode=clone:stop_duration=0.25,trim=end_frame=450,"
        f"setpts=N/(30*TB)[v{index}]"
    )
streams.append("".join(f"[v{i}]" for i in range(6)) + "concat=n=6:v=1:a=0,ass=titles.ass,format=yuv420p[out]")
filter_graph = ";".join(streams)
command = [
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning", "-i", str(SOURCE),
    "-filter_complex", filter_graph, "-map", "[out]", "-an",
    "-c:v", "libx264", "-preset", "medium", "-crf", "19",
    "-profile:v", "high", "-level:v", "4.2", "-pix_fmt", "yuv420p",
    "-r", "30", "-movflags", "+faststart", str(FINAL),
]
subprocess.run(command, cwd=ROOT, check=True)
print(json.dumps({"output": str(FINAL), "chapters": CHAPTERS}, indent=2))
