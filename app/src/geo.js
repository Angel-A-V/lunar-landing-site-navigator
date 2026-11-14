// Geometry helpers for the 3D Moon. Pure functions, no three.js in here, so they can be tested.
//
// Convention (matches how three.js wraps a flat world map, centred on longitude 0, onto a sphere):
//   +y is the north pole, +x is latitude 0 / longitude 0 (the middle of the near side),
//   and longitude increases eastward toward -z.

const RAD = Math.PI / 180;

// Latitude / longitude in degrees -> a point [x, y, z] on a sphere of the given radius.
export function latLonToXyz(latDeg, lonDeg, radius = 1) {
  const lat = latDeg * RAD;
  const lon = lonDeg * RAD;
  return [
    radius * Math.cos(lat) * Math.cos(lon),
    radius * Math.sin(lat),
    -radius * Math.cos(lat) * Math.sin(lon),
  ];
}

// The reverse: a point on (or above) the sphere -> latitude and east longitude (0 to 360) in degrees.
// This is what turns a click on the globe into coordinates.
export function xyzToLatLon(x, y, z) {
  const r = Math.hypot(x, y, z);
  const lon = Math.atan2(-z, x) / RAD;
  return { lat: Math.asin(y / r) / RAD, lon: ((lon % 360) + 360) % 360 };
}

// NASA Moon Trek image tiles (LRO wide-angle camera mosaic). Layout confirmed from the service's
// WMTSCapabilities.xml on 2026-11-14: longitude -180 to 180, top-left corner at (-180, 90),
// 256-pixel tiles, 2 x 1 tiles at zoom 0 and doubling each level.
const TILE_BASE = "https://trek.nasa.gov/tiles/Moon/EQ/LRO_WAC_Mosaic_Global_303ppd_v02/1.0.0/default/default028mm";

export function tileGrid(zoom) {
  return { cols: 2 * 2 ** zoom, rows: 2 ** zoom };
}

export function tileUrl(zoom, row, col) {
  return `${TILE_BASE}/${zoom}/${row}/${col}.jpg`;
}
