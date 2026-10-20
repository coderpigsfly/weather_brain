import re
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query

import brain
import house
import nws
import phrases
import wepwawet
from normals import compare_to_normal
from version import VERSION

app = FastAPI(title="Weather Brain", version=VERSION)


def _openapi():
    """Its OpenAPI document, with its x-wepwawet section: how it fits the house router."""
    if not app.openapi_schema:
        from fastapi.openapi.utils import get_openapi
        app.openapi_schema = wepwawet.described(get_openapi(title=app.title, version=app.version, routes=app.routes))
    return app.openapi_schema


app.openapi = _openapi

WHEN_PATTERN = "^(now|today|tonight|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)$"
PRETEND_HELP = "e.g. 2026-10-11T08:00 (leave blank for real time)"


def _pretend(pretend_time):
    """Turn an optional pretend time into a local datetime."""
    if not pretend_time:
        return None
    now = datetime.fromisoformat(pretend_time)
    if now.tzinfo is None:
        now = now.replace(tzinfo=brain.LOCAL)
    return now


def _grid():
    """Fetch NWS data, or report a clear error."""
    try:
        return nws.get_grid()
    except Exception as err:
        raise HTTPException(status_code=502, detail=f"NWS fetch failed: {err}")


@app.get("/health")
def health():
    """Simple check that the service is running."""
    return {"status": "ok", "version": 1}


@app.get("/weather")
def weather(
    when: str = Query("today", pattern=WHEN_PATTERN),
    pretend_time: Optional[str] = Query(None, description=PRETEND_HELP),
):
    """The main answer Home Assistant asks for."""
    return brain.answer(when, _grid(), _pretend(pretend_time))


@app.get("/test/normal")
def test_normal(
    temp: float,
    kind: str = Query("low", pattern="^(high|low)$"),
    month: int = Query(10, ge=1, le=12),
):
    """Try the normals check: is this temperature unusual for the month?"""
    return compare_to_normal(temp, kind, month)


@app.get("/test/window")
def test_window(
    asked: str = Query("today", pattern=WHEN_PATTERN),
    pretend_time: Optional[str] = Query(None, description=PRETEND_HELP),
):
    """See which hours a question covers, optionally at a pretend time."""
    window = brain.window_for(asked, _pretend(pretend_time))
    return {
        "asked": asked,
        "period": window["period"],
        "start": window["start"].strftime("%a %b %d, %I:%M %p"),
        "end": window["end"].strftime("%a %b %d, %I:%M %p"),
    }


@app.get("/test/facts")
def test_facts(
    asked: str = Query("today", pattern=WHEN_PATTERN),
    pretend_time: Optional[str] = Query(None, description=PRETEND_HELP),
):
    """The forecast facts for whatever window the question covers."""
    window = brain.window_for(asked, _pretend(pretend_time))
    return {
        "period": window["period"],
        "facts": brain.gather_facts(_grid(), window),
    }


@app.get("/sun")
def sun_answer(
    ask: str = Query("sunset", pattern="^(first_light|sunrise|sunset|dark|daylight)$"),
    when: str = Query("today", pattern=WHEN_PATTERN),
    pretend_time: Optional[str] = Query(None, description=PRETEND_HELP),
):
    """Sunrise, sunset, dark and daylight - calculated locally."""
    import suntimes
    return suntimes.answer(ask, when, _pretend(pretend_time))


# ---------- /ask: the request in the person's own words ----------
# The brain decides what it can answer and always replies with a status:
#   answered     -> speech is the answer
#   out_of_reach -> reason (too_far, span, place) and an honest line to speak
# context: earlier requests in the conversation, newest first. For each piece
# (time, sun or weather, place) the new words win; context only fills gaps.

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
NUMBERS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
           "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
