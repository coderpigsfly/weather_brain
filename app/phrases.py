"""
Everything the brain says, in one place.
Each insight has several versions; one is picked at random.
Edit freely - just keep the {names} in curly braces.
"""

import random

PHRASES = {
    "soaking_rain": [
        "Expect a soaking rain, {rain}.",
        "It'll be a wet one, {rain} of rain.",
        "Plenty of rain on the way, {rain}.",
    ],
    "some_rain": [
        "Some showers, {rain}.",
        "A bit of rain, {rain}.",
        "Expect a few showers, {rain}.",
    ],
    "heavy_rain_night": [
        "Heavy rain overnight, {rain}, so keep the windows closed.",
        "It'll pour tonight, {rain}. Best to close the windows.",
        "A soaking rain tonight, {rain}. Check that the windows are shut.",
    ],
    "rain_timing": [
        "The rain should arrive around {time}.",
        "Rain looks likely starting around {time}.",
        "Expect the rain to move in around {time}.",
    ],
    "rain_heavier": [
        "Light showers turn steadier later on.",
        "It starts out light but picks up as it goes.",
        "Showers start light and get heavier later.",
    ],
    "rain_lighter": [
        "The rain tapers off later on.",
        "It should ease up later.",
        "Heavier at first, then tapering off.",
    ],
    "cold_rain": [
        "It'll be a raw, chilly rain.",
        "A cold rain, so dress warm.",
        "Bundle up, it's a chilly rain.",
    ],
    "jacket": [
        "You'll want a jacket {when}.",
        "Grab a jacket, it'll be chilly {when}.",
        "Jacket weather {when}.",
    ],
    "frost": [
        "Patchy frost is possible, so cover any tender plants.",
        "It could get frosty, with a low near {low}.",
        "A chilly night near {low}, frost is possible.",
    ],
    "freeze": [
        "It'll drop below freezing, so the cars will be frosty in the morning.",
        "Below freezing tonight, give yourself time to scrape the windshield.",
        "A frosty one tonight, down to {low}.",
    ],
    "hard_freeze": [
        "A hard freeze tonight, down to {low}. Protect the plants and outdoor pipes.",
        "Bitter cold tonight, {low} degrees. Bring in anything that can freeze.",
    ],
    "snow": [
        "Snow is in the forecast, {snow}.",
        "Expect snow, {snow}.",
        "Get ready for snow, {snow}.",
    ],
    "ice": [
        "Watch out for freezing rain. Roads and steps may be icy.",
        "Ice is possible, so be careful on the steps and the roads.",
    ],
    "windy": [
        "It'll be gusty, up to {gust} miles an hour.",
        "Hold onto your hat, gusts up to {gust}.",
        "Windy at times, with gusts near {gust}.",
    ],
    "storms": [
        "Thunderstorms are possible.",
        "There's a chance of thunderstorms.",
        "Keep an ear out for thunder.",
    ],
    "feels_cold": [
        "With the wind it'll feel like {feels}.",
        "It'll feel more like {feels} out there.",
    ],
    "feels_hot": [
        "It'll feel like {feels} with the humidity.",
        "The heat index reaches {feels}, so take it easy outside.",
    ],
    "unusual_warm": [
        "That's unusually warm for {month}.",
        "Pretty mild for {month}.",
        "Warmer than usual for {month}.",
    ],
    "unusual_cool": [
        "That's unusually cool for {month}.",
        "Chilly for {month}.",
        "Cooler than usual for {month}.",
    ],
    "alert": [
        "Heads up, there's a {alert} in effect.",
        "The weather service has issued a {alert}.",
    ],
}


# One shuffled "bag" per phrase: every version is used once before any repeats.
_bags = {}


def say(kind, **values):
    """Draw the next version of a phrase from its shuffled bag and fill in the numbers."""
    options = PHRASES.get(kind)
    if not options:
        return ""
    bag = _bags.get(kind)
    if not bag:
        bag = list(options)
        random.shuffle(bag)
        _bags[kind] = bag
    return bag.pop().format(**values)


