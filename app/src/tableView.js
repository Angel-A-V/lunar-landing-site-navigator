// "Table view": every hourly row as a plain table. Gives the same data as the diagrams in a
// form that can be read, searched and checked line by line.
import { yesNo } from "./format.js";

export function tableView(rows) {
  let body = "";
  for (const r of rows) {
    body += `
        <tr>
          <td>${r.time_utc}</td>
          <td>${r.sun_az_deg.toFixed(2)}</td>
          <td>${r.sun_el_deg.toFixed(2)}</td>
          <td>${r.sun_skyline_deg.toFixed(2)}</td>
          <td>${r.sun_margin_deg.toFixed(2)}</td>
          <td class="${r.sun_visible ? "yes" : "no"}">${yesNo(r.sun_visible)}</td>
          <td>${r.earth_az_deg.toFixed(2)}</td>
          <td>${r.earth_el_deg.toFixed(2)}</td>
          <td>${r.earth_skyline_deg.toFixed(2)}</td>
          <td>${r.earth_margin_deg.toFixed(2)}</td>
          <td class="${r.earth_visible ? "yes" : "no"}">${yesNo(r.earth_visible)}</td>
        </tr>`;
  }
  return `
    <details class="table-view">
      <summary>Table view: every hourly row (${rows.length})</summary>
      <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Time (UTC)</th>
            <th>Sun az</th><th>Sun el</th><th>Sun skyline</th><th>Sun margin</th><th>Sun visible</th>
            <th>Earth az</th><th>Earth el</th><th>Earth skyline</th><th>Earth margin</th><th>Earth visible</th>
          </tr>
        </thead>
        <tbody>${body}
        </tbody>
      </table>
      </div>
    </details>`;
}
