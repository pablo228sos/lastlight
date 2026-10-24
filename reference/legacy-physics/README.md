# Simulation research reference

This directory preserves the earlier single-bus energy balance model and its tests. It is research code, separate from the current browser experience. The visual outage does not call this model.

The model uses 15 or 60 minute steps, synthetic load and daylight inputs, battery charge and discharge limits, efficiency losses, inverter limits and critical load priority. The tests include the 9.12 hour reference case and energy boundary checks. It does not model voltage, transients, equipment degradation or a real utility network.

To run the reference tests from this directory:

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Any future production simulator needs a reviewed input schema, energy balance residuals, provenance and independent validation before its results appear in the app.
