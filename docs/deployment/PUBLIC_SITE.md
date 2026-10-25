# Public LASTLIGHT site

The public release is the real `apps/web` WebGL application. It publishes a verified, previously computed school scenario from the repository fixtures. The displayed school, district and equipment are illustrative geometry. The public build does not claim a live Physics API connection.

## Build

From `apps/web` on `deployment/public-web`:

```powershell
npm ci
$env:LASTLIGHT_BASE_PATH='/lastlight/'
npm run build
npm run lint
```

`apps/web/.env.production` sets `VITE_PUBLIC_OFFLINE_ONLY=true`. This ensures that disconnecting the school grid loads the verified replay whether or not the URL includes `?demo=offline`. The live design-search control is absent while replaying. The backend URL is not set in this build, and the Vite development proxy is not part of the published files.

Publish the contents of `apps/web/dist` at the root of the dedicated `gh-pages` branch, with a `.nojekyll` file. Configure GitHub Pages to serve `gh-pages` from `/`. The public route is `https://pablo228sos.github.io/lastlight/?demo=offline`.

## Boundaries

- The source branch is `deployment/public-web`. It changes only the public build mode, Vite base path and deployment documentation.
- The `gh-pages` branch contains generated static files only.
- No production Python service is connected. Capacity search requires an authenticated, reliable official API deployment and remains unavailable here.
- The site needs WebGL 2 and enough GPU memory. On lower-power devices the application reduces shadows and pixel density; devices without WebGL show its built-in fallback.
- The URL must be tested over HTTPS in a separate Chromium session after each publish. Check the browser console and all network requests for accidental local API calls.
