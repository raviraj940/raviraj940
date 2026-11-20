# GitHub Wrapped – Scripts

This directory contains the analytics generator that powers the GitHub Wrapped
dashboard in the profile README.

## Files

| File | Purpose |
|------|---------|
| `generate_stats.py` | Main script — fetches GitHub data via GraphQL API and generates SVG charts |
| `github-contribution-blinker.user.js` | Tampermonkey / Chrome userscript for fast random blinking animation directly on `github.com/raviraj940` |
| `requirements.txt` | Python dependencies (`requests`) |

## How it works

1. **GitHub Actions** runs `generate_stats.py` on a daily schedule (02:30 UTC).
2. The script authenticates using the `GH_TOKEN` repository secret.
3. It queries the **GitHub GraphQL API** for real contribution data.
4. Seven SVG charts are written to `../assets/charts/`.
5. The workflow commits and pushes the updated charts back to the repo.
6. The `README.md` references these SVGs with relative paths — GitHub serves them directly.

## Running locally

```bash
# 1. Install dependencies
pip install -r scripts/requirements.txt

# 2. Set your GitHub token
export GH_TOKEN=ghp_your_token_here

# 3. Run the generator
python scripts/generate_stats.py
```

## Required GitHub Secret

| Secret name | Value |
|-------------|-------|
| `GH_TOKEN`  | A GitHub Personal Access Token with `repo` scope |

### Creating the token

1. Go to **GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)**
2. Click **Generate new token**
3. Select scopes: `repo` (full control of private repositories) — or at minimum `public_repo` for a public profile repo
4. Copy the token value
5. In your profile repo: **Settings → Secrets and variables → Actions → New repository secret**
6. Name: `GH_TOKEN`, Value: (paste your token)

## Generated charts

| File | Description |
|------|-------------|
| `heatmap.svg` | Full-year contribution calendar heatmap |
| `summary.svg` | Key stats: total contributions, active days, streaks, gaps, weekend activity, busiest day |
| `monthly_bars.svg` | Bar chart of contributions by month |
| `weekday_bars.svg` | Bar chart of contributions by weekday |
| `languages.svg` | Donut chart of most-used programming languages |
| `top_repos.svg` | Most active repositories with commit counts |
| `coding_time.svg` | Circular progress indicators for weekday activity distribution |
| `snapshot.json` | Raw data snapshot for debugging/caching |
