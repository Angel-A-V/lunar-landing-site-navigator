// "Plan a mission": when are the Sun and Earth up over the year, and when is the best time to land?
// Pure functions: data in, HTML/SVG text out. All the numbers come from Python
// (app/python/analysis/windows.py); nothing is calculated here except where to draw it.
import { formatDuration } from "./format.js";

const W = 720;
const LEFT = 54;
const RIGHT = 12;
const TOP = 24;
const ROW_H = 16;
const GAP = 8;
const PLOT_W = W - LEFT - RIGHT;
const BODIES = [["sun", "Sun"], ["earth", "Earth"], ["both", "Both"]];
const ROWS_BOTTOM = TOP + BODIES.length * ROW_H + (BODIES.length - 1) * GAP;
const H = ROWS_BOTTOM + 34;

const pct = (v) => `${Number(v.toFixed(1))}%`;

// A stretch that touches the edge of the data may really be longer than we can see.
function windowLength(w) {
  const text = formatDuration(w.duration_hours);
  return w.open_start || w.open_end ? `at least ${text}` : text;
}

// The year as three bars: filled where the Sun / Earth / both are above the skyline.
// Numbered boxes mark the best landing windows for the chosen mission length.
function timelineStrip(plan, picks, missionDays) {
  const x = (i) => LEFT + (i / plan.samples) * PLOT_W;
  let out = "";

  for (const m of plan.months) {
    const isYearMark = m.label.startsWith("Jan");
    out += `<line class="tl-month" x1="${x(m.index).toFixed(1)}" x2="${x(m.index).toFixed(1)}" y1="${TOP - 4}" y2="${ROWS_BOTTOM + 4}"/>`;
    out += `<text class="axis-label" x="${(x(m.index) + 2).toFixed(1)}" y="${ROWS_BOTTOM + 16}">${isYearMark ? m.label : m.label.slice(0, 3)}</text>`;
  }

  BODIES.forEach(([key, name], row) => {
    const y = TOP + row * (ROW_H + GAP);
    out += `<text class="tl-name" x="${LEFT - 8}" y="${y + ROW_H - 4}" text-anchor="end">${name}</text>`;
    out += `<rect class="tl-track" x="${LEFT}" y="${y}" width="${PLOT_W}" height="${ROW_H}"/>`;
    for (const w of plan.windows[key]) {
      const x0 = x(w.start_index);
      const width = Math.max(1.5, x(w.end_index + 1) - x0);
      out +=
        `<rect class="tl-win ${key}" x="${x0.toFixed(1)}" y="${y}" width="${width.toFixed(1)}" height="${ROW_H}">` +
        `<title>${name} visible: ${w.start_time_utc} to ${w.end_time_utc} UTC (${windowLength(w)})</title></rect>`;
    }
  });

  const length = (missionDays * 24) / plan.step_hours; // mission length in samples
  for (const p of picks) {
    if (p.both_pct === 0 && p.sun_pct === 0 && p.earth_pct === 0) continue; // nothing worth marking
    const x0 = x(p.start_index);
    const width = Math.max(3, x(p.start_index + length) - x0);
    out +=
      `<g><title>Landing window ${p.rank}: ${p.start_time_utc} to ${p.end_time_utc} UTC. Sun ${pct(p.sun_pct)}, Earth ${pct(p.earth_pct)}, both ${pct(p.both_pct)}</title>` +
      `<rect class="tl-best" x="${x0.toFixed(1)}" y="${TOP - 4}" width="${width.toFixed(1)}" height="${ROWS_BOTTOM - TOP + 8}"/>` +
      `<text class="tl-rank" x="${(x0 + width / 2).toFixed(1)}" y="${TOP - 8}" text-anchor="middle">${p.rank}</text></g>`;
  }

  out += `<text class="axis-title" x="${LEFT + PLOT_W / 2}" y="${H - 2}" text-anchor="middle">${plan.year_start_utc} to ${plan.year_end_utc} UTC</text>`;
  const label = `Timeline of one year. Sun visible in ${plan.windows.sun.length} windows, Earth in ${plan.windows.earth.length}, both in ${plan.windows.both.length}.`;
  return `<svg class="timeline" viewBox="0 0 ${W} ${H}" role="img" aria-label="${label}">${out}</svg>`;
}

