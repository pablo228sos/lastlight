# LASTLIGHT film timeline

This is the editable Remotion timeline for the 62-second LASTLIGHT product film. The composition is `Lastlight62` at 1920×1080, 30 fps, 1860 frames.

Run `npm ci` and `npm run dev` to open the preview. Run `npm run lint` before rendering.

To render and verify all three editions from the parent folder:

```powershell
./render-final.ps1
```

`src/Film.tsx` contains the nine timed scenes. `public/film/` contains the genuine LASTLIGHT capture intermediates and the original full soundtrack. The raw browser and WebGL captures are in `../assets/`. The source report and truth boundaries are documented in `../SOURCE_PROVENANCE.md`.

Remotion 4.0.538 is installed with `@remotion/media`. Manrope and IBM Plex Mono are SIL Open Font License 1.1 fonts. The project is private to the team; the [Remotion license](https://raw.githubusercontent.com/remotion-dev/remotion/main/LICENSE.md) applies to anyone rendering or modifying it.
