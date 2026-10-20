#!/usr/bin/env python3
# tools/test_windows.py - which hours a question covers, at the times that matter (house.json, day:).
# Calls nothing: no weather fetched. Run from the folder:  python3 tools/test_windows.py

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
import brain  # noqa: E402

FAILED = []
FRI = datetime(2026, 10, 16, tzinfo=brain.LOCAL)          # a Friday
at = lambda h, m=0, day=FRI: day.replace(hour=h, minute=m)   # noqa: E731
EVE, NIGHT_END, MORNING = brain.EVENING_START, brain.NIGHT_END, brain.MORNING_START
evening = at(EVE.hour, EVE.minute)
next_morning = at(NIGHT_END.hour, NIGHT_END.minute, FRI + timedelta(days=1))


def case(name, asked, now, period, start, end):
    w = brain.window_for(asked, now)
    got = (w["period"], w["start"], w["end"])
    if got != (period, start, end):
        FAILED.append(name)
        print(f"FAIL  {name}\n        got:  {got}\n        want: {(period, start, end)}")
    else:
        print(f"PASS  {name}")


case("12:01 AM today: the whole day", "today", at(0, 1), "today", at(0, 1), evening)
case("midnight today: from the morning start", "today", at(0, 0), "today", at(MORNING.hour, MORNING.minute), evening)
case("5:59 AM today: the rest of the day, not the night", "today", at(5, 59), "today", at(5, 59), evening)
case("10 AM today: the rest of the day", "today", at(10), "today", at(10), evening)
case("4:30 PM today: still today", "today", at(16, 30), "today", at(16, 30), evening)
case("5:01 PM today: tonight", "today", at(17, 1), "tonight", at(17, 1), next_morning)
case("11:30 PM today: tonight", "today", at(23, 30), "tonight", at(23, 30), next_morning)
case("12:01 AM tonight: that day's evening", "tonight", at(0, 1), "tonight", evening, next_morning)
case("5:59 AM tonight: that day's evening", "tonight", at(5, 59), "tonight", evening, next_morning)
case("10 AM tonight: this evening", "tonight", at(10), "tonight", evening, next_morning)
case("5:01 PM tonight: from now", "tonight", at(17, 1), "tonight", at(17, 1), next_morning)
sat = FRI + timedelta(days=1)
case("2 AM Friday tomorrow: Saturday", "tomorrow", at(2), "tomorrow", at(MORNING.hour, MORNING.minute, sat),
     at(EVE.hour, EVE.minute, sat))
case("Friday asked on Friday: today", "friday", at(10), "today", at(10), evening)
case("Saturday asked on Friday: Saturday's day", "saturday", at(10), "saturday", at(MORNING.hour, MORNING.minute, sat),
     at(EVE.hour, EVE.minute, sat))

print(f"\n{'all pass' if not FAILED else f'{len(FAILED)} fail'}")
sys.exit(1 if FAILED else 0)