function verdict(label, picks, days) {
  if (!picks.length) return `There is less than ${days} days of data, so no ${days}-day landing can be scored.`;
  const best = picks[0];
  if (best.sun_pct === 0 && best.earth_pct === 0) {
    return `No ${days}-day landing at ${label} gets any sunlight or any line to Earth in this year.`;
  }
  return `Best ${days}-day landing at ${label}: <strong>${best.start_time_utc} UTC</strong>. ` +
    `The Sun is visible for ${pct(best.sun_pct)} of the mission and Earth for ${pct(best.earth_pct)}; ` +
    `both together for ${pct(best.both_pct)}.`;
}

// One row per site: its single best landing window for this mission length.
function crossSiteTable(sites, analyses, days) {
  let body = "";
  for (const s of sites) {
    const best = analyses[s.id].plan.best_starts[String(days)][0];
    body += best
      ? `<tr><th scope="row">${s.label}</th><td>${best.start_time_utc}</td><td>${pct(best.sun_pct)}</td>` +
        `<td>${pct(best.earth_pct)}</td><td>${pct(best.both_pct)}</td>` +
        `<td>${formatDuration(best.longest_sun_dark_hours)}</td><td>${formatDuration(best.longest_earth_blocked_hours)}</td></tr>`
      : `<tr><th scope="row">${s.label}</th><td colspan="6">not enough data</td></tr>`;
  }
  return `
    <h3>Best ${days}-day landing at each site</h3>
    <div class="table-wrap plain">
    <table class="stats">
      <thead><tr><th>Site</th><th>Land at (UTC)</th><th>Sun visible</th><th>Earth visible</th><th>Both</th>
      <th>Longest Sun-dark stretch</th><th>Longest Earth-blocked stretch</th></tr></thead>
      <tbody>${body}</tbody>
    </table>
    </div>`;
}

function bestStartsTable(label, picks, days) {
  let body = "";
  for (const p of picks) {
    body += `<tr><th scope="row">${p.rank}</th><td>${p.start_time_utc}</td><td>${p.end_time_utc}</td>` +
      `<td>${pct(p.sun_pct)}</td><td>${pct(p.earth_pct)}</td><td>${pct(p.both_pct)}</td>` +
      `<td>${formatDuration(p.longest_sun_dark_hours)}</td><td>${formatDuration(p.longest_earth_blocked_hours)}</td></tr>`;
  }
  return `
    <h3>Top ${picks.length} landing windows at ${label} for a ${days}-day mission</h3>
    <div class="table-wrap plain">
    <table class="stats">
      <thead><tr><th>Rank</th><th>Land at (UTC)</th><th>Leave at (UTC)</th><th>Sun visible</th><th>Earth visible</th>
      <th>Both</th><th>Longest Sun-dark stretch</th><th>Longest Earth-blocked stretch</th></tr></thead>
      <tbody>${body}</tbody>
    </table>
    </div>`;
}

function windowList(title, windows) {
  if (!windows.length) return `<div><h4>${title}</h4><p>None in this year.</p></div>`;
  let body = "";
  for (const w of windows) {
    body += `<tr><td>${w.start_time_utc}</td><td>${w.end_time_utc}</td><td>${windowLength(w)}</td></tr>`;
  }
  return `
    <div>
      <h4>${title} (${windows.length})</h4>
      <div class="table-wrap">
      <table class="windows">
        <thead><tr><th>From (UTC)</th><th>To (UTC)</th><th>Length</th></tr></thead>
        <tbody>${body}</tbody>
      </table>
      </div>
    </div>`;
}

// sites: the sites index. analyses: {siteId: analysis}. siteId and days: what the two pickers say.
export function planPanel(sites, analyses, siteId, days) {
  const a = analyses[siteId];
  const plan = a.plan;
  const picks = plan.best_starts[String(days)];
  return `
    <p class="verdict">${verdict(a.label, picks, days)}</p>
    ${crossSiteTable(sites, analyses, days)}
    <h3>The year at ${a.label}</h3>
    <p class="hint">A filled bar means above the skyline. Numbered boxes are the best ${days}-day landing windows
    (1 is best). Hover over a bar for its dates.</p>
    ${timelineStrip(plan, picks, days)}
    ${bestStartsTable(a.label, picks, days)}
    <details class="windows-list">
      <summary>Every window in the year at ${a.label}</summary>
      <div class="window-columns">
        ${windowList("Sun visible", plan.windows.sun)}
        ${windowList("Earth visible", plan.windows.earth)}
        ${windowList("Both visible", plan.windows.both)}
      </div>
    </details>`;
}
