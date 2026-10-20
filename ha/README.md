# Home Assistant side

The Home Assistant package that talks to the Weather Brain: voice questions about the weather
and the sun, answered by the brain, with a basic fallback when it can't be reached.

| File here              | Goes in HA as                   |
|------------------------|---------------------------------|
| `weather.example.yaml` | `/config/packages/weather.yaml` |

Setting it up:
1. Packages on: in `configuration.yaml`, `homeassistant:` → `packages: !include_dir_named packages`.
2. Copy `weather.example.yaml` to `/config/packages/weather.yaml` (File Editor) and fill in:
   - `<server>` in the two urls: the address of the machine running the brain.
   - `media_player.your_speaker`: the speaker clips play on when a question was typed.
   - Optional: `router_agents`, voice devices whose questions go to their own conversation agent.
   - Optional: clips, mp3s in `/media/weather/`; their names in the lists and `play_chance` above 0.
3. Restart Home Assistant (or reload automations, scripts and REST commands).

Keeping your own copy: keep your filled-in version beside the example as `weather.yaml`
(release.yaml never publishes it). HA never reads it from here; this folder is the backup with
history.
- Changed it in HA? Paste the new version over `weather.yaml` here, then commit and push.
- Changed it here? `git pull`, then paste it into HA's File Editor and reload.
- Changed what it does (not just your settings)? Make the same change in `weather.example.yaml`
  before the next release.
