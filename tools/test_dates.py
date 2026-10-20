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

print(f"\n{'all pass' if not FAILED else str(len(FAILED)) + ' fail'}")
sys.exit(1 if FAILED else 0)
