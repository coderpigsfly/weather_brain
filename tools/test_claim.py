#!/usr/bin/env python3
# tools/test_claim.py - /ask?claim=true: not_mine unless the words are about the weather or the sun.
# Calls nothing: only requests the brain turns away before any weather is fetched, and the word check.
# Run from the folder:  python3 tools/test_claim.py

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
import server  # noqa: E402

FAILED = []


def case(name, got, want):
    if got != want:
        FAILED.append(name)
        print(f"FAIL  {name}\n        got:  {got!r}\n        want: {want!r}")
    else:
        print(f"PASS  {name}")


for text in ("Tell me a joke", "What is the capital of France", "What's it like outside the box", "Tell me Mara's shoe size"):
    case(f"claim: {text!r} isn't the brain's", server.ask(text=text, context=[], pretend_time=None, claim=True),
         {"status": "not_mine", "reason": "not_weather"})
for text in ("Will it rain tomorrow", "What's the weather", "When is sunset", "Is it nice out", "How many degrees is it",
             "Do I need sunscreen today", "When does it get dark"):
    case(f"claim: {text!r} is the brain's", server._claims(server._clean(text)), True)
case("a sun word that isn't a question, as before: not_mine", server.ask(text="What's a dark color", context=[], pretend_time=None,
                                                                          claim=True)["status"], "not_mine")
case("its Wepwawet section names the claim parameter", __import__("wepwawet").WEPWAWET["answers"]["claim"], "claim")
print(f"\n{'all pass' if not FAILED else str(len(FAILED)) + ' fail'}")
sys.exit(1 if FAILED else 0)
