"""How the weather brain fits a Wepwawet voice system (like Wepwawet Veil, the house router): its
x-wepwawet section (the Wepwawet standard, version 2: github.com/coderpigsfly/wepwawet_standard),
added to its OpenAPI document (/openapi.json), so the voice system lays it out from the brain's own
description."""

WEPWAWET = {
    "version": 2,
    "title": "Weather brain",
    "spoken": "the weather",          # what it's called out loud (expectation 1)
    "role": "answers",                # it answers the router's /ask door with a sentence
    # its data changes by the hour (expectation 15): hold an answer only briefly. How long, and a
    # scheduled pull, wait on dev-weather-brain #1 (live or cached)
    "data": {"kind": "transient", "pace": "fast"},
    "tabs": {"commands": True, "voice_map": False, "clean_up": False, "lists": False, "options": False},
    # its replies (status, and need: when for a day it can't place) are in its OpenAPI document, /ask's response
    # claim: the parameter a voice system sets when it asks whether a request is the brain's at all (dev-house-router
    # #28): not_mine unless the words are about the weather or the sun
    "answers": {"door": "GET /ask", "said": "text", "context": "context", "claim": "claim"},
    # its own commands, each with its starter and fields (expectation 13, a draft): the router asks
    # /ask today; these let a voice system call the brain's commands directly, and try the standard
    "commands": {
        "GET /weather": {"starts": ["what's the weather", "will it rain", "how's the weather", "forecast"],
                         "required": {}, "optional": {"when": "when"}},
        "GET /sun": {"starts": ["when is sunset", "when is sunrise", "when does it get dark", "when does it get light",
                                "how much daylight"],
                     "required": {"ask": "ask"}, "optional": {"when": "when"}},
    },
}


def described(spec):
    """The brain's OpenAPI document with its x-wepwawet section."""
    return dict(spec, **{"x-wepwawet": WEPWAWET})
