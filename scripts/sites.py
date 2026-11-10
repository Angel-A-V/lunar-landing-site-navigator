"""Working site list shared by the scripts. No third-party imports on purpose.

Coordinates are (latitude_deg, east_longitude_deg), south latitude negative.
These are working picks, NOT official landing sites. [verify] before the pitch.
"""

SITES = {
    # Highest point on the Shackleton crater rim, on the ridge facing the pole.
    # Found from LOLA terrain data (see scripts/make_skyline.py).
    "shackleton_rim": (-89.781, 203.743),
}

# Site height above the 1737.4 km reference sphere, in metres (from LOLA, see
# data/skyline_<site>.meta.json). Horizons needs a height; 0 would be a little off.
SITE_HEIGHT_M = {
    "shackleton_rim": 1738.0,
}