NUM = r"(\d+|" + "|".join(NUMBERS) + r")"
# Sun words, longest first so "first light" wins over "light".
# Plain sun words are always about the sun. Loose words ("dark", "get light",
# "the day") only count when the request is asking when or how long - so
# "what's a dark color" comes back not_mine and goes on to Gemini.
SUN_WORDS = {"first light": "first_light", "break of day": "first_light", "daybreak": "first_light",
             "sunrise": "sunrise", "sun rise": "sunrise", "sunup": "sunrise", "sun up": "sunrise",
             "sun come up": "sunrise", "sun comes up": "sunrise", "sun coming up": "sunrise",
             "sunset": "sunset", "sun set": "sunset", "sundown": "sunset",
             "sun go down": "sunset", "sun goes down": "sunset", "sun going down": "sunset",
             "hours of daylight": "daylight", "how much daylight": "daylight", "daylight": "daylight",
             "how long is the day": "daylight", "length of the day": "daylight",
             "dark": "dark",
             "get light": "sunrise", "gets light": "sunrise", "getting light": "sunrise",
             "light out": "sunrise", "light outside": "sunrise"}
LOOSE_SUN = {"dark", "get light", "gets light", "getting light", "light out", "light outside"}
SUN_QUESTION = re.compile(r"\b(when|what time|how long|how much|how many|(dark|light) yet)\b"
                          r"|\bis it (still )?(dark|light)( out| outside)?$")
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september",
          "october", "november", "december"]
# a date said with its month ("february 10th", "wednesday february 10 2027": what the router asks
# when you name a feast day or a chore instead of a day)
DATE = re.compile(r"\b(" + "|".join(MONTHS) + r") (\d{1,2})(?:st|nd|rd|th)?(?: (\d{4}))?\b")
TOO_FAR = ["next week", "next month", "next year", "ten day", "10 day",
           "two weeks", "2 weeks", "fortnight"]
SPAN = ["this week", "this weekend", "the weekend", "weekend",
        "next few days", "coming days", "few days"]
HOME = house.HOME_WORDS        # house.json: home_words (the town's name, "here", "outside"...)
TIME_AFTER_IN = {"morning", "afternoon", "evening", "night", "a", "an", "few",
                 "minute", "minutes", "hour", "hours", "day", "days", "week", "weeks"}
PLACE_STOP = set(WEEKDAYS) | {"today", "tomorrow", "tonight", "now", "this", "next",
                              "on", "for", "at", "right", "later", "please"}
TIME_WORDS = set(WEEKDAYS) | {"today", "tonight", "tomorrow", "now", "right now", "currently",
                              "at the moment", "this morning", "this afternoon",
                              "this evening", "overnight"}


def _clean(text):
    t = text.lower().replace("\u2019", "'")
    t = re.sub(r"'s\b", "", t)                     # tomorrow's -> tomorrow
    return " ".join(re.sub(r"[^a-z0-9' ]+", " ", t).split())


def _has(text, phrase):
    return re.search(r"\b" + re.escape(phrase) + r"\b", text) is not None


def _number(word):
    return int(word) if word.isdigit() else NUMBERS[word]


def _days_ahead(text):
    """'in 3 days' or '3 days from now' -> 3, else None."""
    m = (re.search(r"\bin " + NUM + r" days?\b", text)
         or re.search(r"\b" + NUM + r" days? from (?:now|today)\b", text))
    return _number(m.group(1)) if m else None


def _place(text):
    """A place after 'in' that isn't home -> its name; home or a time -> None."""
    for m in re.finditer(r"\bin (?:the )?([a-z][a-z'.-]*(?: [a-z][a-z'.-]*){0,2})", text):
        words = []
        for w in m.group(1).split():
            if w in PLACE_STOP:
                break
            words.append(w)
        if not words:
            continue
        first = words[0]
        if first in TIME_AFTER_IN or first in NUMBERS or first.isdigit():
            continue
        name = " ".join(words)
        if name in HOME or first in HOME or ("my " + name) in HOME or ("the " + name) in HOME:
            continue
        return name
    return None


def _time_said(text):
    """Does this text say anything about when?"""
    return (any(_has(text, w) for w in TIME_WORDS | set(TOO_FAR) | set(SPAN))
            or _days_ahead(text) is not None or DATE.search(text) is not None)


