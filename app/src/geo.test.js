// Tests for geo.js. Run from app/:  node --test src/
import { test } from "node:test";
import assert from "node:assert/strict";
import { latLonToXyz, xyzToLatLon, tileGrid, tileUrl } from "./geo.js";

const close = (a, b, eps = 1e-9) => assert.ok(Math.abs(a - b) < eps, `${a} is not close to ${b}`);
const closeXyz = (got, want) => want.forEach((w, i) => close(got[i], w));

test("latLonToXyz: lon 0, lat 0 (centre of the near side) is +x", () => {
  closeXyz(latLonToXyz(0, 0), [1, 0, 0]);
});

test("latLonToXyz: the poles are on the y axis", () => {
  closeXyz(latLonToXyz(90, 0), [0, 1, 0]);
  closeXyz(latLonToXyz(-90, 123), [0, -1, 0]);
});

test("latLonToXyz: 90 degrees east is -z (matches how three.js wraps a map centred on lon 0)", () => {
  closeXyz(latLonToXyz(0, 90), [0, 0, -1]);
  closeXyz(latLonToXyz(0, 270), [0, 0, 1]);
  closeXyz(latLonToXyz(0, -90), [0, 0, 1]);
});

test("latLonToXyz: radius scales the point", () => {
  closeXyz(latLonToXyz(0, 0, 2.5), [2.5, 0, 0]);
  const [x, y, z] = latLonToXyz(-89.781, 203.743, 1.01);
  close(Math.hypot(x, y, z), 1.01);
});

test("xyzToLatLon: undoes latLonToXyz, with longitude given as 0 to 360 east", () => {
  for (const [lat, lon] of [[0, 0], [-84.81, 38.15], [-89.781, 203.743], [45, 359.5], [-30, 180]]) {
    const back = xyzToLatLon(...latLonToXyz(lat, lon, 3));
    close(back.lat, lat, 1e-9);
    close(back.lon, lon, 1e-9);
  }
});

test("xyzToLatLon: a negative longitude comes back as east longitude", () => {
  close(xyzToLatLon(...latLonToXyz(10, -90)).lon, 270);
});

test("tileGrid: Moon Trek's layout doubles each zoom level, two tiles wide at zoom 0", () => {
  assert.deepEqual(tileGrid(0), { cols: 2, rows: 1 });
  assert.deepEqual(tileGrid(3), { cols: 16, rows: 8 });
});

test("tileUrl: zoom / row / column, in that order", () => {
  assert.equal(
    tileUrl(2, 1, 5),
    "https://trek.nasa.gov/tiles/Moon/EQ/LRO_WAC_Mosaic_Global_303ppd_v02/1.0.0/default/default028mm/2/1/5.jpg"
  );
});
