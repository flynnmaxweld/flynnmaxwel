"""
Generate a customized, terminal-styled GitHub profile README.
Includes:
  1. 3D ASCII wordmark SVG generator (retained but optional/separate)
  2. VS Code IDE mockup generator (replacing portrait/wordmark layout)
  3. Animated GitHub contribution heatmap generator (fetching live data via scraping)
  4. Tailored terminal-styled README.md
  5. GitHub Actions workflow to auto-refresh the profile daily
"""
import os
import json
import html
import math
import urllib.request
import re
import datetime
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

# Make sure folders exist
os.makedirs("assets", exist_ok=True)
os.makedirs(os.path.join(".github", "workflows"), exist_ok=True)

# Load configuration
CONFIG_PATH = "profile_config.json"
if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"Configuration file {CONFIG_PATH} not found.")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

# Profile Info
USERNAME = config.get("github_username", "username")
DISPLAY_NAME = config.get("display_name", "YOUR NAME")
TITLE = config.get("title", "Fullstack Developer · AI Enthusiast")
PHOTO_PATH = config.get("photo_path", "avatar.png")
SKILLS = config.get("skills", ["Python", "JavaScript", "React"])
SOCIALS = config.get("social_links", [])

# Colors
BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"
CURSOR = "#c9d1d9"

