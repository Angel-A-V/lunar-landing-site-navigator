import "./style.css";
import { loadSites, loadSiteAnalysis } from "./data.js";
import { skyDiagram } from "./skyDiagram.js";
import { numbersPanel } from "./numbersPanel.js";
import { planPanel } from "./planPanel.js";
import { siteInfo } from "./siteInfo.js";
import { statsPanel } from "./statsPanel.js";
import { tableView } from "./tableView.js";

const MISSION_DAYS = [7, 14, 30]; // must match MISSION_DAYS in app/python/scripts/export_site_json.py

// ---------- small HTML builders ----------

function siteOptions(sites, selectedId) {
  return sites
    .map((s) => `<option value="${s.id}"${s.id === selectedId ? " selected" : ""}>${s.label}</option>`)
    .join("");
}

// The planning section: its two pickers are built once; only #plan-holder is redrawn.
function planSection(sites, plan) {
  const lengths = MISSION_DAYS
    .map((d) => `<option value="${d}"${d === plan.days ? " selected" : ""}>${d} days</option>`)
    .join("");
  return `
    <section class="card plan">
      <h2>Plan a mission: when is the best time to land?</h2>
      <div class="plan-controls">
        <label for="plan-site">Site</label>
        <select id="plan-site">${siteOptions(sites, plan.site)}</select>
        <label for="plan-days">Mission length</label> 
        <select id="plan-days">${lengths}</select>
      </div>
      <div id="plan-holder"></div>
    </section>`;
}

// The controls for one card: a site picker and a time slider. Built once, never redrawn,
// so a slider keeps focus while you drag it.
function slotControls(letter, sites, siteId, last, index) {
  const id = letter.toLowerCase();
  return `
    <div class="card-controls">
      <h3>Scenario ${letter}</h3>
      <label for="site-${id}">Site</label>
      <select id="site-${id}">${siteOptions(sites, siteId)}</select>
      <label for="time-${id}">Time <output id="out-${id}"></output></label>
      <input type="range" id="time-${id}" min="0" max="${last}" value="${index}">
      <p class="site-description" id="desc-${id}"></p>
    </div>`;
}

function legend() {
  return `
    <ul class="legend" aria-label="Legend">
      <li><span class="dot sun filled"></span> Sun</li>
      <li><span class="dot earth filled"></span> Earth</li>
      <li><span class="dot ring"></span> Filled dot = above the skyline (visible), hollow dot = blocked</li>
      <li><span class="swatch terrain"></span> Terrain below the skyline</li>
      <li><span class="swatch flat"></span> Flat horizon (0°)</li>
    </ul>`;
}

// The section with the 3D Moon. The globe itself is added by createGlobe() after the page is built.
function globeSection() {
  return `
    <section class="card globe-card">
      <h2>Where are the sites?</h2>
      <div class="globe-layout">
        <div>
          <div id="globe" class="globe-wrap"></div>
          <div class="globe-controls">
            <button type="button" id="view-pole">South pole view</button>
            <button type="button" id="view-moon">Whole Moon</button>
            <span class="sub">Drag to turn, scroll to zoom, click a marker to analyse that site.</span>
          </div>
          <ul class="legend">
            <li><span class="dot named"></span> Named feature (NASA Moon Trek)</li>
            <li><span class="dot model"></span> Model site</li>
            <li><span class="dot picked"></span> Selected</li>
          </ul>
        </div>
        <div id="globe-info" class="globe-info"></div>
      </div>
    </section>`;
}

