"""
The weather brain: interprets the forecast.
Pure logic - no internet, no web server - so it's easy to test.
"""

from datetime import datetime, time, timedelta

import house
import nws  # only for its parsing and unit helpers
import phrases
import suntimes
from normals import compare_to_normal

LOCAL = house.LOCAL

def _clock(name, default):
    """A time of day from house.json's day: section ("17:00"), or the default."""
    hours, minutes = str(house.DAY.get(name) or default).split(":")
    return time(int(hours), int(minutes))


# A day runs midnight to midnight, split once (house.json, day:): "today" is the rest of the day
# until evening_starts; from then on "today" and "tonight" both answer tonight. "tonight" asked at
# any hour is that day's evening. Tonight's low and frost are looked up until night_ends the next
# morning, when the night's coldest hours are.
MORNING_START = _clock("morning_starts", "00:01")
EVENING_START = _clock("evening_starts", "17:00")
NIGHT_END = _clock("night_ends", "07:00")

NIGHT_PERIODS = ("tonight",)
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
DAY_PERIODS = ("today", "tomorrow") + WEEKDAYS

SOAKING_RAIN_IN = 0.4   # this much rain or more is "soaking"
SOME_RAIN_IN = 0.1      # this much or more is worth mentioning
COLD_RAIN_F = 45        # daytime rain at or below this is a "cold rain"
JACKET_F = 55           # at or below this, you want a jacket
LOW_WORTH_SAYING_F = 5  # mention the low if it's this far below the high
DAWN_BEFORE_HOURS = 2   # morning drive: watch from this long before first light until sunrise
DUSK_BEFORE_HOURS = 1   # evening drive: watch from this long before dark...
DUSK_AFTER_HOURS = 3    # ...until this long after dark

# NWS rain intensity words, weakest to strongest.
INTENSITY = {"very_light": 0, "light": 1, "moderate": 2, "heavy": 3}

# Common NWS hazard codes -> spoken names.
HAZARD_NAMES = {
    "FR.Y": "Frost Advisory",
    "FZ.A": "Freeze Watch",
    "FZ.W": "Freeze Warning",
    "WI.Y": "Wind Advisory",
    "HW.A": "High Wind Watch",
    "HW.W": "High Wind Warning",
    "WS.A": "Winter Storm Watch",
    "WS.W": "Winter Storm Warning",
    "WW.Y": "Winter Weather Advisory",
    "IS.W": "Ice Storm Warning",
    "BZ.W": "Blizzard Warning",
    "WC.Y": "Cold Weather Advisory",
    "WC.W": "Extreme Cold Warning",
    "HT.Y": "Heat Advisory",
    "EH.A": "Extreme Heat Watch",
    "EH.W": "Extreme Heat Warning",
    "FG.Y": "Dense Fog Advisory",
    "FA.A": "Flood Watch",
    "FF.A": "Flash Flood Watch",
}


# ---------- When ----------

def _at(day, clock):
    """A specific local date and time."""
    return datetime.combine(day, clock, tzinfo=LOCAL)


def window_for(asked, now=None):
    """
    Decide which hours a question covers.

    asked: "now", "today", "tonight", "tomorrow" or a weekday
    now:   the current local time (can be set for testing)

    Returns the period actually answered plus its start and end.
    """
    now = now or datetime.now(LOCAL)
    today = now.date()

    if asked == "now":
        return {"period": "now", "start": now, "end": now + timedelta(hours=1)}

    if asked in WEEKDAYS:
        # The next time that day comes around (today counts as "today").
        days_ahead = (WEEKDAYS.index(asked) - today.weekday()) % 7
        if days_ahead == 0:
            return window_for("today", now)
        day = today + timedelta(days=days_ahead)
        return {"period": asked, "start": _at(day, MORNING_START), "end": _at(day, EVENING_START)}

    if asked == "tomorrow":
        # A new day starts at midnight: at 2 a.m. Friday, "tomorrow" is Saturday.
        day = today + timedelta(days=1)
        return {"period": "tomorrow", "start": _at(day, MORNING_START), "end": _at(day, EVENING_START)}

    evening = _at(today, EVENING_START)
    if asked == "today" and now < evening:
        return {"period": "today", "start": max(now, _at(today, MORNING_START)), "end": evening}

    # "tonight" (that day's evening, asked at any hour), or "today" from the evening on
    return {"period": "tonight", "start": max(now, evening), "end": _at(today + timedelta(days=1), NIGHT_END)}


# ---------- What (facts) ----------