# ---------- Darkness and the sun ----------

PHRASES.update({
    "dark_rain": [
        "Rain after dark tonight, so the roads will be hard to see. Take it slow.",
        "It'll be raining after dark. Watch the back roads.",
        "Wet and dark later, so drive carefully.",
    ],
    "dark_fog": [
        "Fog is likely after dark, so keep it slow on the back roads.",
        "Foggy after dark. Take it easy driving.",
    ],
    "dark_snow": [
        "Snow after dark, so the roads could get slick and hard to see.",
        "Snowy after dark. Be careful driving.",
    ],
    "dark_by": [
        "It'll be dark by {time}.",
        "Darkness falls around {time}.",
        "Headlights on by {time}.",
    ],
    "first_light_q": [
        "First light is around {time} {day}.",
        "It starts getting light around {time} {day}.",
    ],
    "first_light_q_past": [
        "It got light around {time} {day}.",
    ],
    "sunrise_q": [
        "The sun rises at {time} {day}.",
        "Sunrise is at {time} {day}.",
    ],
    "sunrise_q_past": [
        "The sun came up at {time} {day}.",
    ],
    "sunset_q": [
        "Sunset is at {time} {day}.",
        "The sun sets at {time} {day}.",
    ],
    "sunset_q_past": [
        "The sun set at {time} {day}.",
    ],
    "dark_q": [
        "It'll be dark by {time} {day}.",
        "Full dark comes around {time} {day}.",
        "You'll need headlights by {time} {day}.",
    ],
    "dark_q_past": [
        "It got dark around {time} {day}.",
    ],
    "daylight_q": [
        "There's {hours} of daylight {day}.",
        "You've got {hours} of daylight {day}.",
    ],
})


# ---------- Sun times in the forecast, and dark drive times ----------

PHRASES.update({
    "sun_both": [
        "The sun's up at {sunrise}, and it's dark by {dark}.",
        "Sunrise is at {sunrise}, and full dark by {dark}.",
        "Light from {sunrise} until about {dark}.",
    ],
    "sun_evening": [
        "Sunset's at {sunset}, and it's dark by {dark}.",
        "The sun sets at {sunset}, dark by {dark}.",
        "Headlights on by {dark}, with sunset at {sunset}.",
    ],
    "dark_morning_rain": [
        "Rain in the dark before sunrise, so the early drive could be slick.",
        "Wet and dark early in the morning. Take it easy on the back roads.",
    ],
    "dark_morning_fog": [
        "Fog before sunrise, so take it slow on the early drive.",
        "Foggy and dark early. Easy on the back roads.",
    ],
    "dark_morning_snow": [
        "Snow before sunrise, so the early roads could be slick.",
        "Snowy and dark early in the morning. Leave extra time.",
    ],
    "dark_evening_rain": [
        "Rain moves in around dark, so the drive home could be rough.",
        "Wet roads after dark this evening, so take it slow.",
        "Expect rain around dusk. Headlights and patience.",
    ],
    "dark_evening_fog": [
        "Fog around dark, so keep it slow on the back roads.",
        "Foggy after dark this evening. Easy on the drive home.",
    ],
    "dark_evening_snow": [
        "Snow around dark, so the drive home could be slick.",
        "Snowy after dark this evening. Take it slow.",
    ],
})


# ---------- /ask: lines for questions the brain can't serve ----------
# Never questions; the router decides what happens next.
PHRASES.update({
    "too_far": [
        "My forecast only reaches a week ahead.",
        "I can only see seven days out.",
        "That's further than my forecast reaches. I can do the next seven days.",
    ],
    "past": [
        "That day's already gone by. I only see the days ahead.",
        "I only forecast the days to come, not ones already past.",
    ],
    "span": [
        "I read the weather one day at a time. Name a day and I'll tell you.",
        "Pick a day and I'll give you its forecast.",
        "I do the weather one day at a time. Just name the day.",
    ],
    "place": [
        "I only know the weather here at home, not in {place}.",
        "I only keep an eye on the sky right here, not {place}.",
    ],
})
