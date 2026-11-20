#!/usr/bin/env python3
"""
Generate animated GIF and animated SVG for the GitHub Contribution Calendar.
Creates:
  - assets/charts/animated_calendar.gif (smooth fast random blinking animation)
  - assets/charts/animated_calendar.svg (SVG with embedded CSS keyframe animations)
"""

import os
import sys
import random
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEATMAP_PATH = os.path.join(ROOT_DIR, "assets", "charts", "heatmap.svg")
GIF_PATH = os.path.join(ROOT_DIR, "assets", "charts", "animated_calendar.gif")
SVG_PATH = os.path.join(ROOT_DIR, "assets", "charts", "animated_calendar.svg")

# Parse heatmap cells
def parse_heatmap():
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

# Generate Animated GIF using Pillow
def generate_gif(cells):
    W, H = 739, 171
    SCALE = 2  # 2x supersampling for crisp edges
    SW, SH = W * SCALE, H * SCALE
    CELL_SZ = 11 * SCALE
    CORNER_R = 2 * SCALE

    # Background color #0d1117
    BG_COLOR = (13, 17, 23)
    BORDER_COLOR = (48, 54, 61)

    # Color mapping
    HEX_TO_RGB = {
        '#161b22': (22, 27, 34),
        '#0e4429': (14, 68, 41),
        '#006d32': (0, 109, 50),
        '#26a641': (38, 166, 65),
        '#39d353': (57, 211, 83),
    }

    # Glowing colors for blinking states
    GLOW_COLORS = [
        (86, 255, 159),   # #56ff9f - vibrant bright green
        (0, 255, 136),    # #00ff88 - neon green
        (126, 231, 135),  # #7ee787 - light pastel green
        (57, 211, 83),    # #39d353 - rich green
    ]

    # Pre-render base background image
    base = Image.new('RGB', (SW, SH), BG_COLOR)
    draw_base = ImageDraw.Draw(base)

    # Card border
    draw_base.rounded_rectangle([0, 0, SW - 1, SH - 1], radius=16 * SCALE, outline=BORDER_COLOR, width=2)

    # Draw header text & labels (simple geometric fallback)
    try:
        font = ImageFont.truetype("arial.ttf", 12 * SCALE)
        font_sm = ImageFont.truetype("arial.ttf", 9 * SCALE)
    except Exception:
        font = ImageFont.load_default()
        font_sm = font

    draw_base.text((30 * SCALE, 20 * SCALE), "Contribution Calendar 2026", fill=(139, 148, 158), font=font)

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    m_cols = [0, 5, 9, 13, 17, 22, 26, 30, 35, 39, 44, 48]
    for m, c in zip(months, m_cols):
        mx = (30 + c * 13) * SCALE
        draw_base.text((mx, 38 * SCALE), m, fill=(139, 148, 158), font=font_sm)

    days_lbl = ["Mon", "Wed", "Fri", "Sun"]
    days_y = [52, 78, 104, 130]
    for d, dy in zip(days_lbl, days_y):
        draw_base.text((4 * SCALE, dy * SCALE), d, fill=(139, 148, 158), font=font_sm)

    # Precompute cell rectangles and base RGBs
    cell_info = []
    for c in cells:
        cx = int(c['x'] * SCALE)
        cy = int(c['y'] * SCALE)
        base_rgb = HEX_TO_RGB.get(c['fill'], (22, 27, 34))
        is_active = (c['fill'] != '#161b22')
        cell_info.append({
            'box': [cx, cy, cx + CELL_SZ, cy + CELL_SZ],
            'base_rgb': base_rgb,
            'is_active': is_active
        })

    # Animation configuration:
    # 28 frames, 180ms per frame
    # Each burst lasts 2-4 frames
    NUM_FRAMES = 28
    FRAME_DURATION_MS = 180

    random.seed(42)  # reproducible randomness
    all_indices = list(range(len(cell_info)))
    active_indices = [i for i, c in enumerate(cell_info) if c['is_active']]

    # Schedule blinks: list of {cell_idx, start_frame, duration, glow_color}
    blinks = []
    for frame in range(NUM_FRAMES):
        # With 80% probability, trigger 2-6 new blinks
        if random.random() < 0.85:
            num_blinks = random.randint(2, 6)
            for _ in range(num_blinks):
                # 65% chance pick from active cells, 35% chance pick from inactive cells
                if active_indices and random.random() < 0.65:
                    idx = random.choice(active_indices)
                else:
                    idx = random.choice(all_indices)
                dur = random.randint(2, 4)
                glow = random.choice(GLOW_COLORS)
                blinks.append({
                    'idx': idx,
                    'start': frame,
                    'dur': dur,
                    'glow': glow
                })

    frames = []
    for frame_idx in range(NUM_FRAMES):
        frame_img = base.copy()
        draw = ImageDraw.Draw(frame_img)

        # Determine active blinks on this frame
        active_blinks_map = {}
        for b in blinks:
            # Handle wrap-around for seamless looping
            rel = (frame_idx - b['start']) % NUM_FRAMES
            if 0 <= rel < b['dur']:
                # Compute progress [0 .. 1 .. 0] (smooth bell curve)
                progress = rel / b['dur']
                intensity = 1.0 - abs(progress - 0.5) * 2  # 0 at start/end, 1 at peak
                active_blinks_map[b['idx']] = (b['glow'], intensity)

        # Draw all cells
        for idx, ci in enumerate(cell_info):
            if idx in active_blinks_map:
                glow_color, intensity = active_blinks_map[idx]
                # Blend base_rgb with glow_color
                r = int(ci['base_rgb'][0] + (glow_color[0] - ci['base_rgb'][0]) * intensity)
                g = int(ci['base_rgb'][1] + (glow_color[1] - ci['base_rgb'][1]) * intensity)
                b = int(ci['base_rgb'][2] + (glow_color[2] - ci['base_rgb'][2]) * intensity)
                draw.rounded_rectangle(ci['box'], radius=CORNER_R, fill=(r, g, b))
                # Add outer glow halo on peak
                if intensity > 0.6:
                    halo_box = [ci['box'][0]-2, ci['box'][1]-2, ci['box'][2]+2, ci['box'][3]+2]
                    draw.rounded_rectangle(halo_box, radius=CORNER_R+1, outline=(57, 211, 83), width=1)
            else:
                draw.rounded_rectangle(ci['box'], radius=CORNER_R, fill=ci['base_rgb'])

        # Downsample for antialiased smoothness
        frame_res = frame_img.resize((W, H), Image.Resampling.LANCZOS)
        frames.append(frame_res)

    # Save as looping animated GIF
    frames[0].save(
        GIF_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        optimize=True
    )
    print(f"  ✔ Generated animated GIF: {GIF_PATH} ({os.path.getsize(GIF_PATH):,} bytes)")

