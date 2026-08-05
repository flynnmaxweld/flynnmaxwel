"""
Generate a customized, minimalist Swiss-style GitHub profile README.
Includes:
  1. Animated GitHub contribution heatmap generator (fetching live data from Jan 2026 to today)
  2. Editorial minimalist README.md layout with badges and a filling grid
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
DISPLAY_NAME = "Flynn Maxwel" # Set as requested
TITLE = config.get("title", "Fullstack Developer · AI Enthusiast")
SKILLS = config.get("skills", ["Python", "JavaScript", "React"])
SOCIALS = config.get("social_links", [])

# -----------------------------------------------------------------------------
# 1. Live Contribution Heatmap Graph SVG Generator (Scraping & Date Filtering)
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
    
    # Get total contributions from raw page to display
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
        
    raw_days = []
    for td in cells:
        dt = td.get("data-date")
        lvl = td.get("data-level")
        if dt and lvl is not None:
            raw_days.append({
                "date": dt,
                "level": int(lvl)
            })
            
    if not raw_days:
        print("No contribution records parsed. Skipping contributions graphic.")
        return False
        
    raw_days.sort(key=lambda x: x["date"])
    
    # Filter: Show from current year Jan 2026 to live
    # Find the index of the first day of 2026
    first_2026_idx = -1
    for idx, day in enumerate(raw_days):
        if day["date"] >= "2026-01-01":
            first_2026_idx = idx
            break
            
    if first_2026_idx == -1:
        # Fallback if no 2026 data yet
        print("No 2026 data found yet. Using all parsed days.")
        contribs = raw_days
    else:
        # To align grid rows to Sunday-Saturday, find the Sunday of that week (index must be multiple of 7)
        start_idx = (first_2026_idx // 7) * 7
        contribs = raw_days[start_idx:]
        
    if not contribs:
        contribs = raw_days
        
    # Re-calculate total contributions in this filtered range
    filtered_total = sum(c["level"] for c in contribs) # approximate level counts, or fetch total
    # Let's count days that have levels > 0 for a more accurate count
    # But since we don't have exact counts, we can show total contributions in the year 2026
    # Or just count the parsed counts:
    # Actually, we can fetch the exact count from the scraped page for the year 2026 or estimate.
    # Let's just calculate how many contributions are in 2026 by searching for cells >= 2026-01-01
    # and reading the tooltip counts if we parsed them.
    # Note: we scraped cells, but counts are tooltips. We can count the sum of cells levels as activity.
    # To keep it standard, let's say "Contributions since Jan 2026"
    
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
<text class="total" x="{LEFT}" y="{H-6}">Live contributions since Jan 2026</text>
</svg>'''

    out_path = os.path.join("assets", "contrib-heatmap.svg")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Successfully generated contributions heatmap: {out_path}")
    return True

# -----------------------------------------------------------------------------
# 2. Swiss/Editorial Minimalist README.md Generator (Badges & Grid Icons)
# -----------------------------------------------------------------------------
def generate_readme(has_contrib):
    md = []
    
    # Custom requested title
    md.append(f'# Flynn Maxwel &mdash; Vibecoder\n\n')
    
    # Editorial Bio sentence
    md.append('Designing, building, and automating intelligent applications from New Delhi, India.\n\n')
    
    md.append('---\n\n')
    
    # Center section for Contribution Heatmap
    if has_contrib:
        md.append('<div align="center">\n')
        md.append(f'<img src="./assets/contrib-heatmap.svg" width="860" alt="Flynn Maxwel\'s GitHub contributions" />\n')
        md.append('</div>\n\n')
        md.append('---\n\n')
        
    # Tech Stack & Skills with Icons
    md.append('### 🛠️ Tech Stack &amp; Skills\n\n')
    md.append('| Category | Technologies |\n')
    md.append('| :--- | :--- |\n')
    
    # Build clean shield icon badges
    langs = ' '.join([
        '![](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)',
        '![](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)',
        '![](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)'
    ])
    frameworks = ' '.join([
        '![](https://img.shields.io/badge/Next.js-black?style=flat-square&logo=next.js&logoColor=white)',
        '![](https://img.shields.io/badge/Node.js-339933?style=flat-square&logo=node.js&logoColor=white)'
    ])
    databases = ' '.join([
        '![](https://img.shields.io/badge/SQL-CC292B?style=flat-square&logo=sqlite&logoColor=white)',
        '![](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)'
    ])
    
    md.append(f'| **Languages &amp; Core** | {langs} |\n')
    md.append(f'| **Frameworks &amp; Web** | {frameworks} |\n')
    md.append(f'| **Databases &amp; Systems** | {databases} |\n\n')
    
    md.append('---\n\n')
    
    # /works index section with emojis
    md.append('### 📂 /works\n\n')
    portfolio_url = None
    for s in SOCIALS:
        if s.get("label") == "Portfolio":
            portfolio_url = s.get("url")
            
    if portfolio_url:
        md.append(f'- [**{portfolio_url.replace("https://", "").replace("http://", "")}**]({portfolio_url}) &mdash; Personal Space &amp; Portfolio\n')
    md.append(f'- [**github.com/{USERNAME}**](https://github.com/{USERNAME}) &mdash; Open Source Repositories &amp; Experiments\n\n')
    
    # /connect section with icons
    md.append('### 🔗 /connect\n\n')
    connects = []
    for s in SOCIALS:
        label = s.get("label", "Link")
        url = s.get("url", "#")
        logo = s.get("logo", "").lower()
        color = s.get("color", "0d1117")
        
        logo_param = f"&logo={logo}" if logo else ""
        badge = f'[![{label}](https://img.shields.io/badge/{label}-{color}?style=flat-square{logo_param}&logoColor=white)]({url})'
        connects.append(badge)
        
    md.append(" &nbsp; ".join(connects))
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
