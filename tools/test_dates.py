#!/usr/bin/env python3
# tools/test_dates.py - a date said with its month (what the router asks for a feast day or a chore):
# within the week it's that day's forecast; past the week, too far; gone by, said so.
# Calls nothing for the answers checked here. Run from the folder:  python3 tools/test_dates.py

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
import server  # noqa: E402

FAILED = []
NOW = "2026-10-19T10:00"     # a Monday


def case(name, got, want):
    if got != want:
        FAILED.append(name)
        print(f"FAIL  {name}\n        got:  {got}\n        want: {want}")
    else:
        print(f"PASS  {name}")


def reason(text):
    r = server.ask(text=text, context=[], pretend_time=NOW)
    return r.get("reason") or r.get("when")


from datetime import datetime  # noqa: E402
now = server._pretend(NOW)
case("A month and day: days ahead; with no year, one gone by is next year's",
     (server._date_ahead(server._clean("Will it rain on October 21st?"), now), server._date_ahead("october 1", now) > 300),
     (2, True))
case("Past the week (the router's feast date, its weekday said too): too far, never this week's Wednesday",
     reason("Will it rain on Wednesday, February 10, 2027?"), "too_far")
case("A date with its year, gone by: said so", reason("Will it rain on October 1, 2026?"), "past")
case("A date and no time word still counts as when", server._time_said(server._clean("rain on november 1")), True)
case("Within the week: that day (the window is the weekday)", server._window("wednesday") and server._date_ahead("october 21", now), 2)

r = server.ask(text="Is it going to rain for the picnic", context=[], pretend_time=NOW)
case("No day, a thing only its name dates: it needs when (the router fills it or asks)", (r["status"], r["need"], r["about"]),
     ("need", "when", "the picnic"))
case("The thing with its day said: answered for that day", reason("Is it going to rain for the picnic on Wednesday"), "wednesday")
case("A plain weather question with no day is today's", reason("Is it going to rain"), "today")
case("At home is never a thing to date", reason("Will it be cold at the house"), "today")
r = server.ask(text="Will it snow on the Feast of Steven when I am at the picnic", context=[], pretend_time=NOW)
case("The thing's name stops at the little words: the feast of steven", (r["status"], r.get("about")), ("need", "the feast of steven"))
case("The day put in by the router: too far", reason("Will it snow on Saturday, December 26 when I am at the picnic"), "too_far")

spec = server.app.openapi()
reply = spec["paths"]["/ask"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
case("Its OpenAPI document says what /ask replies: need names a parameter GET /weather takes",
     ("need" in reply["properties"]["status"]["enum"], reply["properties"]["need"]["enum"],
      "when" in [p["name"] for p in spec["paths"]["/weather"]["get"]["parameters"]]), (True, ["when"], True))
case("Its Wepwawet section adds nothing to the standard for it", "needs" in (spec.get("x-wepwawet") or {}).get("answers", {}), False)

print(f"\n{'all pass' if not FAILED else str(len(FAILED)) + ' fail'}")
sys.exit(1 if FAILED else 0)
