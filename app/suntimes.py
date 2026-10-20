"""
Sun times for the house (house.json: its place), calculated locally (no internet).
"Dark" = end of civil twilight: when you need headlights and house lights.
"""

from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun

import house
import phrases

LOCAL = house.LOCAL
HOME = LocationInfo(house.PLACE["name"], house.PLACE.get("region") or "", house.PLACE["timezone"],
                    house.PLACE["latitude"], house.PLACE["longitude"])

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


def sun_times(day):
    """First light, sunrise, sunset, dark and daylight length for one date."""
    s = sun(HOME.observer, date=day, tzinfo=LOCAL)
    return {
        "first_light": s["dawn"],
        "sunrise": s["sunrise"],
        "sunset": s["sunset"],
        "dark": s["dusk"],
        "daylight_hours": (s["sunset"] - s["sunrise"]).total_seconds() / 3600,
    }


def dark_intervals(start, end):
    """The dark stretches (dark until next first light) that overlap start..end."""
    stretches = []
    day = start.date() - timedelta(days=1)
    while day <= end.date():
        dark = sun_times(day)["dark"]
        first_light = sun_times(day + timedelta(days=1))["first_light"]
        if dark < end and first_light > start:
            stretches.append((max(dark, start), min(first_light, end)))
        day += timedelta(days=1)
    return stretches


def spoken_time(moment):
    """7:01, or 7 o'clock on the hour."""
    hour = moment.hour % 12 or 12
    if moment.minute == 0:
        return f"{hour} o'clock"
    return f"{hour}:{moment.minute:02d}"


def _target_day(when, now):
    """Which date a question means: today, tomorrow, or a named weekday."""
    today = now.date()
    if when == "tomorrow":
        return today + timedelta(days=1)
    if when in WEEKDAYS:
        return today + timedelta(days=(WEEKDAYS.index(when) - today.weekday()) % 7)
    return today  # today, tonight, now


def answer(ask, when, now=None):
    """
    Answer a sun question.
    ask:  "first_light", "sunrise", "sunset", "dark" or "daylight"
    when: "today", "tomorrow", a weekday, etc.
    """
    now = now or datetime.now(LOCAL)
    day = _target_day(when, now)
    times = sun_times(day)
    is_today = day == now.date()

    # How to name the day in speech.
    if is_today:
        day_words = "this morning" if ask in ("sunrise", "first_light") else ("today" if ask == "daylight" else "this evening")
    elif day == now.date() + timedelta(days=1):
        day_words = "tomorrow"
    else:
        day_words = f"on {day.strftime('%A')}"

    if ask == "daylight":
        minutes = round(times["daylight_hours"] * 60)
        hours, mins = divmod(minutes, 60)
        amount = f"{hours} hours" + (f" and {mins} minutes" if mins else "")
        speech = phrases.say("daylight_q", hours=amount, day=day_words)
    else:
        moment = times[ask]
        kind = f"{ask}_q"
        if is_today and moment < now:
            kind += "_past"  # already happened today
        speech = phrases.say(kind, time=spoken_time(moment), day=day_words)

    return {
        "version": 1,
        "ask": ask,
        "when": when,
        "date": day.isoformat(),
        "speech": speech,
        "times": {
            key: value.isoformat() if isinstance(value, datetime) else round(value, 2)
            for key, value in times.items()
        },
    }
