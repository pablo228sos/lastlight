# Playback and numerical QA

Checked on the local Windows presentation computer on 25 October 2026.

1. The film was captured from Chromium/WebGL at a real 1920×1080 browser viewport, with the live local Physics API running. The new recording is untouched in `LASTLIGHT_SOURCE_WEBGL_1920x1080.webm`.
2. The final MP4 was decoded from start to end: 2700 video frames, 30 fps, exactly 90.000 s, H.264 High profile, yuv420p, 1920×1080, no audio track. The FFmpeg `blackdetect` scan found no black interval of 0.08 s or longer.
3. Representative frames at 0, 24, 38, 54, 67, 81 and 88 seconds were inspected. They show the district, initial outage with critical demand served, first failure, 36 kWh pass, four-capacity search, Frontier and report control in the intended order. Chapter captions stay above the decision UI; the disclosure remains at the bottom margin.
4. Windows Media Player Legacy opened the MP4 and displayed its actual video frames. Its window showed the school, equipment labels and playback of the exported film.
5. The JSON downloaded during the same live run was checked: 24 and 30 kWh fail; 32 and 36 kWh survive the 12-hour window; 32 kWh is the smallest passing capacity in the supplied set. The baseline first failure is 9.12 h = 09:07:12, and the upgraded case has no observed failure in the window.
6. The final MP4 was opened from disk and decoded without the application server or network. The presentation computer should still run one full projector rehearsal before the jury pitch, as projector scaling and PowerPoint configuration depend on that setup.

The scene is synthetic. The numerical results apply only to its stated inputs. The final 30 fps contains temporal resampling of the authentic 25 fps browser recording; the spatial resolution is not enlarged.