// One line of the sources panel per site: where its coordinate and its terrain came from.
function siteSourceLine(a) {
  const t = a.terrain;
  const near = t.near_map === "85S_20M" ? "LDEM_85S_20M (20 m per pixel)" : "LDEM_80S_40M (40 m per pixel)";
  const edge = t.far_range_limited_by_map_edge
    ? " This is as far as the terrain map reaches from this site, so even more distant mountains are not counted."
    : "";
  return `<li><strong>${a.label}</strong>: ${a.coordinate_source}. Skyline from ${near} out to ${t.near_range_km} km, then
    LDEM_80S_40M out to ${t.far_range_km.toFixed(0)} km.${edge}
    Files: <code>${a.sources.horizons_30d}</code>, <code>${a.sources.horizons_year}</code>, <code>${a.sources.skyline}</code></li>`;
}

function sourcesPanel(analyses) {
  const files = Object.values(analyses).map(siteSourceLine).join("");
  return `
    <details class="sources" open>
      <summary>Data sources and how this works</summary>
      <ul>
        <li><strong>Sun and Earth directions:</strong> NASA JPL Horizons, asked as an observer standing on the Moon at each site.
        Horizons includes the Moon's wobble (libration).</li>
        <li><strong>Skyline:</strong> built from NASA LRO LOLA terrain heights. For each of 360 compass directions we look
        outward and record the steepest terrain angle. Near terrain (to 35 km) comes from the finest map that covers the
        site; far terrain comes from the 40 m map, out to 250 km or the edge of that map. Distant mountains matter: at
        the model site they raise the skyline by up to about 1.5° in some directions.</li>
        <li><strong>Moon picture:</strong> NASA LRO wide-angle camera global mosaic, loaded live from NASA Moon Trek's
        tile service. The stars behind it are decoration, not a real star map.</li>
        <li><strong>Visible</strong> means the body's angle above a flat horizon is greater than the skyline in its direction.
        <strong>Margin</strong> is that difference.</li>
        <li><strong>Windows</strong> are unbroken stretches of visible samples in the one-year data (6-hour steps), so their
        start, end and length are exact to about 6 hours. A window that touches the start or end of the data is shown as
        "at least" its length.</li>
        <li><strong>Best time to land:</strong> every possible start in the year is scored by the share of the mission with
        both the Sun and Earth visible (power and a direct line to Earth). Ties go to more Sun, then more Earth, then the
        earlier date. Listed windows never overlap each other.</li>
        <li><strong>Next change</strong> (in the scenarios) is found between hourly samples by a straight-line estimate.</li>
        <li><strong>Simplifications:</strong> the Sun is treated as a point (not a disc), and Earth has no safety margin.
        "Visible" is yes or no; it does not yet account for how much power a low Sun gives. All times are UTC.</li>
        <li><strong>Sites:</strong> the named features and their coordinates come from NASA Moon Trek (official IAU names).
        Each coordinate is the centre of the feature (for a crater, the middle of its floor), not a chosen landing spot.
        The model site is a point found from LOLA terrain data. None of these is an official landing site.</li>
        <li><strong>Each site</strong> (coordinate source, terrain maps, and the 30-day, one-year and skyline files):
          <ul>${files}</ul>
        </li>
      </ul>
    </details>`;
}

function tableSection(sites, siteId) {
  return `
    <section class="table-section">
      <label for="table-site">Table view for site</label>
      <select id="table-site">${siteOptions(sites, siteId)}</select>
      <div id="table-holder"></div>
    </section>`;
}

// ---------- the page ----------

function shell(sites, analyses, slots, plan) {
  const last = analyses[sites[0].id].rows.length - 1;
  return `
    <h1>Lunar Landing Site Navigator</h1>
    <p class="intro">Which site, and when? Compare landing sites near the lunar south pole by how long the Sun (power) and
    Earth (direct radio contact) stay above the local skyline, and find the best time to land.</p>
    ${globeSection()}
    ${planSection(sites, plan)}
    ${statsPanel(sites)}
    <section class="moment">
      <h2>Look at one moment: where are the Sun and Earth in the sky?</h2>
      <p>Pick a site and a time in each scenario to compare two sites, or two moments at the same site
      (30 days of hourly data).</p>
      ${legend()}
      <div class="cards">
        <section class="card">
          ${slotControls("A", sites, slots.a.site, last, slots.a.index)}
          <div id="view-a"></div>
        </section>
        <section class="card">
          ${slotControls("B", sites, slots.b.site, last, slots.b.index)}
          <div id="view-b"></div>
        </section>
      </div>
    </section>
    ${tableSection(sites, slots.a.site)}
    ${sourcesPanel(analyses)}`;
}

