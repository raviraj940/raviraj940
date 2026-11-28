#!/usr/bin/env python3
"""
GitHub Wrapped Analytics Generator
Fetches real GitHub stats for raviraj940 and generates SVG charts.
Requires: GH_TOKEN environment variable (GitHub Personal Access Token)
"""

import os
import sys
import json
import math
import datetime
import requests
from collections import defaultdict

# ─── CONFIG ────────────────────────────────────────────────────────────────────
USERNAME   = "raviraj940"
# Accept GH_TOKEN or the auto-provided GITHUB_TOKEN
GH_TOKEN   = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "charts")
GRAPHQL_URL = "https://api.github.com/graphql"

if not GH_TOKEN:
    print("ERROR: Neither GH_TOKEN nor GITHUB_TOKEN is set.", file=sys.stderr)
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Content-Type": "application/json",
}

# ─── HELPERS ────────────────────────────────────────────────────────────────────

def gql(query: str, variables: dict = None) -> dict:
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    r = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL error: {data['errors']}")
    return data["data"]


def rest_get(path: str) -> any:
    url = f"https://api.github.com{path}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def escape_xml(s: str) -> str:
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))

# ─── FETCH DATA ─────────────────────────────────────────────────────────────────

def fetch_contribution_data(year: int) -> dict:
    """Fetch contribution calendar for a given year."""
    start = f"{year}-01-01T00:00:00Z"
    end   = f"{year}-12-31T23:59:59Z"
    q = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
                weekday
              }
            }
          }
          commitContributionsByRepository(maxRepositories: 10) {
            repository { name primaryLanguage { name color } }
            contributions { totalCount }
          }
        }
        repositories(first: 10, orderBy: {field: UPDATED_AT, direction: DESC}, isFork: false) {
          nodes {
            name
            stargazerCount
            forkCount
            primaryLanguage { name color }
          }
        }
      }
    }
    """
    return gql(q, {"login": USERNAME, "from": start, "to": end})


def collect_all_days(calendar_weeks: list) -> list:
    days = []
    for week in calendar_weeks:
        for d in week["contributionDays"]:
            days.append(d)
    return sorted(days, key=lambda x: x["date"])


def compute_streaks(days: list):
    longest_streak = 0
    current_streak = 0
    longest_gap    = 0
    current_gap    = 0
    active_days    = 0
    weekend_contribs = 0

    for d in days:
        c = d["contributionCount"]
        wd = d["weekday"]  # 0=Sun … 6=Sat
        if c > 0:
            active_days += 1
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
            if current_gap > longest_gap:
                longest_gap = current_gap
            current_gap = 0
            if wd in (0, 6):
                weekend_contribs += c
        else:
            current_gap += 1
            current_streak = 0

    if current_gap > longest_gap:
        longest_gap = current_gap

    return longest_streak, longest_gap, active_days, weekend_contribs


def busiest_day(days: list) -> tuple:
    best = max(days, key=lambda d: d["contributionCount"])
    return best["date"], best["contributionCount"]


def monthly_contributions(days: list) -> dict:
    months = defaultdict(int)
    for d in days:
        month = d["date"][:7]  # "YYYY-MM"
        months[month] += d["contributionCount"]
    return dict(months)


def weekday_contributions(days: list) -> dict:
    names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    wdays = defaultdict(int)
    for d in days:
        wdays[names[d["weekday"]]] += d["contributionCount"]
    return dict(wdays)


def language_stats(commit_by_repo: list) -> dict:
    langs = defaultdict(int)
    for item in commit_by_repo:
        lang = (item["repository"].get("primaryLanguage") or {}).get("name")
        if lang:
            langs[lang] += item["contributions"]["totalCount"]
    return dict(sorted(langs.items(), key=lambda x: -x[1]))


LANG_COLORS = {
    "Python":     "#3572A5",
    "Java":       "#b07219",
    "TypeScript": "#2b7489",
    "JavaScript": "#f1e05a",
    "HTML":       "#e34c26",
    "CSS":        "#563d7c",
    "SQL":        "#e38c00",
    "Jupyter Notebook": "#DA5B0B",
    "Shell":      "#89e051",
    "Go":         "#00ADD8",
    "Rust":       "#dea584",
    "C++":        "#f34b7d",
    "C":          "#555555",
    "Ruby":       "#701516",
    "Swift":      "#ffac45",
    "Kotlin":     "#F18E33",
    "default":    "#6e7681",
}

def lang_color(name: str) -> str:
    return LANG_COLORS.get(name, LANG_COLORS["default"])

# ─── SVG GENERATORS ─────────────────────────────────────────────────────────────

def svg_header(width: int, height: int, title: str = "") -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&amp;display=swap');
      text {{ font-family: "Inter", "Segoe UI", system-ui, sans-serif; }}
    </style>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0d1117"/>
      <stop offset="100%" stop-color="#161b22"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#00C6FF"/>
      <stop offset="100%" stop-color="#0072FF"/>
    </linearGradient>
    <filter id="shadow">
      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#00C6FF33"/>
    </filter>
  </defs>
  <!-- Background -->
  <rect width="{width}" height="{height}" rx="16" fill="url(#bg)" stroke="#30363d" stroke-width="1.5"/>
'''


def svg_footer() -> str:
    return "</svg>\n"


def svg_title_bar(x: int, y: int, label: str, emoji: str = "") -> str:
    return f'''
  <!-- Section title -->
  <rect x="{x}" y="{y}" width="4" height="20" rx="2" fill="url(#accent)"/>
  <text x="{x+12}" y="{y+15}" fill="#e6edf3" font-size="14" font-weight="700">{escape_xml(emoji)} {escape_xml(label)}</text>
'''


def pct_color(pct: float) -> str:
    if pct >= 0.7:
        return "#00e676"
    if pct >= 0.4:
        return "#00C6FF"
    return "#7c3aed"


# ── 1. Heatmap ────────────────────────────────────────────────────────────────

def gen_heatmap(days: list, year: int) -> str:
    CELL = 11
    GAP  = 2
    COLS = 53
    ROWS = 7
    LEFT_PAD = 30
    TOP_PAD  = 50
    W = LEFT_PAD + COLS * (CELL + GAP) + 20
    H = TOP_PAD + ROWS * (CELL + GAP) + 30

    max_c = max((d["contributionCount"] for d in days), default=1) or 1

    def cell_color(count: int) -> str:
        if count == 0:
            return "#161b22"
        ratio = count / max_c
        if ratio < 0.25:  return "#0e4429"
        if ratio < 0.5:   return "#006d32"
        if ratio < 0.75:  return "#26a641"
        return "#39d353"

    # Build grid: week_col → list of (day_row, day)
    grid = defaultdict(dict)
    for d in days:
        dt   = datetime.date.fromisoformat(d["date"])
        jan1 = datetime.date(year, 1, 1)
        day_of_year = (dt - jan1).days
        week_col = (day_of_year + jan1.weekday() + 1) // 7
        day_row  = dt.weekday()  # 0=Mon … 6=Sun
        grid[week_col][day_row] = d

    day_labels = ["Mon", "", "Wed", "", "Fri", "", "Sun"]
    month_labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    svg  = svg_header(W, H)
    svg += f'  <text x="{LEFT_PAD}" y="28" fill="#8b949e" font-size="13" font-weight="700">Contribution Calendar {year}</text>\n'

    # Month labels
    for m in range(12):
        ref_dt = datetime.date(year, m + 1, 1)
        jan1   = datetime.date(year, 1, 1)
        doy    = (ref_dt - jan1).days
        col    = (doy + jan1.weekday() + 1) // 7
        mx     = LEFT_PAD + col * (CELL + GAP)
        svg   += f'  <text x="{mx}" y="{TOP_PAD - 6}" fill="#8b949e" font-size="9">{month_labels[m]}</text>\n'

    # Day labels
    for i, lbl in enumerate(day_labels):
        if lbl:
            ry = TOP_PAD + i * (CELL + GAP) + CELL - 2
            svg += f'  <text x="0" y="{ry}" fill="#8b949e" font-size="9">{lbl}</text>\n'

    # Cells
    for week_col in range(COLS):
        for day_row in range(ROWS):
            d     = grid.get(week_col, {}).get(day_row)
            count = d["contributionCount"] if d else 0
            color = cell_color(count)
            cx    = LEFT_PAD + week_col * (CELL + GAP)
            cy    = TOP_PAD  + day_row  * (CELL + GAP)
            tip   = f"{count} contributions on {d['date']}" if d else "No data"
            svg  += f'  <rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"><title>{escape_xml(tip)}</title></rect>\n'

    svg += svg_footer()
    return svg


# ── 2. Summary stats card ─────────────────────────────────────────────────────

def gen_summary_card(total: int, active: int, streak: int, gap: int,
                     weekend: int, busiest_date: str, busiest_count: int,
                     year: int) -> str:
    W, H = 800, 180
    svg  = svg_header(W, H)
    svg += f'  <text x="20" y="30" fill="#e6edf3" font-size="14" font-weight="700">📊 GitHub Wrapped {year} — Summary</text>\n'

    stats = [
        ("🔥", "Total Contributions", f"{total:,}"),
        ("📅", "Active Days", str(active)),
        ("⚡", "Longest Streak", f"{streak} days"),
        ("💤", "Longest Gap", f"{gap} days"),
        ("🎉", "Weekend Activity", f"{weekend:,}"),
        ("🏆", "Busiest Day", f"{busiest_date}\n{busiest_count} contribs"),
    ]

    card_w = 118
    for i, (emoji, label, value) in enumerate(stats):
        col = i % 6
        cx  = 10 + col * (card_w + 8)
        cy  = 48

        svg += f'''
  <rect x="{cx}" y="{cy}" width="{card_w}" height="118" rx="10"
        fill="#21262d" stroke="#30363d" stroke-width="1"/>
  <text x="{cx + card_w//2}" y="{cy + 24}" fill="#8b949e" font-size="18"
        text-anchor="middle">{emoji}</text>
  <text x="{cx + card_w//2}" y="{cy + 44}" fill="#8b949e" font-size="9"
        text-anchor="middle">{escape_xml(label)}</text>
'''
        # value may have newline
        lines = value.split("\n")
        for j, line in enumerate(lines):
            yv = cy + 68 + j * 18
            svg += f'  <text x="{cx + card_w//2}" y="{yv}" fill="#e6edf3" font-size="{"14" if j==0 else "10"}" font-weight="700" text-anchor="middle">{escape_xml(line)}</text>\n'

    svg += svg_footer()
    return svg


# ── 3. Language donut chart ───────────────────────────────────────────────────

def gen_language_donut(lang_data: dict) -> str:
    if not lang_data:
        return ""
    W, H = 400, 280
    CX, CY, R, r = 130, 145, 90, 55

    total = sum(lang_data.values()) or 1
    items = list(lang_data.items())[:7]

    svg  = svg_header(W, H)
    svg += '  <text x="20" y="28" fill="#e6edf3" font-size="14" font-weight="700">🧑‍💻 Top Languages</text>\n'

    # Draw donut slices
    start_angle = -math.pi / 2
    for name, count in items:
        pct   = count / total
        angle = pct * 2 * math.pi
        large = 1 if angle > math.pi else 0
        x1 = CX + R * math.cos(start_angle)
        y1 = CY + R * math.sin(start_angle)
        x2 = CX + R * math.cos(start_angle + angle)
        y2 = CY + R * math.sin(start_angle + angle)
        x3 = CX + r * math.cos(start_angle + angle)
        y3 = CY + r * math.sin(start_angle + angle)
        x4 = CX + r * math.cos(start_angle)
        y4 = CY + r * math.sin(start_angle)
        color = lang_color(name)
        path  = f"M {x1:.1f} {y1:.1f} A {R} {R} 0 {large} 1 {x2:.1f} {y2:.1f} L {x3:.1f} {y3:.1f} A {r} {r} 0 {large} 0 {x4:.1f} {y4:.1f} Z"
        svg  += f'  <path d="{path}" fill="{color}" stroke="#0d1117" stroke-width="2"><title>{escape_xml(name)}: {pct:.1%}</title></path>\n'
        start_angle += angle

    # Center text
    svg += f'  <text x="{CX}" y="{CY - 6}" fill="#e6edf3" font-size="12" font-weight="700" text-anchor="middle">Languages</text>\n'
    svg += f'  <text x="{CX}" y="{CY + 12}" fill="#8b949e" font-size="10" text-anchor="middle">{len(items)} detected</text>\n'

    # Legend
    lx = 275
    for i, (name, count) in enumerate(items):
        pct  = count / total
        ly   = 50 + i * 32
        color = lang_color(name)
        svg += f'  <rect x="{lx}" y="{ly}" width="10" height="10" rx="2" fill="{color}"/>\n'
        svg += f'  <text x="{lx + 14}" y="{ly + 9}" fill="#e6edf3" font-size="11">{escape_xml(name)}</text>\n'
        svg += f'  <text x="{W - 12}" y="{ly + 9}" fill="#8b949e" font-size="10" text-anchor="end">{pct:.1%}</text>\n'

    svg += svg_footer()
    return svg


# ── 4. Monthly bar chart ──────────────────────────────────────────────────────

def gen_monthly_bars(monthly: dict, year: int) -> str:
    W, H = 800, 220
    months_order = [f"{year}-{m:02d}" for m in range(1, 13)]
    values = [monthly.get(m, 0) for m in months_order]
    max_v  = max(values) or 1

    BAR_W  = 46
    GAP    = 14
    LEFT   = 40
    BOTTOM = H - 40
    CHART_H = H - 80

    svg  = svg_header(W, H)
    svg += f'  <text x="20" y="28" fill="#e6edf3" font-size="14" font-weight="700">📆 Contributions by Month ({year})</text>\n'

    # Gridlines
    for pct in [0.25, 0.5, 0.75, 1.0]:
        gy = BOTTOM - pct * CHART_H
        v  = int(pct * max_v)
        svg += f'  <line x1="{LEFT}" y1="{gy:.1f}" x2="{W-20}" y2="{gy:.1f}" stroke="#30363d" stroke-width="1" stroke-dasharray="4 4"/>\n'
        svg += f'  <text x="{LEFT - 5}" y="{gy + 4:.1f}" fill="#8b949e" font-size="9" text-anchor="end">{v}</text>\n'

    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    for i, (v, lbl) in enumerate(zip(values, month_names)):
        x = LEFT + i * (BAR_W + GAP)
        bar_h = (v / max_v) * CHART_H
        y     = BOTTOM - bar_h
        # Gradient fill per bar
        gid = f"barG{i}"
        pct_ratio = v / max_v
        c1  = "#00C6FF" if pct_ratio > 0.5 else "#0072FF"
        c2  = "#0072FF" if pct_ratio > 0.5 else "#7c3aed"
        svg += f'  <defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="{c1}"/><stop offset="100%" stop-color="{c2}"/></linearGradient></defs>\n'
        svg += f'  <rect x="{x:.1f}" y="{y:.1f}" width="{BAR_W}" height="{bar_h:.1f}" rx="4" fill="url(#{gid})"><title>{lbl}: {v} contributions</title></rect>\n'
        svg += f'  <text x="{x + BAR_W/2:.1f}" y="{BOTTOM + 15}" fill="#8b949e" font-size="10" text-anchor="middle">{lbl}</text>\n'
        if v > 0:
            svg += f'  <text x="{x + BAR_W/2:.1f}" y="{y - 4:.1f}" fill="#e6edf3" font-size="9" text-anchor="middle">{v}</text>\n'

    svg += svg_footer()
    return svg


# ── 4b. Smooth Activity Graph ──────────────────────────────────────────────────

def gen_activity_graph(monthly: dict, year: int) -> str:
    months_order = [f"{year}-{m:02d}" for m in range(1, 13)]
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    values = [monthly.get(m, 0) for m in months_order]
    max_v = max(values) if max(values) > 0 else 10

    W, H = 840, 240
    LEFT = 50
    RIGHT = W - 30
    BOTTOM = H - 45
    TOP = 55
    CHART_W = RIGHT - LEFT
    CHART_H = BOTTOM - TOP

    points = []
    for i, v in enumerate(values):
        x = LEFT + (i / 11) * CHART_W
        y = BOTTOM - (v / max_v) * CHART_H
        points.append((x, y, v, month_labels[i]))

    path_d = f"M {points[0][0]:.1f} {points[0][1]:.1f}"
    for i in range(len(points) - 1):
        x0, y0 = points[i][0], points[i][1]
        x1, y1 = points[i+1][0], points[i+1][1]
        cp1x = x0 + (x1 - x0) / 2
        cp1y = y0
        cp2x = x0 + (x1 - x0) / 2
        cp2y = y1
        path_d += f" C {cp1x:.1f} {cp1y:.1f}, {cp2x:.1f} {cp2y:.1f}, {x1:.1f} {y1:.1f}"

    area_d = path_d + f" L {points[-1][0]:.1f} {BOTTOM:.1f} L {points[0][0]:.1f} {BOTTOM:.1f} Z"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&amp;display=swap');
      text {{ font-family: "Inter", "Segoe UI", system-ui, sans-serif; }}
    </style>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0d1117"/>
      <stop offset="100%" stop-color="#161b22"/>
    </linearGradient>
    <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#00C6FF"/>
      <stop offset="100%" stop-color="#0072FF"/>
    </linearGradient>
    <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#00C6FF" stop-opacity="0.35"/>
      <stop offset="70%" stop-color="#0072FF" stop-opacity="0.10"/>
      <stop offset="100%" stop-color="#0072FF" stop-opacity="0.0"/>
    </linearGradient>
    <filter id="glow">
      <feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="#00C6FF" flood-opacity="0.6"/>
    </filter>
  </defs>

  <rect width="{W}" height="{H}" rx="16" fill="url(#bg)" stroke="#30363d" stroke-width="1.5"/>
  <text x="24" y="32" fill="#e6edf3" font-size="15" font-weight="700">📈 GitHub Activity Graph ({year})</text>
  <text x="{RIGHT}" y="32" fill="#8b949e" font-size="11" text-anchor="end">Monthly Contribution Trend</text>
'''

    for pct in [0.25, 0.5, 0.75, 1.0]:
        gy = BOTTOM - pct * CHART_H
        v_label = int(pct * max_v)
        svg += f'  <line x1="{LEFT}" y1="{gy:.1f}" x2="{RIGHT}" y2="{gy:.1f}" stroke="#30363d" stroke-width="1" stroke-dasharray="4 3"/>\n'
        svg += f'  <text x="{LEFT - 8}" y="{gy + 4:.1f}" fill="#8b949e" font-size="10" text-anchor="end">{v_label}</text>\n'

    svg += f'  <line x1="{LEFT}" y1="{BOTTOM}" x2="{RIGHT}" y2="{BOTTOM}" stroke="#30363d" stroke-width="1.5"/>\n'
    svg += f'  <text x="{LEFT - 8}" y="{BOTTOM + 4}" fill="#8b949e" font-size="10" text-anchor="end">0</text>\n'

    svg += f'  <path d="{area_d}" fill="url(#areaGrad)"/>\n'
    svg += f'  <path d="{path_d}" fill="none" stroke="url(#lineGrad)" stroke-width="3" stroke-linecap="round" filter="url(#glow)"/>\n'

    for x, y, v, lbl in points:
        svg += f'  <text x="{x:.1f}" y="{BOTTOM + 18}" fill="#8b949e" font-size="11" text-anchor="middle">{lbl}</text>\n'
        if v > 0:
            svg += f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#00C6FF" stroke="#ffffff" stroke-width="2"><title>{lbl}: {v} contributions</title></circle>\n'
            svg += f'  <text x="{x:.1f}" y="{y - 8:.1f}" fill="#e6edf3" font-size="10" font-weight="700" text-anchor="middle">{v}</text>\n'
        else:
            svg += f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#30363d"><title>{lbl}: 0 contributions</title></circle>\n'

    svg += svg_footer()
    return svg


# ── 5. Weekday bar chart ──────────────────────────────────────────────────────

def gen_weekday_bars(weekday: dict) -> str:
    # Medium format: 660px wide, balanced bar widths
    W, H   = 660, 240
    order  = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    values = [weekday.get(d, 0) for d in order]
    max_v  = max(values) or 1

    BAR_W   = 56   # medium bar width
    GAP     = 20   # spacing between bars
    LEFT    = 55   # left padding for y-axis labels
    BOTTOM  = H - 48
    CHART_H = H - 90

    svg  = svg_header(W, H)
    svg += f'  <text x="24" y="30" fill="#e6edf3" font-size="15" font-weight="700">📅 Contributions by Weekday</text>\n'

    # Gridlines + y-axis labels
    for pct in [0.25, 0.5, 0.75, 1.0]:
        gy = BOTTOM - pct * CHART_H
        v  = int(pct * max_v)
        svg += f'  <line x1="{LEFT}" y1="{gy:.1f}" x2="{W - 20}" y2="{gy:.1f}" stroke="#30363d" stroke-width="1" stroke-dasharray="4 3"/>\n'
        svg += f'  <text x="{LEFT - 8}" y="{gy + 4:.1f}" fill="#8b949e" font-size="10" text-anchor="end">{v}</text>\n'

    colors = ["#00C6FF","#00C6FF","#00C6FF","#00C6FF","#00C6FF","#39d353","#39d353"]
    weekend_label = ["", "", "", "", "", "Weekend", "Weekend"]

    for i, (v, lbl) in enumerate(zip(values, order)):
        x     = LEFT + i * (BAR_W + GAP)
        bar_h = max((v / max_v) * CHART_H, 2)   # min 2px so zero is visible
        y     = BOTTOM - bar_h
        color = colors[i]

        # Bar with rounded top
        svg += f'  <rect x="{x:.1f}" y="{y:.1f}" width="{BAR_W}" height="{bar_h:.1f}" rx="5" fill="{color}" opacity="0.90"><title>{lbl}: {v} contributions</title></rect>\n'

        # Count label above bar
        label_y = y - 7 if v > 0 else BOTTOM - 14
        svg += f'  <text x="{x + BAR_W/2:.1f}" y="{label_y:.1f}" fill="#e6edf3" font-size="12" font-weight="700" text-anchor="middle">{v}</text>\n'

        # Day name label
        svg += f'  <text x="{x + BAR_W/2:.1f}" y="{BOTTOM + 18}" fill="#8b949e" font-size="12" text-anchor="middle">{lbl}</text>\n'

    # Legend
    svg += f'  <circle cx="{W-130}" cy="22" r="5" fill="#00C6FF"/>\n'
    svg += f'  <text x="{W-121}" y="26" fill="#8b949e" font-size="10">Weekday</text>\n'
    svg += f'  <circle cx="{W-68}" cy="22" r="5" fill="#39d353"/>\n'
    svg += f'  <text x="{W-59}" y="26" fill="#8b949e" font-size="10">Weekend</text>\n'

    svg += svg_footer()
    return svg


# ── 6. Top repos card ─────────────────────────────────────────────────────────

def gen_top_repos(repos: list, commit_by_repo: list) -> str:
    commit_map = {
        item["repository"]["name"]: item["contributions"]["totalCount"]
        for item in commit_by_repo
    }
    enriched = []
    for r in repos:
        name    = r["name"]
        stars   = r.get("stargazerCount", 0)
        forks   = r.get("forkCount", 0)
        lang    = (r.get("primaryLanguage") or {}).get("name", "")
        commits = commit_map.get(name, 0)
        enriched.append((name, stars, forks, lang, commits))

    enriched.sort(key=lambda x: -x[4])
    top = enriched[:5]

    # Fixed column positions — nothing bleeds outside the card
    W        = 860
    ROW      = 64
    H        = 54 + len(top) * ROW + 16
    RANK_CX  = 34          # rank circle center-x
    NAME_X   = 58          # repo name start
    BAR_X    = 58          # progress bar start
    BAR_MAX  = 320         # max bar width (stays well inside the card)
    LANG_X   = 420         # language dot + name column
    STAT_X   = W - 20      # stars/forks/commits, right-aligned

    svg  = svg_header(W, H)
    svg += f'  <text x="20" y="34" fill="#e6edf3" font-size="15" font-weight="700">🏆 Most Active Repositories</text>\n'

    for i, (name, stars, forks, lang, commits) in enumerate(top):
        y     = 50 + i * ROW
        rank  = i + 1
        color = lang_color(lang)
        pct   = commits / (top[0][4] or 1)
        bar_w = max(int(pct * BAR_MAX), 4)

        # Card background
        svg += f'  <rect x="12" y="{y}" width="{W-24}" height="{ROW-6}" rx="8" fill="#21262d" stroke="#30363d" stroke-width="1"/>\n'

        # Rank badge
        svg += f'  <circle cx="{RANK_CX}" cy="{y+26}" r="12" fill="#30363d"/>\n'
        svg += f'  <text x="{RANK_CX}" y="{y+30}" fill="#8b949e" font-size="11" font-weight="700" text-anchor="middle">#{rank}</text>\n'

        # Repo name — truncate if too long (max 26 chars before LANG_X)
        display_name = (name[:24] + "…") if len(name) > 24 else name
        svg += f'  <text x="{NAME_X}" y="{y+22}" fill="#e6edf3" font-size="13" font-weight="700">{escape_xml(display_name)}</text>\n'

        # Progress bar under name
        svg += f'  <rect x="{BAR_X}" y="{y+32}" width="{bar_w}" height="5" rx="2" fill="{color}" opacity="0.75"/>\n'
        svg += f'  <text x="{BAR_X}" y="{y+48}" fill="#6e7681" font-size="9">{int(pct*100)}% of top activity</text>\n'

        # Language dot + name (fixed column, truncated)
        if lang:
            lang_disp = (lang[:14] + "…") if len(lang) > 14 else lang
            svg += f'  <circle cx="{LANG_X}" cy="{y+22}" r="5" fill="{color}"/>\n'
            svg += f'  <text x="{LANG_X+12}" y="{y+26}" fill="#8b949e" font-size="11">{escape_xml(lang_disp)}</text>\n'

        # Stats — right-aligned, all on one line
        stats_str = f"⭐ {stars}  🍴 {forks}  💾 {commits} commits"
        svg += f'  <text x="{STAT_X}" y="{y+26}" fill="#8b949e" font-size="11" text-anchor="end">{escape_xml(stats_str)}</text>\n'

    svg += svg_footer()
    return svg


# ── 7. Circular progress – coding time estimate ───────────────────────────────

def gen_coding_time(weekday: dict) -> str:
    """
    GitHub doesn't expose time-of-day data via public API.
    We display weekday distribution as circular progress bars
    and label this section clearly.
    """
    W, H = 420, 300
    svg  = svg_header(W, H)
    svg += '  <text x="20" y="28" fill="#e6edf3" font-size="14" font-weight="700">⏰ Activity by Weekday (Circular)</text>\n'
    svg += '  <text x="20" y="44" fill="#8b949e" font-size="10">Time-of-day data is not available via GitHub API</text>\n'

    order  = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    values = [weekday.get(d, 0) for d in order]
    total  = sum(values) or 1

    CX_START = 60
    CY = 170
    SPACING = 56
    R_OUTER = 24
    R_INNER = 16
    STROKE   = 6

    for i, (lbl, v) in enumerate(zip(order, values)):
        cx   = CX_START + i * SPACING
        pct  = v / total
        circ = 2 * math.pi * (R_OUTER - STROKE / 2)
        dash = pct * circ
        gap  = circ - dash
        color = "#39d353" if lbl in ("Sat", "Sun") else "#00C6FF"

        # Background ring
        svg += f'  <circle cx="{cx}" cy="{CY}" r="{R_OUTER - STROKE/2}" fill="none" stroke="#30363d" stroke-width="{STROKE}"/>\n'
        # Progress arc
        svg += f'''  <circle cx="{cx}" cy="{CY}" r="{R_OUTER - STROKE/2}"
    fill="none" stroke="{color}" stroke-width="{STROKE}"
    stroke-dasharray="{dash:.2f} {gap:.2f}"
    stroke-dashoffset="{circ/4:.2f}"
    stroke-linecap="round"/>\n'''
        svg += f'  <text x="{cx}" y="{CY+5}" fill="#e6edf3" font-size="9" text-anchor="middle" font-weight="700">{int(pct*100)}%</text>\n'
        svg += f'  <text x="{cx}" y="{CY+30}" fill="#8b949e" font-size="9" text-anchor="middle">{lbl}</text>\n'
        svg += f'  <text x="{cx}" y="{CY+42}" fill="#8b949e" font-size="8" text-anchor="middle">{v}</text>\n'

    svg += svg_footer()
    return svg


# ─── MAIN ────────────────────────────────────────────────────────────────────────

def main():
    if not GH_TOKEN:
        print("ERROR: GH_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    year = datetime.date.today().year
    print(f"Fetching GitHub data for @{USERNAME} ({year})…")

    data        = fetch_contribution_data(year)
    user        = data["user"]
    coll        = user["contributionsCollection"]
    calendar    = coll["contributionCalendar"]
    all_days    = collect_all_days(calendar["weeks"])
    total       = calendar["totalContributions"]
    commit_by_r = coll["commitContributionsByRepository"]
    repos       = user["repositories"]["nodes"]

    streak, gap, active, weekend = compute_streaks(all_days)
    b_date, b_count              = busiest_day(all_days)
    monthly   = monthly_contributions(all_days)
    wday      = weekday_contributions(all_days)
    langs     = language_stats(commit_by_r)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    charts = {
        "activity_graph.svg": gen_activity_graph(monthly, year),
        "heatmap.svg":        gen_heatmap(all_days, year),
        "summary.svg":        gen_summary_card(total, active, streak, gap,
                                               weekend, b_date, b_count, year),
        "languages.svg":      gen_language_donut(langs),
        "monthly_bars.svg":   gen_monthly_bars(monthly, year),
        "weekday_bars.svg":   gen_weekday_bars(wday),
        "top_repos.svg":      gen_top_repos(repos, commit_by_r),
        "coding_time.svg":    gen_coding_time(wday),
    }

    for fname, content in charts.items():
        path = os.path.join(OUTPUT_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✔ Written: {fname}")

    # Save JSON snapshot for debugging / caching
    snapshot = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "year": year,
        "username": USERNAME,
        "total_contributions": total,
        "active_days": active,
        "longest_streak": streak,
        "longest_gap": gap,
        "weekend_contributions": weekend,
        "busiest_day": {"date": b_date, "count": b_count},
        "monthly": monthly,
        "weekday": wday,
        "languages": langs,
    }
    snap_path = os.path.join(OUTPUT_DIR, "snapshot.json")
    with open(snap_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)
    print(f"  ✔ Written: snapshot.json")
    print("Done! All charts generated successfully.")


if __name__ == "__main__":
    main()