def gather_facts(grid, window):
    """
    Collect the forecast numbers for one window.
    No opinions here - just what NWS says, in friendly units.
    """
    start, end = window["start"], window["end"]

    def values(field):
        return nws.values_in_window(grid, field, start, end)

    def total(field):
        return nws.total_in_window(grid, field, start, end)

    def to_f(celsius):
        return round(nws.c_to_f(celsius))

    temps = values("temperature")
    feels = values("apparentTemperature")
    precip = values("probabilityOfPrecipitation")
    thunder = values("probabilityOfThunder")
    gusts = values("windGust")
    sky = values("skyCover")

    # Is the coldest part of the window near the start or the end?
    low_when = None
    temp_blocks = [
        (block_start, value)
        for block_start, block_end, value in nws.series(grid, "temperature")
        if value is not None and block_start < end and block_end > start
    ]
    if temp_blocks:
        coldest_start, _ = min(temp_blocks, key=lambda block: block[1])
        low_when = "early" if coldest_start <= start + timedelta(hours=3) else "late"

    # NWS weather codes, e.g. "chance rain showers" (no duplicates).
    weather = []
    for block in values("weather"):
        for item in block or []:
            if item and item.get("weather"):
                words = [item.get("coverage"), item.get("intensity"), item.get("weather")]
                phrase = " ".join(w for w in words if w).replace("_", " ")
                if phrase not in weather:
                    weather.append(phrase)

    # Official hazards, e.g. "FR.Y" = Frost Advisory (no duplicates).
    hazards = []
    for block in values("hazards"):
        for item in block or []:
            code = f"{item.get('phenomenon')}.{item.get('significance')}"
            if code not in hazards:
                hazards.append(code)

    return {
        "high": to_f(max(temps)) if temps else None,
        "low": to_f(min(temps)) if temps else None,
        "low_when": low_when,
        "feels_like_high": to_f(max(feels)) if feels else None,
        "feels_like_low": to_f(min(feels)) if feels else None,
        "precip_chance": round(max(precip)) if precip else 0,
        "thunder_chance": round(max(thunder)) if thunder else 0,
        "rain_in": round(nws.mm_to_in(total("quantitativePrecipitation")), 2),
        "snow_in": round(nws.mm_to_in(total("snowfallAmount")), 1),
        "ice_in": round(nws.mm_to_in(total("iceAccumulation")), 2),
        "max_gust_mph": round(nws.kmh_to_mph(max(gusts))) if gusts else None,
        "sky_cover": round(sum(sky) / len(sky)) if sky else None,
        "weather": weather,
        "hazards": hazards,
    }


def rain_trend(grid, window):
    """
    Read NWS's own story: does the rain build or fade through the window?
    Returns "heavier", "lighter", or None.
    """
    levels = []
    for block_start, block_end, value in nws.series(grid, "weather"):
        if block_start >= window["end"] or block_end <= window["start"]:
            continue
        for item in value or []:
            if (item and item.get("weather") and "rain" in item["weather"]
                    and item.get("intensity") in INTENSITY):
                levels.append(INTENSITY[item["intensity"]])
    if len(levels) < 2:
        return None
    if levels[-1] > levels[0]:
        return "heavier"
    if levels[-1] < levels[0]:
        return "lighter"
    return None


# ---------- Saying amounts and times like a person ----------

def describe_rain(inches):
    if inches < 0.15:
        return "just a little"
    if inches < 0.35:
        return "about a quarter inch"
    if inches < 0.6:
        return "about half an inch"
    if inches < 0.9:
        return "about three quarters of an inch"
    if inches < 1.25:
        return "about an inch"
    return f"about {round(inches * 2) / 2:g} inches"


def describe_snow(inches):
    if inches < 1:
        return "less than an inch"
    whole = round(inches)
    return "about an inch" if whole == 1 else f"about {whole} inches"


def describe_hour(moment):
    hour = moment.hour
    if hour == 0:
        return "midnight"
    if hour == 12:
        return "noon"
    if hour < 12:
        part = "in the morning"
    elif hour < 17:
        part = "in the afternoon"
    elif hour < 21:
        part = "in the evening"
    else:
        part = "at night"
    return f"{hour % 12} {part}"


def driving_risk(grid, facts, start, end):
    """Rain, snow or fog likely between start and end? Returns the kind, or None."""
    for block_start, block_end, value in nws.series(grid, "probabilityOfPrecipitation"):
        if value is not None and value >= 50 and block_start < end and block_end > start:
            return "snow" if facts["snow_in"] >= 0.1 else "rain"
    for block_start, block_end, value in nws.series(grid, "weather"):
        if block_start < end and block_end > start and any(
            item and item.get("weather") == "fog" and item.get("coverage") != "slight_chance"
            for item in value or []
        ):
            return "fog"
    return None


