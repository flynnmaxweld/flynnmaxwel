"""
Generate a customized, ultra-minimalist Swiss-style GitHub profile README.
Includes:
  1. Animated GitHub contribution heatmap generator (fetching live data via scraping)
  2. Editorial minimalist README.md layout
  3. GitHub Actions workflow to auto-refresh the profile daily
"""
import os
import json
import urllib.request
import re
import datetime

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
SKILLS = config.get("skills", ["Python", "JavaScript", "React"])
SOCIALS = config.get("social_links", [])

# -----------------------------------------------------------------------------
# 1. Live Contribution Heatmap Graph SVG Generator (Scraping)
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
# 2. Swiss/Editorial Minimalist README.md Generator
# -----------------------------------------------------------------------------
def generate_readme(has_contrib):
    md = []
    
    # Header Signature
    md.append(f'# {DISPLAY_NAME} &mdash; Fullstack &amp; AI Builder\n\n')
    
    # Editorial Bio sentence
    md.append('Designing, building, and automating intelligent applications from New Delhi, India.\n\n')
    
    # Minimalist inline dot-separated tech stack
    stack_line = " &middot; ".join(SKILLS)
    md.append(f'`{stack_line}`\n\n')
    
    md.append('---\n\n')
    
    # Center section for Contribution Heatmap
    if has_contrib:
        md.append('<div align="center">\n')
        md.append(f'<img src="./assets/contrib-heatmap.svg" width="860" alt="{DISPLAY_NAME}\'s GitHub contributions" />\n')
        md.append('</div>\n\n')
        md.append('---\n\n')
        
    # /works index section
    md.append('### /works\n\n')
    # Loop through social portfolio if available or generate default clean links
    portfolio_url = None
    for s in SOCIALS:
        if s.get("label") == "Portfolio":
            portfolio_url = s.get("url")
            
    if portfolio_url:
        md.append(f'- [{portfolio_url.replace("https://", "").replace("http://", "")}]({portfolio_url}) &mdash; Personal Space\n')
    md.append(f'- [github.com/{USERNAME}](https://github.com/{USERNAME}) &mdash; Open Source Repositories\n\n')
    
    # /connect section
    md.append('### /connect\n\n')
    connects = []
    for s in SOCIALS:
        label = s.get("label", "Link")
        url = s.get("url", "#")
        connects.append(f'[{label}]({url})')
    md.append(" &nbsp;/&nbsp; ".join(connects))
    md.append('\n')
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.writelines(md)
    print("Successfully generated README.md")

# -----------------------------------------------------------------------------
# 3. Generate GitHub Action Workflow
# -----------------------------------------------------------------------------
def generate_workflow():
    workflow_yaml = f'''name: Update Profile Art

# Refreshes the contribution graph SVG daily from real data.
# Runs daily, plus on-demand.

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
          file_pattern: "assets/contrib-heatmap.svg README.md"
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
    print("Generating Editorial Minimalist GitHub Profile README...")
    print("="*60)
    
    has_contrib = generate_contributions()
    generate_readme(has_contrib)
    generate_workflow()
    
    print("="*60)
    print("Done! You can commit the files in 'assets/', '.github/' and 'README.md'")
    print("to your personal GitHub profile repository.")
    print("="*60)
