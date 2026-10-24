# LASTLIGHT

An interactive energy resilience digital twin by CURSED, Kyrgyzstan.

The current prototype is a cinematic 3D night district. Visitors can fly into the city, select a school, inspect its visible energy equipment, disconnect the grid in a synthetic rehearsal and reset the scene. The engineering simulation is not connected yet.

## Run locally

Requires Node.js 20.19 or newer.

```sh
cd apps/web
npm ci
npm run dev
```

Open the address printed by Vite. From the repository root, run `npm run build`, `npm run lint` and `npm run test:smoke` to check the app. The browser tests require Chrome.

## Product boundary

LASTLIGHT is built to test backup energy decisions for facilities such as schools and clinics. The district and facilities in this prototype are synthetic. No utility network is controlled, no meter is connected, and no outage survival figure is presented as a measured result.

See [product scope](docs/PRODUCT.md), [engineering plan](docs/ENGINEERING.md) and the [visual review with browser footage](evidence/phase-00.5/README.md).
