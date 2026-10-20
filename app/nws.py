"""
Fetching and reading NWS data for the house (house.json: forecast:).
Only fetches when asked; remembers results for a few minutes.
NWS raw gridpoint data is metric (C, mm, km/h) and comes in time blocks.
"""

import re
import time
from datetime import datetime, timedelta

import httpx

import house

_GRID = house.FORECAST["grid"]
GRID_URL = f"https://api.weather.gov/gridpoints/{_GRID['office']}/{_GRID['x']},{_GRID['y']}"
FORECAST_URL = GRID_URL + "/forecast"

HEADERS = {
    "User-Agent": f"(HomeAssistant weather-brain, {house.FORECAST.get('contact') or ''})",
    "Accept": "application/geo+json",
}
TIMEOUT_SECONDS = float(house.FORECAST.get("timeout_seconds", 5.0))
CACHE_SECONDS = int(house.FORECAST.get("cache_seconds", 600))  # how long answers are remembered

_cache = {}


def _get(url):
    """Fetch a URL from NWS, or reuse a recent answer."""
    now = time.time()
    hit = _cache.get(url)
    if hit and now - hit[0] < CACHE_SECONDS:
        return hit[1]
    response = httpx.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    data = response.json()
    _cache[url] = (now, data)
    return data


def get_grid():
    """Raw gridpoint data: amounts, gusts, hazards and more."""
    return _get(GRID_URL)["properties"]


def get_forecast_periods():
    """Narrative forecast periods ("Tonight", "Friday"...) with written text."""
    return _get(FORECAST_URL)["properties"]["periods"]


# ---- Unit conversions ----

def c_to_f(c):
    return c * 9 / 5 + 32


def mm_to_in(mm):
    return mm / 25.4


def kmh_to_mph(kmh):
    return kmh * 0.621371


# ---- Time blocks ----

_DURATION = re.compile(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?)?")


def parse_valid_time(valid_time):
    """'2026-10-09T00:00:00+00:00/PT6H' -> (start, end) datetimes."""
    start_text, duration_text = valid_time.split("/")
    start = datetime.fromisoformat(start_text)
    match = _DURATION.fullmatch(duration_text)
    days, hours, minutes = (int(x) if x else 0 for x in match.groups())
    return start, start + timedelta(days=days, hours=hours, minutes=minutes)


def series(grid, field):
    """A gridpoint field as a list of (start, end, value)."""
    blocks = []
    for item in grid.get(field, {}).get("values", []):
        start, end = parse_valid_time(item["validTime"])
        blocks.append((start, end, item["value"]))
    return blocks


def total_in_window(grid, field, start, end):
    """
    Add up an amount (like rain) over a stretch of time.
    Blocks that only partly overlap are counted proportionally.
    """
    total = 0.0
    for block_start, block_end, value in series(grid, field):
        if value is None:
            continue
        overlap = (min(block_end, end) - max(block_start, start)).total_seconds()
        if overlap > 0:
            length = (block_end - block_start).total_seconds()
            total += value * overlap / length
    return total


def values_in_window(grid, field, start, end):
    """All values for a field that overlap a stretch of time."""
    return [
        value
        for block_start, block_end, value in series(grid, field)
        if value is not None and block_start < end and block_end > start
    ]
