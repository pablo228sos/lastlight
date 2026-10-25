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

The deployed application source commit is `e77b57f3a924ecd354ac1712edd57b4a22ffa4fc`; the generated `gh-pages` commit is `c898b5efd8a67b18ac41a5924bc027110d3aa02e`. The publish directory includes `DEPLOYED_SOURCE.txt` with that source reference.

The same source is deployed to the existing `ggg-ffbf/web` Vercel project. Its public URL is `https://web-rosy-iota-krwtmih6ds.vercel.app/?demo=offline`, production deployment `dpl_HSW1N1dFsfbiwekQQejVBRNtvnKX`. Vercel builds from the `apps/web` root directory with Vite and the production offline setting. The project link in `.vercel/` and local environment files stay untracked. To redeploy, link the repository root to project `web` in scope `ggg-ffbf`, then run `vercel deploy --prod --yes --scope ggg-ffbf` from the repository root. Verify the production URL after every deployment.

## Public verification

Run `node scripts/verify-public.mjs` from `apps/web`. It visits GitHub Pages over HTTPS in a fresh Chromium session, checks the WebGL 2 context, walks through the school outage and 36 kWh comparison, reads all 273 Frontier cells, downloads the JSON report, checks a mobile viewport, and fails on console, network, or local-address errors. Screenshots and the report are in `evidence/public-deployment/`. Set `LASTLIGHT_PUBLIC_URL` to the Vercel URL and `LASTLIGHT_PUBLIC_EVIDENCE_DIR=vercel-deployment` to run the same test against Vercel. Both URLs passed locally with no failed network requests or browser console errors. The workflow `.github/workflows/public-deployment-verify.yml` runs both checks on an independent Ubuntu runner.

## Boundaries

- The source branch is `deployment/public-web`. It changes only the public build mode, Vite base path, deployment verification and documentation.
- The `gh-pages` branch contains generated static files only.
- No production Python service is connected. Capacity search requires an authenticated, reliable official API deployment and remains unavailable here.
- The site needs WebGL 2 and enough GPU memory. On lower-power devices the application reduces shadows and pixel density; devices without WebGL show its built-in fallback.
- A 390×844 browser viewport renders the intro and keeps its WebGL 2 context. The complete school walkthrough was verified at 1440×900; mobile interaction and performance on a physical phone remain unverified.
