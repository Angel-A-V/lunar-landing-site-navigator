// Small helpers that turn numbers into text for the page. No page or data code in here.

// 168.5177 hours -> "7 d 31 min". null (no event in the data) -> "none".
export function formatDuration(hours) {
  if (hours === null || hours === undefined) return "none";
  const totalMinutes = Math.round(hours * 60); // rounding first avoids showing "60 min"
  const days = Math.floor(totalMinutes / 1440);
  const hrs = Math.floor((totalMinutes % 1440) / 60);
  const mins = totalMinutes % 60;
  const parts = [];
  if (days) parts.push(`${days} d`);
  if (hrs) parts.push(`${hrs} h`);
  if (mins) parts.push(`${mins} min`);
  return parts.length ? parts.join(" ") : "0 min";
}

// 1.7364 -> "+1.74", -1.2189 -> "-1.22". A value that rounds to zero shows no sign.
export function formatSigned(value, digits = 2) {
  const rounded = Number(value.toFixed(digits));
  if (rounded === 0) return (0).toFixed(digits);
  return (rounded > 0 ? "+" : "") + rounded.toFixed(digits);
}

export function yesNo(value) {
  return value ? "Yes" : "No";
}