# Generate Animated SVG with CSS Keyframes
def generate_svg(cells):
    W, H = 739, 171
    random.seed(940)

    # CSS Keyframes for fast, organic blinking
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    text { font-family: "Inter", "Segoe UI", system-ui, sans-serif; }
    
    @keyframes blinkA {
      0%, 100% { opacity: 1; fill-opacity: 1; }
      50% { fill: #56ff9f; opacity: 1; filter: drop-shadow(0 0 4px #00ff88); }
    }
    @keyframes blinkB {
      0%, 100% { opacity: 1; }
      50% { fill: #00ff88; filter: drop-shadow(0 0 5px #39d353); }
    }
    @keyframes blinkC {
      0%, 100% { opacity: 1; }
      40% { fill: #7ee787; filter: drop-shadow(0 0 3px #56ff9f); }
    }
    @keyframes blinkD {
      0%, 100% { opacity: 1; }
      60% { fill: #39d353; filter: drop-shadow(0 0 4px #00ff88); }
    }
    
    /* Random animation classes */
    .b1 { animation: blinkA 1.4s ease-in-out infinite 0.1s; }
    .b2 { animation: blinkB 1.8s ease-in-out infinite 0.5s; }
    .b3 { animation: blinkC 1.2s ease-in-out infinite 0.3s; }
    .b4 { animation: blinkD 2.0s ease-in-out infinite 0.8s; }
    .b5 { animation: blinkA 1.6s ease-in-out infinite 1.1s; }
    .b6 { animation: blinkB 2.2s ease-in-out infinite 0.4s; }
    .b7 { animation: blinkC 1.5s ease-in-out infinite 1.3s; }
    .b8 { animation: blinkD 1.9s ease-in-out infinite 0.7s; }
    .b9 { animation: blinkA 2.4s ease-in-out infinite 1.6s; }
    .b10 { animation: blinkB 1.7s ease-in-out infinite 1.0s; }
    .b11 { animation: blinkC 2.1s ease-in-out infinite 0.2s; }
    .b12 { animation: blinkD 1.3s ease-in-out infinite 0.9s; }

    @media (prefers-reduced-motion: reduce) {
      .b1, .b2, .b3, .b4, .b5, .b6, .b7, .b8, .b9, .b10, .b11, .b12 {
        animation: none !important;
      }
    }
    """

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <style>
{css}
    </style>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0d1117"/>
      <stop offset="100%" stop-color="#161b22"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#00C6FF"/>
      <stop offset="100%" stop-color="#0072FF"/>
    </linearGradient>
  </defs>
  <!-- Background -->
  <rect width="{W}" height="{H}" rx="16" fill="url(#bg)" stroke="#30363d" stroke-width="1.5"/>
  <text x="30" y="28" fill="#8b949e" font-size="13" font-weight="700">Contribution Calendar 2026 &#x2022; Live Activity</text>
  
  <!-- Pulse indicator -->
  <circle cx="{W-95}" cy="24" r="4" fill="#39d353">
    <animate attributeName="opacity" values="1;0.3;1" dur="1.2s" repeatCount="indefinite"/>
  </circle>
  <text x="{W-84}" y="28" fill="#39d353" font-size="11" font-weight="600">LIVE</text>

  <!-- Month labels -->
'''
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    m_cols = [0, 5, 9, 13, 17, 22, 26, 30, 35, 39, 44, 48]
    for m, c in zip(months, m_cols):
        mx = 30 + c * 13
        svg += f'  <text x="{mx}" y="44" fill="#8b949e" font-size="9">{m}</text>\n'

    # Day labels
    days_lbl = ["Mon", "Wed", "Fri", "Sun"]
    days_y = [59, 85, 111, 137]
    for d, dy in zip(days_lbl, days_y):
        svg += f'  <text x="0" y="{dy}" fill="#8b949e" font-size="9">{d}</text>\n'

    # Select ~35 random cells across calendar to carry blinking classes
    active_indices = [i for i, c in enumerate(cells) if c['fill'] != '#161b22']
    all_indices = list(range(len(cells)))
    
    # 25 active cells + 15 random inactive cells = 40 animating cells total
    animated_map = {}
    chosen_active = random.sample(active_indices, min(25, len(active_indices)))
    for idx in chosen_active:
        animated_map[idx] = f"b{random.randint(1, 12)}"
    
    inactive_candidates = [i for i in all_indices if i not in animated_map]
    chosen_inactive = random.sample(inactive_candidates, min(15, len(inactive_candidates)))
    for idx in chosen_inactive:
        animated_map[idx] = f"b{random.randint(1, 12)}"

    # Render cells
    for idx, c in enumerate(cells):
        cls_attr = f' class="{animated_map[idx]}"' if idx in animated_map else ''
        svg += f'  <rect x="{c["x"]}" y="{c["y"]}" width="11" height="11" rx="2" fill="{c["fill"]}"{cls_attr}><title>{c["title"]}</title></rect>\n'

    svg += '</svg>\n'

    with open(SVG_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"  ✔ Generated animated SVG: {SVG_PATH} ({os.path.getsize(SVG_PATH):,} bytes)")

def main():
    print("Generating animated contribution calendar assets...")
    cells = parse_heatmap()
    generate_gif(cells)
    generate_svg(cells)
    print("Done!")

if __name__ == "__main__":
    main()
