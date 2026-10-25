# LASTLIGHT | final product film

The primary film is exactly 62 seconds. Use the speech mix during the live pitch. Keep the full mix for standalone playback and the muted file as a fallback. All three editions are offline H.264 MP4s at 1920×1080 and 30 fps.

## Playback

1. Copy the chosen MP4 to the presentation computer before the event.
2. Open it once in the regular Windows media player and play it from beginning to end.
3. In PowerPoint choose **Insert → Video → This Device**, select `LASTLIGHT_PRODUCT_FILM_62S_SPEECH_MIX.mp4`, then set **Playback → Start: Automatically**.
4. Disable online media dependencies and test the deck locally with the projector or its actual display path.
5. If embedded playback fails, leave PowerPoint and launch the same MP4 directly from File Explorer. The film needs no server or internet.

## Editorial sources

- `remotion/src/Film.tsx` is the editable 62-second timeline and graphics.
- `remotion/public/film/` contains the 30 fps editing media, stills and original full audio.
- `assets/` contains the untouched actual browser/WebGL source recordings, screenshots and JSON report.
- `capture-webgl.mjs`, `capture-intro.mjs` and `capture-detail-full.mjs` reproduce the local capture. They require the app and local Physics API.
- `make_sound.py` generates the original soundtrack.

For audio regeneration and contact-sheet verification, install the small Python dependencies with `python -m pip install -r requirements.txt`.

To preview locally: `cd remotion`, `npm ci`, `npm run dev`. To reproduce all three mastered editions and the verification artifacts, run `powershell -ExecutionPolicy Bypass -File .\render-final.ps1` from this folder. The script renders the Remotion timeline, converts it for regular Windows playback, then runs the full decode and source-data checks. The edited film assets are already included, so this step needs no running application or server.

## Truth boundaries

This is a synthetic school scenario. The 3D geometry is illustrative. Numerical claims come from the official local Physics API; no field telemetry or integrated ML inference is claimed. See `SOURCE_PROVENANCE.md` for the exact source and limits.
