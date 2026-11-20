#!/usr/bin/env python3
"""Build dashboard/index.html with embedded real contribution cells."""
import os
import json
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEATMAP_PATH = os.path.join(ROOT, "assets", "charts", "heatmap.svg")
OUT_PATH = os.path.join(ROOT, "dashboard", "index.html")

def parse_heatmap_cells():
    tree = ET.parse(HEATMAP_PATH)
    root = tree.getroot()
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    cells = []
    for r in root.findall('.//svg:rect', ns):
        if r.get('width') == '11':
            cells.append({
                'x': float(r.get('x')),
                'y': float(r.get('y')),
                'fill': r.get('fill'),
                'title': r.findtext('svg:title', default='', namespaces=ns)
            })
    return cells

cells = parse_heatmap_cells()

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Ravi Raj (@raviraj940) — Live Animated GitHub Contribution Calendar</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0d1117;
      --card-bg: #161b22;
      --border: #30363d;
      --border-accent: #00C6FF;
      --text: #e6edf3;
      --text-muted: #8b949e;
      --c0: #161b22;
      --c1: #0e4429;
      --c2: #006d32;
      --c3: #26a641;
      --c4: #39d353;
      --glow-1: #56ff9f;
      --glow-2: #00ff88;
      --glow-3: #7ee787;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 32px 16px;
      line-height: 1.5;
    }}

    .container {{
      width: 100%;
      max-width: 900px;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }}

    /* Header */
    header {{
      background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    }}

    .user-info {{
      display: flex;
      align-items: center;
      gap: 16px;
    }}

    .avatar {{
      width: 56px;
      height: 56px;
      border-radius: 50%;
      border: 2px solid #00C6FF;
      background: #21262d;
    }}

    .title-group h1 {{
      font-size: 1.35rem;
      font-weight: 700;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .badge-live {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(57, 211, 83, 0.15);
      border: 1px solid rgba(57, 211, 83, 0.4);
      color: #39d353;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.5px;
    }}

    .badge-live .dot {{
      width: 7px;
      height: 7px;
      background: #39d353;
      border-radius: 50%;
      box-shadow: 0 0 8px #39d353;
      animation: pulseDot 1.2s infinite ease-in-out;
    }}

    @keyframes pulseDot {{
      0%, 100% {{ opacity: 1; transform: scale(1); }}
      50% {{ opacity: 0.4; transform: scale(0.75); }}
    }}

    .title-group p {{
      font-size: 0.88rem;
      color: var(--text-muted);
    }}

    .nav-link {{
      color: #00C6FF;
      text-decoration: none;
      font-size: 0.88rem;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 14px;
      border: 1px solid rgba(0, 198, 255, 0.3);
      border-radius: 8px;
      transition: all 0.2s ease;
      background: rgba(0, 198, 255, 0.05);
    }}

    .nav-link:hover {{
      background: rgba(0, 198, 255, 0.15);
      border-color: #00C6FF;
    }}

    /* Stats strip */
    .stats-strip {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 12px;
    }}

    .stat-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px 16px;
      text-align: center;
    }}

    .stat-value {{
      font-size: 1.4rem;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
      color: #00E5FF;
    }}

    .stat-label {{
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-top: 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    /* Calendar Card */
    .calendar-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
      overflow-x: auto;
    }}

    .calendar-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      flex-wrap: wrap;
      gap: 10px;
    }}

    .calendar-title {{
      font-size: 1rem;
      font-weight: 600;
      color: var(--text);
    }}

    .legend {{
      display: flex;
      align-items: center;
      gap: 5px;
      font-size: 0.75rem;
      color: var(--text-muted);
    }}

    .legend-box {{
      width: 11px;
      height: 11px;
      border-radius: 2px;
    }}

    /* SVG Grid */
    .calendar-svg-wrapper {{
      width: 100%;
      display: flex;
      justify-content: center;
      padding: 8px 0;
    }}

    svg.calendar-svg {{
      width: 100%;
      height: auto;
      max-width: 820px;
      overflow: visible;
    }}

    .cell {{
      cursor: pointer;
      rx: 2px;
      transition: fill 200ms ease, filter 200ms ease, transform 200ms ease;
      transform-origin: center;
    }}

    .cell:hover {{
      stroke: #fff;
      stroke-width: 1px;
    }}

    /* Blinking active styles */
    .cell.blink-level-1 {{
      fill: #39d353 !important;
      filter: drop-shadow(0 0 4px #39d353);
    }}
    .cell.blink-level-2 {{
      fill: #56ff9f !important;
      filter: drop-shadow(0 0 6px #00ff88);
    }}
    .cell.blink-level-3 {{
      fill: #00ff88 !important;
      filter: drop-shadow(0 0 8px #56ff9f);
    }}
    .cell.blink-level-4 {{
      fill: #b9ffcb !important;
      filter: drop-shadow(0 0 10px #00ff88);
    }}

    /* Controls Panel */
    .controls-panel {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 18px 24px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}

    .control-group {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}

    .btn {{
      background: #21262d;
      border: 1px solid var(--border);
      color: var(--text);
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
    }}

    .btn:hover {{
      background: #30363d;
      border-color: #8b949e;
    }}

    .btn.primary {{
      background: #238636;
      border-color: rgba(240, 246, 252, 0.1);
      color: #fff;
    }}
    .btn.primary:hover {{
      background: #2ea043;
    }}

    .range-group {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.82rem;
      color: var(--text-muted);
    }}

    input[type="range"] {{
      accent-color: #00C6FF;
      cursor: pointer;
    }}

    .status-text {{
      font-size: 0.82rem;
      color: var(--text-muted);
      font-family: 'JetBrains Mono', monospace;
    }}

    /* Tooltip */
    #tooltip {{
      position: fixed;
      background: #1c2128;
      color: #e6edf3;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 6px 10px;
      font-size: 0.75rem;
      pointer-events: none;
      display: none;
      z-index: 1000;
      box-shadow: 0 4px 12px rgba(0,0,0,0.5);
      font-family: 'Inter', system-ui, sans-serif;
    }}

    /* Accessibility prefers-reduced-motion */
    @media (prefers-reduced-motion: reduce) {{
      .cell {{
        transition: none !important;
        animation: none !important;
      }}
      .badge-live .dot {{
        animation: none;
      }}
    }}

    footer {{
      text-align: center;
      color: var(--text-muted);
      font-size: 0.82rem;
      margin-top: 20px;
    }}
  </style>
</head>
<body>
  <div id="tooltip"></div>

  <div class="container">
    <!-- Header -->
    <header>
      <div class="user-info">
        <img src="https://github.com/raviraj940.png" alt="Ravi Raj" class="avatar" />
        <div class="title-group">
          <h1>
            Ravi Raj
            <span class="badge-live">
              <span class="dot"></span> LIVE CODING
            </span>
          </h1>
          <p>GitHub Wrapped Activity &amp; Live Contribution Monitor</p>
        </div>
      </div>
      <a href="https://github.com/raviraj940" class="nav-link" target="_blank" rel="noopener">
        <span>View Profile on GitHub</span> &rarr;
      </a>
    </header>

    <!-- Stats summary -->
    <div class="stats-strip">
      <div class="stat-card">
        <div class="stat-value">87</div>
        <div class="stat-label">Total Contributions</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">39</div>
        <div class="stat-label">Active Days</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">5 days</div>
        <div class="stat-label">Longest Streak</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" id="activeSquaresCount">0</div>
        <div class="stat-label">Blinking Squares</div>
      </div>
    </div>

    <!-- Calendar Card -->
    <div class="calendar-card">
      <div class="calendar-header">
        <div class="calendar-title">Contribution Calendar 2026 (Live Blinking Activity)</div>
        <div class="legend">
          <span>Less</span>
          <div class="legend-box" style="background: var(--c0); border: 1px solid var(--border);"></div>
          <div class="legend-box" style="background: var(--c1);"></div>
          <div class="legend-box" style="background: var(--c2);"></div>
          <div class="legend-box" style="background: var(--c3);"></div>
          <div class="legend-box" style="background: var(--c4);"></div>
          <span>More</span>
        </div>
      </div>

      <div class="calendar-svg-wrapper">
        <svg class="calendar-svg" viewBox="0 0 740 172" id="calendarSvg">
          <!-- Month labels -->
          <text x="30" y="32" fill="#8b949e" font-size="9">Jan</text>
          <text x="95" y="32" fill="#8b949e" font-size="9">Feb</text>
          <text x="147" y="32" fill="#8b949e" font-size="9">Mar</text>
          <text x="199" y="32" fill="#8b949e" font-size="9">Apr</text>
          <text x="251" y="32" fill="#8b949e" font-size="9">May</text>
          <text x="316" y="32" fill="#8b949e" font-size="9">Jun</text>
          <text x="368" y="32" fill="#8b949e" font-size="9">Jul</text>
          <text x="420" y="32" fill="#8b949e" font-size="9">Aug</text>
          <text x="485" y="32" fill="#8b949e" font-size="9">Sep</text>
          <text x="537" y="32" fill="#8b949e" font-size="9">Oct</text>
          <text x="602" y="32" fill="#8b949e" font-size="9">Nov</text>
          <text x="654" y="32" fill="#8b949e" font-size="9">Dec</text>
          <!-- Day labels -->
          <text x="0" y="47" fill="#8b949e" font-size="9">Mon</text>
          <text x="0" y="73" fill="#8b949e" font-size="9">Wed</text>
          <text x="0" y="99" fill="#8b949e" font-size="9">Fri</text>
          <text x="0" y="125" fill="#8b949e" font-size="9">Sun</text>

          <!-- Contribution Cells Container -->
          <g id="cellsGroup"></g>
        </svg>
      </div>
    </div>

    <!-- Controls Panel -->
    <div class="controls-panel">
      <div class="control-group">
        <button id="toggleBtn" class="btn primary">
          <span id="toggleIcon">&#x23F8;</span>
          <span id="toggleLabel">Pause Animation</span>
        </button>
        <button id="burstBtn" class="btn">&#x26A1; Instant Burst</button>
      </div>

      <div class="control-group range-group">
        <label for="densitySlider">Active Squares:</label>
        <input type="range" id="densitySlider" min="2" max="8" value="5" />
        <span id="densityVal" class="status-text">2&#x2013;5 sq</span>
      </div>

      <div class="control-group range-group">
        <label for="speedSelect">Speed:</label>
        <select id="speedSelect" class="btn" style="padding: 6px 12px;">
          <option value="fast" selected>Fast (150&#x2013;250ms)</option>
          <option value="ultra">Ultra (100&#x2013;180ms)</option>
          <option value="smooth">Smooth (250&#x2013;350ms)</option>
        </select>
      </div>

      <div class="status-text" id="engineStatus">Engine: RUNNING</div>
    </div>

    <footer>
      Auto-updated from live GitHub GraphQL API for @raviraj940 &bull; Continuous Random Animation Engine v2.0
    </footer>
  </div>

  <script>
    // Embedded real contribution cells
    const CELLS_DATA = {json.dumps(cells)};

    // Animation configuration
    const config = {{
      isRunning: true,
      minActive: 2,
      maxActive: 5,
      minDuration: 150,  // ms
      maxDuration: 280,  // ms
      minDelay: 60,      // ms
      maxDelay: 180,     // ms
      respectReducedMotion: true
    }};

    // DOM Elements
    const cellsGroup = document.getElementById('cellsGroup');
    const tooltip = document.getElementById('tooltip');
    const toggleBtn = document.getElementById('toggleBtn');
    const toggleIcon = document.getElementById('toggleIcon');
    const toggleLabel = document.getElementById('toggleLabel');
    const burstBtn = document.getElementById('burstBtn');
    const densitySlider = document.getElementById('densitySlider');
    const densityVal = document.getElementById('densityVal');
    const speedSelect = document.getElementById('speedSelect');
    const activeSquaresCount = document.getElementById('activeSquaresCount');
    const engineStatus = document.getElementById('engineStatus');

    const cellElements = [];
    const activeIndices = [];
    const currentActiveBlinks = new Set();
    let loopTimeoutId = null;

    // Check prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (prefersReducedMotion.matches && config.respectReducedMotion) {{
      config.isRunning = false;
      engineStatus.textContent = 'Engine: PAUSED (Reduced Motion)';
    }}

    // Render cells into SVG
    CELLS_DATA.forEach((c, idx) => {{
      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('x', c.x);
      rect.setAttribute('y', c.y - 12);
      rect.setAttribute('width', 11);
      rect.setAttribute('height', 11);
      rect.setAttribute('rx', 2);
      rect.setAttribute('fill', c.fill);
      rect.classList.add('cell');
      rect.dataset.index = idx;
      rect.dataset.baseFill = c.fill;
      rect.dataset.title = c.title;

      rect.addEventListener('mouseenter', (e) => {{
        tooltip.textContent = c.title || 'No contributions';
        tooltip.style.display = 'block';
        moveTooltip(e);
      }});
      rect.addEventListener('mousemove', moveTooltip);
      rect.addEventListener('mouseleave', () => {{
        tooltip.style.display = 'none';
      }});

      cellsGroup.appendChild(rect);
      cellElements.push(rect);

      if (c.fill !== '#161b22') {{
        activeIndices.push(idx);
      }}
    }});

    function moveTooltip(e) {{
      tooltip.style.left = (e.clientX + 10) + 'px';
      tooltip.style.top = (e.clientY + 15) + 'px';
    }}

    function randomInt(min, max) {{
      return Math.floor(Math.random() * (max - min + 1)) + min;
    }}

    const GLOW_LEVELS = ['blink-level-1', 'blink-level-2', 'blink-level-3', 'blink-level-4'];

    function blinkSquare(index, duration) {{
      const el = cellElements[index];
      if (!el || currentActiveBlinks.has(index)) return;

      currentActiveBlinks.add(index);
      updateActiveCounter();

      const glowClass = GLOW_LEVELS[randomInt(0, GLOW_LEVELS.length - 1)];
      el.classList.add(glowClass);

      setTimeout(() => {{
        el.classList.remove(glowClass);
        currentActiveBlinks.delete(index);
        updateActiveCounter();
      }}, duration);
    }}

    function triggerBurst() {{
      if (!config.isRunning) return;

      const numSquares = randomInt(config.minActive, config.maxActive);
      for (let i = 0; i < numSquares; i++) {{
        let chosenIdx;
        if (activeIndices.length > 0 && Math.random() < 0.7) {{
          chosenIdx = activeIndices[randomInt(0, activeIndices.length - 1)];
        }} else {{
          chosenIdx = randomInt(0, cellElements.length - 1);
        }}

        const duration = randomInt(config.minDuration, config.maxDuration);
        const stagger = randomInt(0, 80);
        setTimeout(() => {{
          blinkSquare(chosenIdx, duration);
        }}, stagger);
      }}
    }}

    function runAnimationLoop() {{
      if (!config.isRunning) return;

      triggerBurst();

      const nextDelay = randomInt(config.minDelay, config.maxDelay);
      loopTimeoutId = setTimeout(() => {{
        requestAnimationFrame(runAnimationLoop);
      }}, nextDelay);
    }}

    function updateActiveCounter() {{
      activeSquaresCount.textContent = currentActiveBlinks.size;
    }}

    function toggleAnimation() {{
      config.isRunning = !config.isRunning;
      if (config.isRunning) {{
        toggleIcon.textContent = '\\u23F8';
        toggleLabel.textContent = 'Pause Animation';
        toggleBtn.classList.add('primary');
        engineStatus.textContent = 'Engine: RUNNING';
        runAnimationLoop();
      }} else {{
        toggleIcon.textContent = '\\u25B6';
        toggleLabel.textContent = 'Resume Animation';
        toggleBtn.classList.remove('primary');
        engineStatus.textContent = 'Engine: PAUSED';
        clearTimeout(loopTimeoutId);
        cellElements.forEach(el => {{
          GLOW_LEVELS.forEach(cls => el.classList.remove(cls));
        }});
        currentActiveBlinks.clear();
        updateActiveCounter();
      }}
    }}

    toggleBtn.addEventListener('click', toggleAnimation);
    burstBtn.addEventListener('click', () => {{
      triggerBurst();
    }});

    densitySlider.addEventListener('input', (e) => {{
      const val = parseInt(e.target.value, 10);
      config.minActive = Math.max(2, val - 2);
      config.maxActive = val;
      densityVal.innerHTML = config.minActive + '&ndash;' + config.maxActive + ' sq';
    }});

    speedSelect.addEventListener('change', (e) => {{
      const val = e.target.value;
      if (val === 'ultra') {{
        config.minDuration = 100;
        config.maxDuration = 180;
        config.minDelay = 40;
        config.maxDelay = 120;
      }} else if (val === 'smooth') {{
        config.minDuration = 250;
        config.maxDuration = 360;
        config.minDelay = 120;
        config.maxDelay = 260;
      }} else {{
        config.minDuration = 150;
        config.maxDuration = 280;
        config.minDelay = 60;
        config.maxDelay = 180;
      }}
    }});

    document.addEventListener('visibilitychange', () => {{
      if (document.hidden) {{
        clearTimeout(loopTimeoutId);
      }} else if (config.isRunning) {{
        runAnimationLoop();
      }}
    }});

    window.addEventListener('beforeunload', () => {{
      clearTimeout(loopTimeoutId);
    }});

    if (config.isRunning) {{
      runAnimationLoop();
    }}
  </script>
</body>
</html>
"""

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Generated {OUT_PATH} successfully ({len(html):,} bytes)")
