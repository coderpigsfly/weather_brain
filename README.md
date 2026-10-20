# Weather brain

A weather and sun app built to the **Wepwawet standard**: an extension to OpenAPI that lets an app
describe itself to a voice system, so the voice system can use it with no glue written for that
app. The weather brain is the standard's worked example. Point a Wepwawet voice system at its
`/openapi.json` and it plugs right in.

On its own, it answers questions about the weather and the sun for one house, in the person's own
words ("what's the weather tonight", "will it frost", "when does it get dark on Saturday"), with a
short sentence to speak. Ask about somewhere else, or too far ahead, and it says so instead of
guessing.

- **Forecasts** come from the US National Weather Service, so the house must be in the US.
- **Sun times** (first light, sunrise, sunset, dark, hours of daylight) are worked out locally.
- **Unusual weather** ("much colder than usual for October") is judged against your area's
  monthly climate normals.

## The Wepwawet standard

The standard (*What an app's API needs so it can be used by voice*) is published at
**[github.com/coderpigsfly/wepwawet_standard](https://github.com/coderpigsfly/wepwawet_standard)**. In short: a voice assistant sees no screen, its words come through
speech-to-text, and it must turn them into one exact call and say truthfully what happened. The
standard lists what an API needs for that, and an `x-wepwawet` section in the app's OpenAPI
document that says it. Tools that don't know the section ignore it (OpenAPI allows `x-` sections).

The weather brain's section, served in its own `/openapi.json`:

```json
"x-wepwawet": {
  "version": 1,
  "title": "Weather brain",
  "role": "answers",
  "tabs": {"commands": true, "voice_map": false, "clean_up": false, "lists": false, "options": false},
  "answers": {"door": "GET /ask", "said": "text", "context": "context"},
  "commands": {
    "GET /weather": {"starts": ["what's the weather", "will it rain", "..."], "optional": {"when": "when"}},
    "GET /sun": {"starts": ["when is sunset", "when does it get dark", "..."], "required": {"ask": "ask"}, "optional": {"when": "when"}}
  }
}
```

What that tells a voice system:

- **`role: answers`** (expectation 11): it understands words itself, so send it the request
  exactly as heard. Its one door is `GET /ask`, taking `text` and `context` (earlier requests,
  newest first, for "what about Sunday?").
- **`voice_map: false`, `clean_up: false`**: nothing to map words onto, nothing to strip. The
  brain reads "Do I need an umbrella on Saturday?" itself.
- **`lists: false`, `options: false`**: no people or projects to match, no knobs.
- **`commands`** (expectation 13, a draft): its `/weather` and `/sun` commands with the words a
  request for each opens with, for a voice system that calls commands directly.
- **`info: version`** (expectation 2): its real version (`app/version.py`), so a voice system
  notices an update.

Every answer has a status and a sentence, so nothing is made up elsewhere:

```json
{"status": "answered", "speech": "The sun sets at 6:15 this evening."}
{"status": "out_of_reach", "reason": "too_far", "speech": "I can only see seven days out."}
{"status": "not_mine", "reason": "not_a_sun_question"}
```

`not_mine` means the words weren't really for it ("what's a dark color"), so the voice system
passes the request on.

## Quick start

1. Copy `app/house.example.json` to `app/house.json` and fill in your house (below).
2. `docker compose up -d --build`
3. `curl "http://<server>:8765/ask?text=when+does+the+sun+set"`
4. Point your voice system at `http://<server>:8765/openapi.json`. For Home Assistant without one,
   see `ha/`.

Put `TZ=<your timezone>` (like `TZ=America/New_York`) in `.env` for log timestamps in local time.
`docker-compose.yml` runs the code straight from `./app` and restarts on changes.

## Your house: app/house.json

Everything about the house is in `app/house.json`; nothing about any one house is in the code:

- `place`: name, region, latitude, longitude and timezone (sun times, "today", "tonight").
- `home_words`: what counts as here ("here", "outside", your town's name), so "the weather in
  London" is known to be somewhere else.
- `day`: a day runs midnight to midnight. "today" is the rest of the day until `evening_starts`
  (17:00); from then on "today" and "tonight" both answer tonight; "tonight" asked at any hour is
  that day's evening, its low and frost looked up until `night_ends` (07:00) the next morning.
  "tomorrow" after midnight is the next calendar day.
- `forecast`: the National Weather Service grid (open `https://api.weather.gov/points/<lat>,<lon>`
  and copy gridId, gridX, gridY), the contact the Weather Service asks for (it goes in the
  User-Agent), the timeout and how long answers are remembered.
- `normals`: the nearest station's monthly climate normals (NCEI 1991-2020: high, low, rain and
  snow for each month), and how far from normal counts as unusual.

Until `house.json` exists the brain uses the example, and says so in its log. `house.json` is
never released.

## Its doors

| Door | What it's for |
|------|---------------|
| `GET /openapi.json` | Its spec, with the `x-wepwawet` section. `/docs` to try the doors in a browser. |
| `GET /ask?text=...` | The request in the person's own words (`context=` earlier requests, newest first). |
| `GET /weather?when=...` | A forecast: `today`, `tonight`, `now`, `tomorrow` or a weekday. Used by `ha/`. |
| `GET /sun?ask=...&when=...` | `first_light`, `sunrise`, `sunset`, `dark` or `daylight`, for the same `when`. Used by `ha/`. |
| `GET /health` | Is it running. |

Every door takes `pretend_time=` (like `2026-10-19T21:00`) to ask as if it were then.

## Tests

`tools/test_windows.py` (which hours "today", "tonight" and "tomorrow" cover) and
`tools/test_dates.py` (a date said with its month). They need the libraries in `requirements.txt`:

    pip install -r requirements.txt
    python3 tools/test_windows.py
    python3 tools/test_dates.py

## Version

`app/version.py` holds the version its spec shows (`info: version:`). Change it with every release.

## License

MIT: see `LICENSE`.
