// The numbers for one moment in time. Pure function: one analysed row in, HTML text out.
import { formatDuration, formatSigned, yesNo } from "./format.js";

// "Sunset in 3 d 4 h", or "No sunset in the 30 d of data after this time".
function nextChange(row, body) {
  const name = row[`${body}_event`]; // sunset, sunrise, earthset or earthrise
  const hours = row[`${body}_event_hours`];
  if (hours === null) {
    return `No ${name} in the ${formatDuration(row[`${body}_window_hours`])} of data after this time`;
  }
  return `${name[0].toUpperCase()}${name.slice(1)} in ${formatDuration(hours)}`;
}

function visibleCell(visible) {
  // The tick/cross and the word mean it is never color alone.
  return `<td class="${visible ? "yes" : "no"}">${visible ? "✓" : "✗"} ${yesNo(visible)}</td>`;
}

export function numbersPanel(row) {
  return `
    <table class="numbers">
      <thead><tr><th></th><th>Sun</th><th>Earth</th></tr></thead>
      <tbody>
        <tr><th>Direction (azimuth)</th><td>${row.sun_az_deg.toFixed(1)}°</td><td>${row.earth_az_deg.toFixed(1)}°</td></tr>
        <tr><th>Angle above a flat horizon</th><td>${formatSigned(row.sun_el_deg)}°</td><td>${formatSigned(row.earth_el_deg)}°</td></tr>
        <tr><th>Skyline in that direction</th><td>${formatSigned(row.sun_skyline_deg)}°</td><td>${formatSigned(row.earth_skyline_deg)}°</td></tr>
        <tr><th>Margin above the skyline</th><td>${formatSigned(row.sun_margin_deg)}°</td><td>${formatSigned(row.earth_margin_deg)}°</td></tr>
        <tr><th>Visible?</th>${visibleCell(row.sun_visible)}${visibleCell(row.earth_visible)}</tr>
        <tr><th>Next change</th><td>${nextChange(row, "sun")}</td><td>${nextChange(row, "earth")}</td></tr>
      </tbody>
    </table>`;
}
