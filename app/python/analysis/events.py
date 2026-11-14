"""When does the Sun (or Earth) next cross the skyline?

Pure functions, no web or hardware code. Works on the rows that
analysis.visibility.analyse() produces.

Words used here:
  set / rise   the body goes from visible to blocked (set) or blocked to visible (rise)
  margin       body elevation minus skyline. Visible means margin > 0.
"""

_EVENT_NAMES = {
    "sun": ("sunset", "sunrise"),      # (visible -> blocked, blocked -> visible)
    "earth": ("earthset", "earthrise"),
}


def next_event(rows, index, body, step_hours=1.0):
    """Time from row `index` until `body` ("sun" or "earth") next sets or rises.

    Returns a dict:
      state         "visible" or "blocked" at the starting row
      event         "sunset"/"sunrise" (or "earthset"/"earthrise"): what the next change is
      hours         hours until it happens, or None if it does not happen inside the data
      window_hours  how many hours of data lie after the starting row

    The crossing time is a straight-line estimate between the two samples either side of
    the flip, so it is finer than the sample step. Example: margin +1 deg at one sample and
    -1 deg at the next puts the crossing exactly halfway between them.
    """
    if body not in _EVENT_NAMES:
        raise ValueError(f"body must be 'sun' or 'earth', got {body!r}")
    if not 0 <= index < len(rows):
        raise ValueError(f"index {index} is outside 0..{len(rows) - 1}")

    margin_key = f"{body}_margin_deg"
    visible_key = f"{body}_visible"
    set_name, rise_name = _EVENT_NAMES[body]

    start_visible = rows[index][visible_key]
    event = set_name if start_visible else rise_name
    window_hours = (len(rows) - 1 - index) * step_hours

    for j in range(index + 1, len(rows)):
        if rows[j][visible_key] != start_visible:
            before = rows[j - 1][margin_key]   # still on the starting side (or exactly 0)
            after = rows[j][margin_key]        # on the other side
            fraction = before / (before - after)  # 0..1: how far between the two samples
            hours = ((j - 1 - index) + fraction) * step_hours
            return {
                "state": "visible" if start_visible else "blocked",
                "event": event,
                "hours": max(0.0, hours),
                "window_hours": window_hours,
            }

    return {
        "state": "visible" if start_visible else "blocked",
        "event": event,
        "hours": None,
        "window_hours": window_hours,
    }


def annotate_events(rows, step_hours=1.0):
    """Copy of `rows` with the next Sun and Earth event added to every row.

    New keys per body (sun_ or earth_): event (name of the next change), event_hours
    (hours until it, or None if it does not happen inside the data), window_hours
    (hours of data left after this row).
    """
    out = []
    for i, row in enumerate(rows):
        new = dict(row)
        for body in ("sun", "earth"):
            e = next_event(rows, i, body, step_hours)
            new[f"{body}_event"] = e["event"]
            new[f"{body}_event_hours"] = e["hours"]
            new[f"{body}_window_hours"] = e["window_hours"]
        out.append(new)
    return out
