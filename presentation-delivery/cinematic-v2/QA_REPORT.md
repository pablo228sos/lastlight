# Film verification

## Final media

All three delivered editions pass a complete FFmpeg decode without errors. `verification.json` records their SHA-256 hashes and stream details.

| Edition | Duration | Video | Audio |
| --- | --- | --- | --- |
| Full | 62.000 s | H.264, 1920×1080, 30 fps, 1860 frames, yuv420p, BT.709 | AAC stereo, 48 kHz |
| Speech mix | 62.000 s | Same picture | AAC stereo, 48 kHz, subdued mix |
| Muted | 62.000 s | Same picture | None |

All files use MP4 fast start. The master was rendered at CRF 17 and then converted from full-range 4:2:0 to standard limited-range yuv420p/BT.709 for PowerPoint playback.

The final speech mix was opened in Windows Media Player. Its process remained open after the 62-second window and was closed manually, so an automatic end-of-playback exit was not confirmed there. A separate full run in the local FFplay video player finished and exited normally. These playback checks are separate from the successful frame-by-frame FFmpeg decode of all editions.

## Picture review

The 10-frame `CONTACT_SHEET.png` and `stills/` cover the full film: opening, school, roof detail, blackout, first failure, comparison, capacity search, Frontier, report and ending. The rooftop close-up was recorded by moving the real application's camera. The matched-camera outage is visible; the school retains critical illumination after ordinary district lights switch off. The first failure reads `09:07:12`. The four candidate outcomes and selected `32 kWh` result are large enough to read on a projector. The Frontier crop shows the real cell classifications and preserves the 13-runs/273-cells qualification. The report card displays only fields present in the exported JSON.

FFmpeg's `blackdetect` found one near-black interval, 14.3–14.7 seconds. This is the intentional outage beat. It found no other interval lasting 0.15 seconds or more. The last frames fade cleanly.

## Sound review

The full mix measures about -21.55 LUFS integrated, -3.56 dB true peak. The speech mix measures about -30.43 LUFS, -12.46 dB true peak. Both use original procedural sound from `make_sound.py`; the muted fallback has no audio stream. The brief dip at the outage is intentional.

## Numerical review

`verify_film.py` checked the actual downloaded live report: synthetic school inputs, live local Physics API, 24 kWh first failure at 09:07:12, 24 and 30 kWh failing, 32 and 36 kWh sustaining the 12-hour test, and 32 kWh selected only within the tested set. The 36 kWh result makes no claim beyond the exclusive observation horizon.

## Capture limitation

The film itself is a true 30 fps deliverable. The WebGL source recorder targeted 30 fps at 1920×1080 on NVIDIA hardware, but the number of *unique* source frames varies by shot. The opening and roof-zoom full-browser captures run at 25 fps. The roof detail is shown as a smaller crop within the 1080p composition. The editing intermediates repeat source frames where necessary. No lower-resolution source was presented as native 4K or as 30 unique WebGL frames per second. The geometry remains the approved application scene; this film does not alter the application.
