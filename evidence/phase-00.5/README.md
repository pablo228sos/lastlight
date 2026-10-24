# Cinematic rebuild review

The first flat city composition did not meet the visual target. This revision replaces it with a continuous WebGL district built in React Three Fiber. The school, solar panels, inverter, battery cabinet, streets, lamps and surrounding buildings share one 3D world. The camera moves between opening, district, facility and equipment views.

`interaction-demo.webm` is a recording of the running app. The screenshots capture opening, descent, school inspection, synthetic outage and reset at 1440 x 900. The corresponding 1920 x 1080 frames are also included. The three `keyframe-*.png` images are direct WebGL captures without interface layers.

The grid disconnect control changes scene lighting and the visible power path. It is a synthetic visual rehearsal. Battery dispatch and outage survival are not calculated in this release. The interface labels the rehearsal so it cannot be mistaken for an engineering result.

The current world is a stylized model. Its distant skyline and repeated building shapes still need creative review. The school is the only detailed equipment model. Other facility types use simpler geometry. The opening is a high aerial view of this synthetic district, not a geospatial Earth rendering.

The next engineering step is to connect the scene to one validated simulation trace. Until that exists, no displayed outage state should be read as a physical forecast.