# ---------- Insights (what's worth saying) ----------

def build_insights(grid, window, facts):
    """Turn facts into a list of notable things, most important first."""
    insights = []
    period = window["period"]
    night = period in NIGHT_PERIODS
    month = window["start"].month
    rain_likely = facts["precip_chance"] >= 50
    high, low = facts["high"], facts["low"]

    def add(kind, severity, **values):
        insights.append({
            "type": kind,
            "severity": severity,
            "values": values,
            "advice": phrases.say(kind, **values),
        })

    # Rain amount
    rain = facts["rain_in"]
    if rain >= SOAKING_RAIN_IN:
        add("heavy_rain_night" if night else "soaking_rain", 2, rain=describe_rain(rain))
    elif rain >= SOME_RAIN_IN:
        add("some_rain", 1, rain=describe_rain(rain))

    # Does the rain build or fade? (NWS's own intensity words)
    if rain >= SOME_RAIN_IN:
        trend = rain_trend(grid, window)
        if trend:
            add(f"rain_{trend}", 1)

    # When the rain arrives (only if it's not already starting)
    if period != "now" and rain_likely:
        start, end = window["start"], window["end"]
        for block_start, block_end, value in nws.series(grid, "probabilityOfPrecipitation"):
            if value is not None and value >= 50 and block_start < end and block_end > start:
                arrives = max(block_start, start).astimezone(LOCAL)
                if arrives > start + timedelta(hours=1):
                    add("rain_timing", 1, time=describe_hour(arrives))
                break

    # Jacket: only when the day crosses the jacket line
    if period in DAY_PERIODS and high is not None and low is not None and low <= JACKET_F < high:
        when = "in the morning" if facts["low_when"] == "early" else "by evening"
        add("jacket", 2, when=when)

    # A cold daytime rain
    if not night and rain_likely and low is not None and low <= COLD_RAIN_F:
        add("cold_rain", 1)

    # Frost and freeze (overnight only)
    if night and low is not None:
        if low <= 28:
            add("hard_freeze", 3, low=low)
        elif low <= 32:
            add("freeze", 2, low=low)
        elif low <= 36:
            add("frost", 1, low=low)

    # Snow and ice
    if facts["snow_in"] >= 0.1:
        add("snow", 3 if facts["snow_in"] >= 4 else 2, snow=describe_snow(facts["snow_in"]))
    if facts["ice_in"] > 0:
        add("ice", 3)

    # Wind and storms
    gust = facts["max_gust_mph"]
    if gust is not None and gust >= 35:
        add("windy", 2, gust=gust)
    if facts["thunder_chance"] >= 30:
        add("storms", 2)

    # Feels-like extremes
    feels_low, feels_high = facts["feels_like_low"], facts["feels_like_high"]
    if feels_low is not None and feels_low <= 20 and low is not None and feels_low < low - 3:
        add("feels_cold", 2, feels=feels_low)
    elif feels_high is not None and feels_high >= 95:
        add("feels_hot", 2, feels=feels_high)

    # Unusual for the season (lows at night, highs by day)
    kind = "low" if night else "high"
    temp = facts[kind]
    if temp is not None and period != "now":
        result = compare_to_normal(temp, kind, month)
        if result["direction"]:
            add(f"unusual_{result['direction']}", 1, month=result["month"], diff=result["diff"])

    # Bad weather after dark - hard driving on country roads
    if night:
        dark = suntimes.dark_intervals(window["start"], window["end"])

        def in_dark(block_start, block_end):
            return any(block_start < d_end and block_end > d_start for d_start, d_end in dark)

        risk = None
        for block_start, block_end, value in nws.series(grid, "probabilityOfPrecipitation"):
            if value is not None and value >= 50 and in_dark(block_start, block_end):
                risk = "snow" if facts["snow_in"] >= 0.1 else "rain"
                break
        if risk is None:
            for block_start, block_end, value in nws.series(grid, "weather"):
                if in_dark(block_start, block_end) and any(
                    item and item.get("weather") == "fog" and item.get("coverage") != "slight_chance"
                    for item in value or []
                ):
                    risk = "fog"
                    break
        if risk:
            add(f"dark_{risk}", 2)

    # Daytime answers: bad weather on the dark drives (before sunrise, around dark)
    if period in DAY_PERIODS:
        times = suntimes.sun_times(window["start"].date())
        drives = {
            "morning": (times["first_light"] - timedelta(hours=DAWN_BEFORE_HOURS), times["sunrise"]),
            "evening": (times["dark"] - timedelta(hours=DUSK_BEFORE_HOURS),
                        times["dark"] + timedelta(hours=DUSK_AFTER_HOURS)),
        }
        for drive, (drive_start, drive_end) in drives.items():
            if drive_end <= window["start"]:
                continue  # already passed
            risk = driving_risk(grid, facts, drive_start, drive_end)
            if risk:
                add(f"dark_{drive}_{risk}", 2)

    # Official alerts
    for code in facts["hazards"]:
        add("alert", 3, alert=HAZARD_NAMES.get(code, "weather alert"), code=code)

    insights.sort(key=lambda item: item["severity"], reverse=True)
    return insights