function drawSlot(id, slot, analyses) {
  const analysis = analyses[slot.site];
  const row = analysis.rows[slot.index];
  document.querySelector(`#out-${id}`).textContent = `${row.time_utc} UTC`;
  document.querySelector(`#desc-${id}`).textContent = analysis.description;
  document.querySelector(`#view-${id}`).innerHTML = skyDiagram(analysis.skyline_deg, row) + numbersPanel(row);
}

async function main() {
  const app = document.querySelector("#app");
  try {
    const sites = await loadSites();
    // A handful of small files: load them all up front so every picker answers instantly.
    // (When there are many sites, load each one when it is first picked instead.)
    const analyses = Object.fromEntries(
      await Promise.all(sites.map(async (s) => [s.id, await loadSiteAnalysis(s.id)]))
    );

    const last = analyses[sites[0].id].rows.length - 1;
    const slots = {
      a: { site: sites[0].id, index: 0 },
      b: { site: (sites[1] || sites[0]).id, index: Math.floor(last / 2) },
    };
    const plan = { site: sites[0].id, days: 14 };
    app.innerHTML = shell(sites, analyses, slots, plan);

    // Planning section
    const planHolder = document.querySelector("#plan-holder");
    const drawPlan = () => (planHolder.innerHTML = planPanel(sites, analyses, plan.site, plan.days));

    // The globe. It is loaded separately and inside try/catch: if 3D graphics (WebGL) are not
    // available, the rest of the page must still work.
    let globe = null;
    try {
      const { createGlobe } = await import("./globe.js");
      globe = createGlobe(document.querySelector("#globe"), sites, (id) => selectSite(id));
      document.querySelector("#view-pole").addEventListener("click", () => globe.setView("pole"));
      document.querySelector("#view-moon").addEventListener("click", () => globe.setView("moon"));
    } catch (error) {
      document.querySelector("#globe").innerHTML =
        `<p class="error">The 3D Moon could not start (${error.message}). Use the site pickers below instead.</p>`;
    }

    // One place that changes the selected site, so the globe, the info box and the plan agree.
    function selectSite(id) {
      plan.site = id;
      document.querySelector("#plan-site").value = id;
      document.querySelector("#globe-info").innerHTML = siteInfo(sites.find((s) => s.id === id));
      if (globe) globe.select(id);
      drawPlan();
    }

    document.querySelector("#plan-site").addEventListener("change", (e) => selectSite(e.target.value));
    document.querySelector("#plan-days").addEventListener("change", (e) => {
      plan.days = Number(e.target.value);
      drawPlan();
    });
    selectSite(plan.site);

    // The two scenarios
    for (const id of ["a", "b"]) {
      document.querySelector(`#site-${id}`).addEventListener("change", (e) => {
        slots[id].site = e.target.value;
        drawSlot(id, slots[id], analyses);
      });
      document.querySelector(`#time-${id}`).addEventListener("input", (e) => {
        slots[id].index = Number(e.target.value);
        drawSlot(id, slots[id], analyses);
      });
      drawSlot(id, slots[id], analyses);
    }

    // Table view
    const holder = document.querySelector("#table-holder");
    const drawTable = (siteId) => (holder.innerHTML = tableView(analyses[siteId].rows));
    document.querySelector("#table-site").addEventListener("change", (e) => drawTable(e.target.value));
    drawTable(slots.a.site);
  } catch (error) {
    app.innerHTML = `<p class="error">Could not load the data: ${error.message}</p>`;
  }
}

main();
