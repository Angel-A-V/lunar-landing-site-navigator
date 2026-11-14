// The box next to the globe: what the selected site is, and its headline numbers for the year.
// Pure function: one entry of the sites index in, HTML text out.
import { formatDuration } from "./format.js";

export function siteInfo(site) {
  const y = site.year;
  const height = `${site.site_height_m >= 0 ? "+" : ""}${Math.round(site.site_height_m).toLocaleString("en-US")} m`;
  return `
    <h3>${site.label}</h3>
    <p>${site.description}</p>
    <table class="numbers">
      <tbody>
        <tr><th>Position</th><td>${site.lat_deg.toFixed(3)}°, ${site.lon_deg_east.toFixed(3)}° E</td></tr>
        <tr><th>Distance from the south pole</th><td>${site.pole_distance_km.toFixed(1)} km</td></tr>
        <tr><th>Ground height (above the Moon's mean radius)</th><td>${height}</td></tr>
        <tr><th>Sun visible in the year</th><td>${y.sun_visible_days.toFixed(1)} d (${y.sun_visible_pct.toFixed(1)}%)</td></tr>
        <tr><th>Earth visible in the year</th><td>${y.earth_visible_days.toFixed(1)} d (${y.earth_visible_pct.toFixed(1)}%)</td></tr>
        <tr><th>Longest stretch with both</th><td>${formatDuration(y.longest_both_visible_hours)}</td></tr>
        <tr><th>Longest Sun-dark stretch</th><td>${formatDuration(y.longest_sun_dark_hours)}</td></tr>
      </tbody>
    </table>
    <p class="sub">Coordinate: ${site.coordinate_source}.</p>`;
}
