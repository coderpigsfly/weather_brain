"""How the weather brain fits a Wepwawet voice system (like Wepwawet Veil, the house router): its
x-wepwawet section (the Wepwawet standard, version 1: github.com/coderpigsfly/wepwawet_standard),
added to its OpenAPI document (/openapi.json), so the voice system lays it out from the brain's own
description."""

WEPWAWET = {
    "version": 1,
    "title": "Weather brain",
    "role": "answers",                # it answers the router's /ask door with a sentence
    "tabs": {"commands": True, "voice_map": False, "clean_up": False, "lists": False, "options": False},
    "answers": {"door": "GET /ask", "said": "text", "context": "context"},
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
