# Changelog

Versions are year.month.release, the way Home Assistant numbers its own: 2026.10.0 is the first
release in October 2026, 2026.10.1 the next. The first public release was 1.0.0.

## 2026.10.0

- **It says when a request isn't its own.** A voice system that hasn't routed a request to it can
  ask with `claim=true`: it answers `not_mine` (reason `not_weather`) unless the words are about the
  weather or the sun. Without it, `/ask` answers as before. Its Wepwawet section names the parameter
  (`answers: claim`).
- **It names what it needs.** Asked about a day it can't place ("Is it going to rain for the
  picnic?"), it answers `status: need`, `need: when`, `about: the picnic`, instead of guessing
  today. A voice system can fill in the day from its other apps, or ask the person, and then ask
  again.
- **Its replies are in its OpenAPI document.** `/ask` lists its statuses (answered, out_of_reach,
  not_mine, need) and their fields. `need` names the parameter it's missing, as `GET /weather` and
  `GET /sun` take it (`when`).
- **Its Wepwawet section is version 2:** its spoken name ("the weather") and its data life
  (transient, fast).
- **A date said with its weekday** (the day a voice system puts in, "Sunday, March 28, 2027") is
  that date. Past the week, it says how far ahead it can see.

## 1.0.0

The first public release.