# -----------------------------------------------------------------------------
# 1. VS Code IDE Mockup SVG Generator
# -----------------------------------------------------------------------------
def generate_ide_mockup():
    canvas_w = 860
    canvas_h = 360
    sidebar_w = 190
    titlebar_h = 32
    tabbar_h = 30
    terminal_h = 95
    
    # Calculate code region
    editor_x = sidebar_w + 20
    editor_y_start = titlebar_h + tabbar_h + 15
    line_h = 17
    
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        # Background window
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="10" fill="{BG}" />',
        f'<rect x="0.5" y="0.5" width="{canvas_w-1}" height="{canvas_h-1}" rx="10" fill="none" stroke="{FRAME}" stroke-width="1"/>',
        
        # Titlebar
        f'<rect width="{canvas_w}" height="{titlebar_h}" rx="10" fill="#161b22"/>',
        f'<line x1="0" y1="{titlebar_h}" x2="{canvas_w}" y2="{titlebar_h}" stroke="{FRAME}"/>',
        
        # Window controls
        f'<circle cx="16" cy="16" r="4.5" fill="#ff5f56"/>',
        f'<circle cx="30" cy="16" r="4.5" fill="#ffbd2e"/>',
        f'<circle cx="44" cy="16" r="4.5" fill="#27c93f"/>',
        
        # Title text
        f'<text x="{canvas_w/2}" y="20" fill="{TITLE_TEXT}" font-size="11" text-anchor="middle">about_me.py - flynnmaxweld - VS Code</text>',
        
        # Sidebar
        f'<rect x="0" y="{titlebar_h}" width="{sidebar_w}" height="{canvas_h-titlebar_h}" fill="#111722" rx="0"/>',
        f'<line x1="{sidebar_w}" y1="{titlebar_h}" x2="{sidebar_w}" y2="{canvas_h}" stroke="{FRAME}"/>',
        
        # Sidebar Content
        f'<text x="15" y="{titlebar_h + 20}" fill="{TITLE_TEXT}" font-size="10" font-weight="bold" letter-spacing="0.5">EXPLORER: FLYNN</text>',
        # Folder - projects
        f'<text x="15" y="{titlebar_h + 42}" fill="#58a6ff" font-size="11">▼ <tspan fill="{INK}">projects</tspan></text>',
        f'<text x="30" y="{titlebar_h + 60}" fill="{TITLE_TEXT}" font-size="11">📄 <tspan fill="{INK}" font-weight="bold">about_me.py</tspan></text>',
        f'<text x="30" y="{titlebar_h + 78}" fill="{TITLE_TEXT}" font-size="11">📄 <tspan fill="{TITLE_TEXT}">skills.json</tspan></text>',
        f'<text x="30" y="{titlebar_h + 96}" fill="{TITLE_TEXT}" font-size="11">📄 <tspan fill="{TITLE_TEXT}">config.json</tspan></text>',
        # Folder - assets
        f'<text x="15" y="{titlebar_h + 120}" fill="#58a6ff" font-size="11">▶ <tspan fill="{TITLE_TEXT}">assets</tspan></text>',
        
        # Editor Tab bar
        f'<rect x="{sidebar_w}" y="{titlebar_h}" width="{canvas_w-sidebar_w}" height="{tabbar_h}" fill="#161b22"/>',
        f'<line x1="{sidebar_w}" y1="{titlebar_h+tabbar_h}" x2="{canvas_w}" y2="{titlebar_h+tabbar_h}" stroke="{FRAME}"/>',
        
        # Active Tab (about_me.py)
        f'<rect x="{sidebar_w}" y="{titlebar_h}" width="125" height="{tabbar_h}" fill="{BG}"/>',
        f'<line x1="{sidebar_w+125}" y1="{titlebar_h}" x2="{sidebar_w+125}" y2="{titlebar_h+tabbar_h}" stroke="{FRAME}"/>',
        f'<text x="{sidebar_w + 15}" y="{titlebar_h + 18}" fill="{INK}" font-size="11">🐍 about_me.py</text>',
        f'<text x="{sidebar_w + 105}" y="{titlebar_h + 18}" fill="{TITLE_TEXT}" font-size="10">×</text>',
        
        # Inactive Tab (skills.json)
        f'<rect x="{sidebar_w+125}" y="{titlebar_h}" width="110" height="{tabbar_h}" fill="#111722"/>',
        f'<line x1="{sidebar_w+235}" y1="{titlebar_h}" x2="{sidebar_w+235}" y2="{titlebar_h+tabbar_h}" stroke="{FRAME}"/>',
        f'<text x="{sidebar_w + 138}" y="{titlebar_h + 18}" fill="{TITLE_TEXT}" font-size="11">📄 skills.json</text>',
    ]
    
    # Line Numbers & Editor Code
    code_lines = [
        ('<tspan fill="#6a9955"># profile configuration</tspan>', 1),
        ('<tspan fill="#c586c0">from</tspan> developer <tspan fill="#c586c0">import</tspan> <tspan fill="#4ec9b0">FullstackDev</tspan>', 2),
        ('', 3),
        (f'<tspan fill="#c586c0">class</tspan> <tspan fill="#4ec9b0">FlynnMaxwelD</tspan>(<tspan fill="#4ec9b0">FullstackDev</tspan>):', 4),
        (f'    <tspan fill="#c586c0">def</tspan> <tspan fill="#dcdcaa">__init__</tspan>(<tspan fill="#9cdcfe">self</tspan>):', 5),
        (f'        <tspan fill="#9cdcfe">self</tspan>.role = <tspan fill="#ce9178">"Fullstack Developer &amp; AI Builder"</tspan>', 6),
        (f'        <tspan fill="#9cdcfe">self</tspan>.location = <tspan fill="#ce9178">"New Delhi, India"</tspan>', 7),
        (f'        <tspan fill="#9cdcfe">self</tspan>.status = <tspan fill="#ce9178">"Building agentic systems..."</tspan>', 8),
        (f'        <tspan fill="#9cdcfe">self</tspan>.open_to_collab = <tspan fill="#569cd6">True</tspan>', 9),
        (f'    <tspan fill="#c586c0">def</tspan> <tspan fill="#dcdcaa">get_stack</tspan>(<tspan fill="#9cdcfe">self</tspan>):', 10),
        (f'        <tspan fill="#c586c0">return</tspan> [<tspan fill="#ce9178">"Python"</tspan>, <tspan fill="#ce9178">"React"</tspan>, <tspan fill="#ce9178">"Next.js"</tspan>, <tspan fill="#ce9178">"SQL"</tspan>]', 11)
    ]
    
    # Render lines
    for code, line_num in code_lines:
        y = editor_y_start + (line_num - 1) * line_h
        # Draw Line Number
        svg.append(f'<text x="{sidebar_w + 12}" y="{y}" fill="#5c6370" font-size="11" text-anchor="end">{line_num}</text>')
        # Draw Code Content
        if code:
            svg.append(f'<text x="{editor_x}" y="{y}" fill="{INK}" font-size="11" xml:space="preserve">{code}</text>')
            
    # Bottom Terminal Separator
    terminal_y = canvas_h - terminal_h
    svg.append(f'<line x1="{sidebar_w}" y1="{terminal_y}" x2="{canvas_w}" y2="{terminal_y}" stroke="{FRAME}" />')
    
    # Terminal Titlebar
    terminal_bar_h = 22
    svg.append(f'<rect x="{sidebar_w}" y="{terminal_y}" width="{canvas_w-sidebar_w}" height="{terminal_bar_h}" fill="#161b22" />')
    svg.append(f'<text x="{sidebar_w + 15}" y="{terminal_y + 15}" fill="{INK}" font-size="10" font-weight="bold">TERMINAL</text>')
    svg.append(f'<text x="{sidebar_w + 90}" y="{terminal_y + 15}" fill="{TITLE_TEXT}" font-size="10">PROBLEMS</text>')
    svg.append(f'<text x="{sidebar_w + 160}" y="{terminal_y + 15}" fill="{TITLE_TEXT}" font-size="10">OUTPUT</text>')
    
    # Terminal Content
    term_x = sidebar_w + 15
    term_y_start = terminal_y + terminal_bar_h + 18
    
    svg.append(f'<text x="{term_x}" y="{term_y_start}" fill="{INK}" font-size="11" xml:space="preserve">'
               f'<tspan fill="#50fa7b">flynnmaxweld@github</tspan>:<tspan fill="#8be9fd">~$</tspan> pytest test_profile.py'
               f'</text>')
    # Blinking cursor block
    cursor_x = sidebar_w + 372
    svg.append(f'<rect x="{cursor_x}" y="{term_y_start - 10}" width="7" height="12" fill="{INK}">'
               f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite" />'
               f'</rect>')
               
    svg.append(f'<text x="{term_x}" y="{term_y_start + 18}" fill="{TITLE_TEXT}" font-size="11">====================== 5 passed in 0.08s ======================</text>')
    svg.append(f'<text x="{term_x}" y="{term_y_start + 36}" fill="#50fa7b" font-size="11">status: ACTIVE (Ready to compile)</text>')
    
    svg.append("</svg>")
    
    out_path = os.path.join("assets", "ide-mockup.svg")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("".join(svg))
    print(f"Successfully generated IDE mockup: {out_path}")
    return True

