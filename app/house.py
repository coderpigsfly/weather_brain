"""The weather brain's house: where it is and what's usual there, from house.json (yours, never
released) or, on a new install, house.example.json. Nothing about any one house is in the code."""

import json
import logging
import os
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
log = logging.getLogger("uvicorn.error")


def _load():
    for name in ("house.json", "house.example.json"):
        path = os.path.join(HERE, name)
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            if name != "house.json":
                log.warning("weather brain: no house.json, using %s: copy it to house.json and fill in your place", name)
            return data, name
    raise SystemExit("weather brain: no house.json (copy house.example.json and fill in your place)")


HOUSE, SOURCE = _load()
PLACE = HOUSE["place"]
LOCAL = ZoneInfo(PLACE["timezone"])
HOME_WORDS = {str(w).lower() for w in HOUSE.get("home_words") or []}
FORECAST = HOUSE["forecast"]
DAY = HOUSE.get("day") or {}       # when "today" starts and ends, and how far "tonight" looks
NORMALS = {int(k): v for k, v in HOUSE["normals"]["months"].items()}
UNUSUAL_DEGREES = HOUSE["normals"].get("unusual_degrees", 10)
