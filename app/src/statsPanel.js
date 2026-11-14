// Yearly comparison of every site. Pure function: the sites index in, HTML text out.
import { formatDuration } from "./format.js";

// "291.2 d (79.7%)"
function daysAndPct(days, percent) {
  return `${days.toFixed(1)} d <span class="sub">(${percent.toFixed(1)}%)</span>`;
}

export function statsPanel(sites) {
  let body = "";
  for (const s of sites) {
    const y = s.year;
    body += `
        <tr>
          <th scope="row">${s.label}<br><span class="sub">${s.lat_deg.toFixed(3)}°, ${s.lon_deg_east.toFixed(3)}° E</span></th>
          <td>${daysAndPct(y.sun_visible_days, y.sun_visible_pct)}<br><span class="sub">in ${y.sun_window_count} windows</span></td>
          <td>${daysAndPct(y.earth_visible_days, y.earth_visible_pct)}<br><span class="sub">in ${y.earth_window_count} windows</span></td>
          <td>${daysAndPct(y.both_visible_days, y.both_visible_pct)}<br><span class="sub">in ${y.both_window_count} windows</span></td>
          <td>${formatDuration(y.longest_both_visible_hours)}</td>
          <td>${formatDuration(y.longest_sun_lit_hours)}</td>
          <td>${formatDuration(y.longest_sun_dark_hours)}</td>
          <td>${formatDuration(y.longest_earth_blocked_hours)}</td>
        </tr>`;
  }
  const days = Math.round(sites[0].year.span_days);
  return `
    <section class="card year">
      <h2>How good is each site over a full year?</h2>
      <p>${days} days of data in 6-hour steps, so every length here is exact to about 6 hours. "Longest stretch with
      both" is the longest a mission could run with solar power and a direct line to Earth the whole time. A site with a
      long Sun-dark stretch has to survive it on stored power.</p>
      <div class="table-wrap plain">
      <table class="stats">
        <thead>
          <tr>
            <th>Site</th>
            <th>Sun visible</th>
            <th>Earth visible</th>
            <th>Both visible</th>
            <th>Longest stretch with both</th>
            <th>Longest sunlit stretch</th>
            <th>Longest Sun-dark stretch</th>
            <th>Longest Earth-blocked stretch</th>
          </tr>
        </thead>
        <tbody>${body}
        </tbody>
      </table>
      </div>
    </section>`;
}