# -----------------------------------------------------------------------------
# 2. Animated GitHub Streak / Contributions Heatmap Generator
# -----------------------------------------------------------------------------
def generate_contributions():
    url = f"https://github.com/users/{USERNAME}/contributions"
    print(f"Fetching contribution data from: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=25) as r:
            html_text = r.read().decode("utf-8")
    except Exception as e:
        print(f"Error fetching contributions: {e}. Skipping contributions graphic.")
        return False

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("BeautifulSoup (bs4) library is required to scrape contributions. Skipping contributions graphic.")
        return False
        
    soup = BeautifulSoup(html_text, "html.parser")
    
    # Get total contributions
    h2 = soup.find("h2", class_=lambda c: c and "f4" in c and "text-normal" in c)
    if not h2:
        h2 = soup.find(id="js-contribution-activity-description")
    
    total = 0
    if h2:
        txt = h2.get_text(strip=True)
        m = re.search(r"([\d,]+)\s+contribution", txt)
        if m:
            total = int(m.group(1).replace(",", ""))
            
    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        print("No contribution cells found in scraped page. Skipping contributions graphic.")
        return False
        
    contribs = []
    for td in cells:
        dt = td.get("data-date")
        lvl = td.get("data-level")
        if dt and lvl is not None:
            contribs.append({
                "date": dt,
                "level": int(lvl)
            })
            
    if not contribs:
        print("No contribution records parsed. Skipping contributions graphic.")
        return False
        
    # Sort contributions by date
    contribs.sort(key=lambda x: x["date"])
    
    CELL, GAP, RAD, LEFT, TOP = 13, 3, 2.5, 34, 24
    COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    GRAY = "#7d8590"
    MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    
    n = len(contribs)
    NW = (n + 6) // 7
    W = LEFT + NW * (CELL + GAP) + 6
    H = TOP + 7 * (CELL + GAP) + 22
    
    REVEAL, DUR = 3.6, 0.55
    maxorder = (NW - 1) + 6 * 0.55
    
    rects, labels = [], []
    sd = datetime.date.fromisoformat(contribs[0]["date"])
    last_m = None
    
    for wk in range(NW):
        d = sd + datetime.timedelta(days=wk * 7)
        if d.month != last_m:
            last_m = d.month
            labels.append(f'<text class="lbl" x="{LEFT+wk*(CELL+GAP)}" y="{TOP-8}">{MONTHS[d.month-1]}</text>')
            
    for name, r in [("Mon", 1), ("Wed", 3), ("Fri", 5)]:
        labels.append(f'<text class="lbl" x="2" y="{TOP+r*(CELL+GAP)+CELL-2}">{name}</text>')
        
    for i, c in enumerate(contribs):
        wk, row, lvl = i // 7, i % 7, c["level"]
        x = LEFT + wk * (CELL + GAP)
        y = TOP + row * (CELL + GAP)
        delay = round((wk + row * 0.55) / maxorder * REVEAL, 3)
        cls = "c g" if lvl >= 1 else "c e"
        rects.append(
            f'<rect class="{cls}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{RAD}" '
            f'fill="{COLORS[lvl]}" style="animation-delay:{delay}s"/>'
        )
        
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">
<style>
  text.lbl {{ fill:{GRAY}; font-size:13px; font-weight:600; }}
  text.total {{ fill:#e6edf3; font-size:15px; font-weight:700; }}
  .c {{ transform-box:fill-box; transform-origin:center; opacity:0; animation:pop {DUR}s ease-out both; }}
  .g {{ animation:pop {DUR}s ease-out both, flash {DUR+0.15}s ease-out both; }}
  @keyframes pop {{ 0%{{opacity:0;transform:scale(.2)}} 60%{{opacity:1;transform:scale(1.1)}} 100%{{opacity:1;transform:scale(1)}} }}
  @keyframes flash {{ 0%{{filter:brightness(2.4)}} 45%{{filter:brightness(2.4)}} 100%{{filter:brightness(1)}} }}
  @media (prefers-reduced-motion: reduce) {{ .c {{ opacity:1 !important; animation:none !important; }} }}
</style>
<rect width="{W}" height="{H}" fill="none"/>
{"".join(labels)}
{"".join(rects)}
<text class="total" x="{LEFT}" y="{H-6}">{total:,} contributions in the last year</text>
</svg>'''

    out_path = os.path.join("assets", "contrib-heatmap.svg")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Successfully generated contributions heatmap: {out_path}")
    return True

# -----------------------------------------------------------------------------
# 3. README.md Generator
# -----------------------------------------------------------------------------
def generate_readme(has_ide, has_contrib):
    md = []
    md.append('<div align="center">\n\n')
    
    # 1. Whoami / Terminal IDE Mockup Header section
    md.append(f'<h3><code>{USERNAME}@github ~ $ whoami</code></h3>\n\n')
    if has_ide:
        md.append(f'<img src="./assets/ide-mockup.svg" width="860" alt="{DISPLAY_NAME} — IDE Mockup" />\n\n')
    else:
        md.append(f'<h2>{DISPLAY_NAME}</h2>\n<p>{TITLE}</p>\n\n')
        
    md.append('<br>\n<br>\n\n')
    
    # 2. Contributions Heatmap
    if has_contrib:
        md.append(f'<h3><code>{USERNAME}@github ~ $ ./contributions.sh</code></h3>\n\n')
        md.append(f'<img src="./assets/contrib-heatmap.svg" width="860" alt="{DISPLAY_NAME}\'s GitHub contribution graph — auto-refreshed daily" />\n\n')
        md.append('<br>\n<br>\n\n')
        
    # 2.5. GitHub Stats Cards
    md.append(f'<h3><code>{USERNAME}@github ~ $ ./stats.sh</code></h3>\n\n')
    md.append('<p align="center">\n')
    md.append(f'  <img src="https://github-readme-stats.vercel.app/api?username={USERNAME}&show_icons=true&bg_color=0d1117&border_color=30363d&title_color=7d8590&text_color=c9d1d9&icon_color=58a6ff" alt="{DISPLAY_NAME}\'s GitHub Stats" />\n')
    md.append('  &nbsp;&nbsp;\n')
    md.append(f'  <img src="https://github-readme-stats.vercel.app/api/top-langs/?username={USERNAME}&layout=compact&bg_color=0d1117&border_color=30363d&title_color=7d8590&text_color=c9d1d9&icon_color=58a6ff" alt="{DISPLAY_NAME}\'s Top Languages" />\n')
    md.append('</p>\n\n')
    md.append('<br>\n<br>\n\n')
        
    # 3. Skills Section
    md.append(f'<h3><code>{USERNAME}@github ~ $ ./skills.sh</code></h3>\n\n')
    md.append(f'<p><b>{TITLE}</b></p>\n\n')
    
    skills_html = []
    for skill in SKILLS:
        skill_clean = skill.replace(" ", "%20").replace("-", "--")
        skills_html.append(f'<img src="https://img.shields.io/badge/{skill_clean}-0d1117?style=flat-square&logoColor=white" alt="{skill}" />')
    md.append(" &nbsp; ".join(skills_html))
    md.append('\n\n<br>\n<br>\n\n')
    
    # 4. Links / Contact Section
    md.append(f'<h3><code>{USERNAME}@github ~ $ ./links.sh</code></h3>\n\n')
    
    socials_html = []
    for social in SOCIALS:
        label = social.get("label", "Link")
        val = social.get("value", "link")
        url = social.get("url", "#")
        color = social.get("color", "0d1117")
        logo = social.get("logo", "")
        
        logo_query = f"&logo={logo}" if logo else ""
        badge_img = f"https://img.shields.io/badge/{label}-{val}-{color}?style=for-the-badge{logo_query}&logoColor=white"
        socials_html.append(f'[![{label}]({badge_img})]({url})')
        
    md.append("\n".join(socials_html))
    md.append('\n\n<br>\n')
    md.append('</div>\n')
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.writelines(md)
    print("Successfully generated README.md")

# -----------------------------------------------------------------------------
# 4. Generate GitHub Action Workflow
# -----------------------------------------------------------------------------
def generate_workflow():
    workflow_yaml = f'''name: Update Profile Art

# Refreshes the contribution graph SVG daily from real data.
# Runs daily, plus whenever you push to main, plus on-demand.

on:
  schedule:
    - cron: "17 6 * * *"   # ~06:17 UTC every day
  workflow_dispatch: {{}}
  push:
    branches: [main]

permissions:
  contents: write

jobs:
  refresh-profile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install pillow numpy beautifulsoup4 requests

      - name: Render dynamic assets
        run: python make_profile.py

      - name: Commit updated art
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: refresh profile art [skip ci]"
          file_pattern: "assets/contrib-heatmap.svg assets/ide-mockup.svg README.md"
'''
    workflow_path = os.path.join(".github", "workflows", "update-profile-art.yml")
    with open(workflow_path, "w", encoding="utf-8") as f:
        f.write(workflow_yaml)
    print(f"Successfully generated GitHub Action Workflow: {workflow_path}")

# -----------------------------------------------------------------------------
# Main Execution Flow
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("="*60)
    print("Generating Terminal-Style GitHub Profile README...")
    print("="*60)
    
    has_ide = generate_ide_mockup()
    has_contrib = generate_contributions()
    
    generate_readme(has_ide, has_contrib)
    generate_workflow()
    
    print("="*60)
    print("Done! You can commit the files in 'assets/', '.github/' and 'README.md'")
    print("to your personal GitHub profile repository.")
    print("="*60)