# ---------- The answer ----------

def sky_word(facts, night):
    if facts["snow_in"] >= 0.1:
        return "snowy"
    if facts["precip_chance"] >= 60 and facts["rain_in"] >= SOME_RAIN_IN:
        return "rainy"
    sky = facts["sky_cover"]
    if sky is None:
        return "cloudy"
    if sky < 25:
        return "clear" if night else "sunny"
    if sky < 60:
        return "partly cloudy"
    if sky < 85:
        return "mostly cloudy"
    return "cloudy"


def category(facts):
    """For HA's clips: rain, cloudy or nice."""
    if facts["rain_in"] >= SOME_RAIN_IN or facts["precip_chance"] >= 50:
        return "rain"
    if (facts["sky_cover"] or 0) >= 70:
        return "cloudy"
    return "nice"


def default_speech(window, facts, insights):
    """A plain spoken answer: the basics, then the top insights."""
    period = window["period"]
    sun = suntimes.sun_times(window["start"].date())
    sky = sky_word(facts, period in NIGHT_PERIODS or (period == "now" and not sun["sunrise"] <= window["start"] < sun["sunset"]))
    chance = facts["precip_chance"]
    high, low = facts["high"], facts["low"]

    # Only mention a percentage when rain is uncertain.
    if sky in ("rainy", "snowy") or chance < 20 or chance >= 60:
        chance_part = ""
    else:
        chance_part = f", with a {chance} percent chance of showers"

    # Daytime: mention the low too, and when it happens.
    low_part = ""
    if period in DAY_PERIODS and high is not None and low is not None and high - low >= LOW_WORTH_SAYING_F:
        if facts["low_when"] == "early":
            low_part = f", starting out near {low}"
        else:
            low_part = f", dropping to {low} by evening"

    if period == "now":
        first = f"It's {high} degrees and {sky} right now."
    elif period == "today":
        first = f"Today will be {sky} with a high of {high}{low_part}{chance_part}."
    elif period == "tonight":
        first = f"Tonight will be {sky} with a low of {low}{chance_part}."
    elif period in WEEKDAYS:
        first = f"{period.title()} will be {sky} with a high of {high}{low_part}{chance_part}."
    else:
        first = f"Tomorrow will be {sky} with a high of {high}{low_part}{chance_part}."

    # Sun times: sunrise and dark for daytime answers (only what's still ahead),
    # and sunset and dark for tonight if it isn't dark yet.
    dark_line = ""
    times = suntimes.sun_times(window["start"].date())
    sun_values = {
        "sunrise": suntimes.spoken_time(times["sunrise"]),
        "sunset": suntimes.spoken_time(times["sunset"]),
        "dark": suntimes.spoken_time(times["dark"]),
    }
    rise_ahead = times["sunrise"] > window["start"]
    dark_ahead = times["dark"] > window["start"]
    if period in DAY_PERIODS:
        if rise_ahead and dark_ahead:
            dark_line = phrases.say("sun_both", **sun_values)
        elif dark_ahead:
            dark_line = phrases.say("sun_evening", **sun_values)
    elif period == "tonight" and dark_ahead:
        dark_line = phrases.say("sun_evening", **sun_values)

    extras = [item["advice"] for item in insights[:3] if item["advice"]]
    return " ".join([first] + extras + ([dark_line] if dark_line else []))


def answer(asked, grid, now=None):
    """The full version 1 response."""
    window = window_for(asked, now)
    facts = gather_facts(grid, window)
    insights = build_insights(grid, window, facts)
    return {
        "version": 1,
        "when": asked,
        "period": window["period"],
        "start": window["start"].isoformat(),
        "end": window["end"].isoformat(),
        "speech": default_speech(window, facts, insights),
        "category": category(facts),
        "insights": insights,
        "facts": facts,
    }
