# OTH Scorecard

Stableford points scorecard for Windyke CC (West and East) with Golf Bunch targets.

- `index.html` is the whole app (GitHub Pages serves it).
- `targets.json` holds player targets. A GitHub Action (`.github/workflows/update-targets.yml`) refreshes it from the Golf Bunch targets page every 30 minutes from 0400 to 0700 Central. Run it on demand from the **Actions** tab → **Update targets** → **Run workflow**.
