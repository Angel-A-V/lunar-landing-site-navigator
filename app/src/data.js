// THE DATA LAYER: the only file that fetches anything (architecture rule 1).
// The JSON files are made by app/python/scripts/export_site_json.py. Python does the
// calculation; the page only displays it. Vite serves everything in app/public/ from the root.
const BASE = "/data";

async function getJson(name) {
  const url = `${BASE}/${name}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Could not load ${url} (HTTP ${response.status}). Did you run export_site_json.py?`);
  }
  return await response.json(); // turns the JSON text into a JavaScript object
}

// Short list of every site with its yearly statistics.
export function loadSites() {
  return getJson("sites.json");
}

// One site: 30 days of hourly rows, the skyline, and its yearly statistics.
export function loadSiteAnalysis(id) {
  return getJson(`${id}_analysis.json`);
}