def _date_ahead(text, now):
    """A date said with its month -> days from today (negative: gone by), else None. With no year,
    a day already gone this year is next year's."""
    m = DATE.search(text)
    if not m:
        return None
    today = now.date()
    year = int(m.group(3)) if m.group(3) else today.year
    try:
        day = datetime(year, MONTHS.index(m.group(1)) + 1, int(m.group(2))).date()
    except ValueError:
        return None
    if not m.group(3) and day < today:
        day = day.replace(year=today.year + 1)
    return (day - today).days


def _window(text):
    if re.search(r"\b(right now|now|currently|at the moment)\b", text):
        return "now"
    if re.search(r"\b(tonight|this evening|overnight)\b", text):
        return "tonight"
    for day in WEEKDAYS:
        if _has(text, day):
            return day
    if _has(text, "tomorrow"):
        return "tomorrow"
    return "today"


def _sun_word(text):
    """The sun phrase in this text (longest wins), or None."""
    return next((k for k in sorted(SUN_WORDS, key=len, reverse=True) if _has(text, k)), None)


WEATHER_WORDS = {"weather", "forecast", "rain", "raining", "rainy", "snow", "snowing", "ice", "icy",
                 "sleet", "fog", "foggy", "wind", "windy", "storm", "storms", "thunder",
                 "cold", "hot", "warm", "temperature", "freeze", "freezing", "frost",
                 "cloudy", "sunny", "umbrella", "jacket", "coat", "drive", "driving", "roads"}


def _weathery(text):
    return any(_has(text, w) for w in WEATHER_WORDS)


def _sun(text):
    """Which sun answer this text wants. A loose word next to weather words
    ("rain after dark") is a weather question, not a sun one."""
    word = _sun_word(text)
    if not word or (word in LOOSE_SUN and _weathery(text)):
        return None
    return SUN_WORDS[word]


def _out_of_reach(reason, **values):
    return {"status": "out_of_reach", "reason": reason, **values,
            "speech": phrases.say(reason, **values)}


@app.get("/ask")
def ask(
    text: str = Query(..., min_length=1, description="the request, as the person said it"),
    context: List[str] = Query([], description="earlier requests, newest first"),
    pretend_time: Optional[str] = Query(None, description=PRETEND_HELP),
):
    """The router's door: the brain reads the words and decides what it can answer."""
    texts = [_clean(text)] + [_clean(c) for c in context]

    # a loose sun word ("dark", "get light") that isn't asking when -> not ours
    word = _sun_word(texts[0])
    if word in LOOSE_SUN and not _weathery(texts[0]) and not SUN_QUESTION.search(texts[0]):
        return {"status": "not_mine", "reason": "not_a_sun_question"}

    # each piece from the newest text that has it
    place = next((p for p in map(_place, texts) if p), None)
    timed = next((x for x in texts if _time_said(x)), "")
    sun = next((s for s in map(_sun, texts) if s), None)

    if place:
        return _out_of_reach("place", place=place.title())
    if any(_has(timed, p) for p in TOO_FAR):
        return _out_of_reach("too_far")
    if any(_has(timed, p) for p in SPAN):
        return _out_of_reach("span")

    when = _window(timed)
    ahead = _days_ahead(timed)
    if ahead is None:
        ahead = _date_ahead(timed, _pretend(pretend_time) or datetime.now(brain.LOCAL))
        if ahead is not None and ahead < 0:
            return _out_of_reach("past")
    if ahead is not None:
        if ahead >= 7:
            return _out_of_reach("too_far")
        now = _pretend(pretend_time) or datetime.now(brain.LOCAL)
        when = "today" if ahead == 0 else "tomorrow" if ahead == 1 else \
            WEEKDAYS[(now + timedelta(days=ahead)).weekday()]

    if sun:
        import suntimes
        result = suntimes.answer(sun, when, _pretend(pretend_time))
        topic = "sun"
    else:
        result = brain.answer(when, _grid(), _pretend(pretend_time))
        topic = "weather"
    speech = result.get("speech") if isinstance(result, dict) else str(result)
    return {"status": "answered", "topic": topic, "when": when,
            "speech": speech, "detail": result}