"""The site list shared by the scripts. Standard library only, on purpose.

Two kinds of site:
  1. The MODEL SITE (shackleton_rim): the point the tabletop model is built for. It was found from
     LOLA terrain data and is NOT a named feature or an official landing site.
  2. NAMED FEATURES from NASA Moon Trek (IAU nomenclature), cached in data/sites_moontrek.json by
     fetch_trek_sites.py. Each coordinate is the centre of the feature, not a chosen landing spot.

Coordinates are (latitude_deg, east_longitude_deg), south latitude negative.
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, "data")
R_KM = 1737.4
MODEL_SITE = "shackleton_rim"
BAND_REACH_KM = 50.0   # the cut-down 85S 20 m band covers this far from the pole
SKYLINE_RANGE_KM = 35.0


def _pole_distance_km(lat_deg):
    return 2 * R_KM * math.tan(math.radians(90.0 + lat_deg) / 2)


SITES = {
    # Highest point on the Shackleton crater rim, on the ridge facing the pole.
    MODEL_SITE: (-89.781, 203.743),
}
# Names and one-line descriptions shown on the website.
SITE_INFO = {
    MODEL_SITE: ("Shackleton rim (model site)",
                 "Highest point on the Shackleton crater rim, 6.6 km from the pole. Found from NASA LOLA terrain "
                 "data; the tabletop model shows this site. Not a named feature or an official landing site."),
}
# Where each coordinate came from, shown in the data-sources panel.
SITE_SOURCE = {
    MODEL_SITE: "Found from NASA LOLA terrain data (highest rim point); not a named feature",
}

_trek_path = os.path.join(DATA, "sites_moontrek.json")
if os.path.exists(_trek_path):
    with open(_trek_path) as _f:
        _trek = json.load(_f)
    for _s in _trek["sites"]:
        SITES[_s["id"]] = (_s["lat_deg"], _s["lon_deg_east"])
        SITE_INFO[_s["id"]] = (
            _s["name"],
            f"Centre of the named lunar feature {_s['name']}, {_s['pole_distance_km']:.0f} km from the south pole. "
            "A named place, not a chosen landing spot.",
        )
        SITE_SOURCE[_s["id"]] = f"NASA Moon Trek (IAU nomenclature), retrieved {_trek['retrieved_utc']}"

# Which terrain map each site's skyline is built from: the finest one that covers the site and its
# 35 km look-out distance. The 20 m band only reaches 50 km from the pole; the 40 m map reaches 304 km.
SITE_GRID = {
    site: "85S_20M" if _pole_distance_km(lat) + SKYLINE_RANGE_KM <= BAND_REACH_KM else "80S_40M"
    for site, (lat, _lon) in SITES.items()
}

# The skyline file the WEBSITE uses for each site (near terrain plus far terrain out to 250 km).
# The model site has two files on purpose:
#   skyline_shackleton_rim.csv           the original 35 km skyline; the printed wall is built from it
#   skyline_shackleton_rim_extended.csv  the website's version, which also sees mountains beyond 35 km
SKYLINE_FILE = {site: f"skyline_{site}.csv" for site in SITES}
SKYLINE_FILE[MODEL_SITE] = f"skyline_{MODEL_SITE}_extended.csv"

# Site height above the 1737.4 km reference sphere, in metres, read from the skyline meta file
# (make_skyline.py writes it). Horizons needs a height. A site is missing here until its skyline
# has been built.
SITE_HEIGHT_M = {MODEL_SITE: 1738.0}
for _site in SITES:
    _meta = os.path.join(DATA, SKYLINE_FILE[_site][:-4] + ".meta.json")
    if _site != MODEL_SITE and os.path.exists(_meta):  # the model site keeps the height its cached data used
        with open(_meta) as _f:
            SITE_HEIGHT_M[_site] = round(json.load(_f)["site_height_m_above_1737.4km_sphere"], 1)
