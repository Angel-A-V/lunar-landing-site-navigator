"""Look up named lunar features in NASA Moon Trek and cache them in data/sites_moontrek.json.

Moon Trek's search service returns the official (IAU) feature names with coordinates.
The coordinate is the CENTRE of the named feature (for a crater: the middle of its floor),
not a chosen landing spot.

Run from app/python:  python3 scripts/fetch_trek_sites.py      (needs internet once)
"""
import datetime as dt
import json
import math
import os
import urllib.parse
import urllib.request

API = "https://trek.nasa.gov/moon/TrekServices/ws/index/eq/searchItems"
R_KM = 1737.4

# Named features near the south pole to offer on the website. Add a name and re-run.
FEATURES = ["Shackleton", "de Gerlache", "Haworth", "Nobile", "Mons Mouton", "Malapert", "Cabeus"]

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "data", "sites_moontrek.json")


def slug(name):
    """'Mons Mouton' -> 'mons_mouton' (used in file names)."""
    return "_".join(name.lower().split())


def pole_distance_km(lat_deg):
    """Distance from the south pole on the polar map, in km (same formula the terrain maps use)."""
    return 2 * R_KM * math.tan(math.radians(90.0 + lat_deg) / 2)


def pick_feature(docs, name):
    """Find the named feature called exactly `name` in a Moon Trek reply -> (lat_deg, east_lon_deg).

    Moon Trek gives a box "west,south,east,north" in degrees with longitude from -180 to 180.
    A point feature has a zero-size box; for an area we take the centre.
    """
    for doc in docs:
        if doc.get("itemType") == "nomenclature" and (doc.get("title") or "").lower() == name.lower():
            west, south, east, north = (float(v) for v in doc["bbox"].split(","))
            return (south + north) / 2, ((west + east) / 2) % 360
    raise LookupError(f"Moon Trek has no named feature called {name!r}")


def search_url(name):
    query = {"start": 0, "rows": 25, "key": name, "facetKeys": "itemType", "facetValues": "nomenclature"}
    return API + "?" + urllib.parse.urlencode(query)


def search(name):
    with urllib.request.urlopen(search_url(name), timeout=60) as r:
        return json.load(r)["response"]["docs"]


def main():
    sites = []
    for name in FEATURES:
        lat, lon = pick_feature(search(name), name)
        sites.append({
            "id": slug(name),
            "name": name,
            "lat_deg": round(lat, 6),
            "lon_deg_east": round(lon, 6),
            "pole_distance_km": round(pole_distance_km(lat), 1),
            "query": search_url(name),
        })
        print(f"{name:12s} lat {lat:9.4f}  lon_E {lon:9.4f}  {pole_distance_km(lat):6.1f} km from the pole")
    payload = {
        "source": "NASA Moon Trek search service (IAU nomenclature), https://trek.nasa.gov/moon/",
        "note": "Each coordinate is the centre of the named feature, not a chosen landing spot.",
        "retrieved_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
        "sites": sites,
    }
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
