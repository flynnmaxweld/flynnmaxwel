"""
Generate a customized, terminal-styled GitHub profile README.
Includes:
  1. 3D ASCII wordmark SVG generator (adapted from Avi Vashishta's design)
  2. Monochrome typing-in ASCII portrait SVG generator from any image (Pillow + NumPy)
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

# Wordmark config
WORDMARK_TEXT = config.get("wordmark_text", DISPLAY_NAME.split()[0].upper()[:5])

# Colors
BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"
CURSOR = "#c9d1d9"

# Find a valid font for the wordmark
WINDOWS_FONTS = [
    "C:\\Windows\\Fonts\\arialbd.ttf",   # Arial Bold
    "C:\\Windows\\Fonts\\impact.ttf",    # Impact
    "C:\\Windows\\Fonts\\consolab.ttf",  # Consolas Bold
    "C:\\Windows\\Fonts\\segoeuib.ttf",  # Segoe UI Bold
]
WORDMARK_FONT_PATH = None
for fp in WINDOWS_FONTS:
    if os.path.exists(fp):
        WORDMARK_FONT_PATH = fp
        break

if not WORDMARK_FONT_PATH:
    print("Warning: Common Windows bold fonts not found. Wordmark generation will fallback.")

# -----------------------------------------------------------------------------
# 1. 3D ASCII Wordmark Generator
# -----------------------------------------------------------------------------
def generate_wordmark():
    if not WORDMARK_FONT_PATH:
        print("Skipping 3D ASCII wordmark due to lack of bold TrueType font.")
        return False
        
    COLS = 50
    ROW_MARGIN = 5
    CELL_W = 9.0
    CELL_H = 15.5
    
    MASK_H = 300
    TRACKING = 0.14
    DEPTH_FRAC = 0.34
    TILT_DEG = 4.0
    CAM_DIST = 6.0
    FOCAL = 4.15
    FIT = 0.92
    
    RAMP = " .`:-=+*csS#%@"
    LIGHT = np.array([-0.15, -0.45, -1.00])
    LIGHT = LIGHT / np.linalg.norm(LIGHT)
    AMBIENT = 0.22
    FOG = 0.34
    FOG_SPAN = 0.55
    
    PAD = 18
    TITLEBAR_H = 28
    
    # Render text mask
    font_size = MASK_H
    font = ImageFont.truetype(WORDMARK_FONT_PATH, font_size)
    l, t, r, b = font.getbbox(WORDMARK_TEXT)
    h = b - t
    track = int(round(TRACKING * font_size))
    
    def line_w(s):
        return sum(font.getlength(c) for c in s) + track * (len(s) - 1)
        
    total_w = int(round(line_w(WORDMARK_TEXT))) + 8
    total_h = h + 8
    img = Image.new("L", (total_w, total_h), 0)
    d = ImageDraw.Draw(img)
    pen = 4.0 + (total_w - 8 - line_w(WORDMARK_TEXT)) / 2.0
    base = -t + 4
    for ch in WORDMARK_TEXT:
        d.text((pen, base), ch, font=font, fill=255)
        pen += font.getlength(ch) + track
        
    mask = np.array(img) > 127
    xs_any = np.nonzero(mask.any(0))[0]
    ys_any = np.nonzero(mask.any(1))[0]
    if len(xs_any) == 0 or len(ys_any) == 0:
        print("Empty text mask generated.")
        return False
        
    mask = mask[ys_any[0]:ys_any[-1] + 1, xs_any[0]:xs_any[-1] + 1]
    H, W = mask.shape
    depth = max(4, int(round(H * DEPTH_FRAC)))
    cy, cx = np.nonzero(mask)
    
    pts, nrm = [], []
    
    # Caps
    front = np.stack([cx, cy, np.full_like(cx, -0.6, dtype=float)], 1)
    pts.append(front)
    nrm.append(np.tile([0.0, 0.0, -1.0], (len(front), 1)))
    
    back = np.stack([cx, cy, np.full_like(cx, depth)], 1).astype(float)
    pts.append(back)
    nrm.append(np.tile([0.0, 0.0, 1.0], (len(back), 1)))
    
    # Side walls
    pad = np.pad(mask, 1)
    empty_r = ~pad[1:-1, 2:]
    empty_l = ~pad[1:-1, :-2]
    empty_d = ~pad[2:, 1:-1]
    empty_u = ~pad[:-2, 1:-1]
    edge = mask & (empty_r | empty_l | empty_d | empty_u)
    ey, ex = np.nonzero(edge)
    nx = empty_r[ey, ex].astype(float) - empty_l[ey, ex].astype(float)
    ny = empty_d[ey, ex].astype(float) - empty_u[ey, ex].astype(float)
    ln = np.sqrt(nx * nx + ny * ny)
    ln[ln == 0] = 1.0
    nx, ny = nx / ln, ny / ln
    
    zsteps = np.linspace(0, depth, max(3, depth // 2))
    for z in zsteps:
        pts.append(np.stack([ex, ey, np.full_like(ex, z, dtype=float)], 1))
        nrm.append(np.stack([nx, ny, np.zeros_like(nx)], 1))
        
    P = np.concatenate(pts).astype(np.float32)
    N = np.concatenate(nrm).astype(np.float32)
    
    P[:, 0] -= W / 2.0
    P[:, 1] -= H / 2.0
    P[:, 2] -= depth / 2.0
    P /= float(W)
    
    def rot_y(a):
        c, s = math.cos(a), math.sin(a)
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float32)
        
    def rot_x(a):
        c, s = math.cos(a), math.sin(a)
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float32)
        
    def project(P, N, yaw):
        M = rot_x(math.radians(TILT_DEG)) @ rot_y(yaw)
        p = P @ M.T
        n = N @ M.T
        vis = n[:, 2] < 0.0
        p, n = p[vis], n[vis]
        z = p[:, 2] + CAM_DIST
        f = FOCAL / z
        lam = n @ LIGHT
        inten = AMBIENT + (1.0 - AMBIENT) * np.clip(lam, 0, 1)
        t = np.clip((z - CAM_DIST) / FOG_SPAN, -1.0, 1.0)
        inten *= 1.0 - FOG * (t + 1.0) / 2.0
        idx = np.clip((inten * (len(RAMP) - 1)).round().astype(int), 1, len(RAMP) - 1)
        return p[:, 0] * f, p[:, 1] * f, z, idx
        
    # Rock animation angles
    nf = 20
    rest = math.radians(-13)
    amp = math.radians(11)
    yaws = [rest + amp * math.sin(2 * math.pi * i / nf) for i in range(nf)]
    
    proj = [project(P, N, y) for y in yaws]
    
    # Fit sizing
    xs = np.concatenate([q[0] for q in proj])
    ys = np.concatenate([q[1] for q in proj])
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    ar = CELL_W / CELL_H
    scale = FIT * (COLS - 1) / (x1 - x0)
    ROWS = int(math.ceil((y1 - y0) * ar * scale)) + 1 + 2 * ROW_MARGIN
    cx = (COLS - 1) / 2.0 - (x0 + x1) / 2.0 * scale
    cy = (ROWS - 1) / 2.0 - (y0 + y1) / 2.0 * scale * ar
    
    def rasterize(q):
        x, y, z, idx = q
        col = np.round(cx + x * scale).astype(int)
        row = np.round(cy + y * scale * ar).astype(int)
        ok = (col >= 0) & (col < COLS) & (row >= 0) & (row < ROWS)
        col, row, z, idx = col[ok], row[ok], z[ok], idx[ok]
        grid = np.zeros((ROWS, COLS), np.int8)
        order = np.argsort(-z)
        grid[row[order], col[order]] = idx[order]
        return ["".join(RAMP[i] for i in r) for r in grid]
        
    frames = [rasterize(q) for q in proj]
    
    # Emit SVG
    art_w = COLS * CELL_W
    art_h = ROWS * CELL_H
    canvas_w = art_w + PAD * 2
    canvas_h = TITLEBAR_H + art_h + PAD
    art_top = TITLEBAR_H + PAD * 0.3
    fs = CELL_H * 0.92
    
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w:.0f}" height="{canvas_h:.0f}" '
        f'viewBox="0 0 {canvas_w:.0f} {canvas_h:.0f}" font-family="ui-monospace, SFMono-Regular, '
        f'Menlo, Consolas, monospace">',
        '<defs><linearGradient id="wbg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
        '</linearGradient></defs>',
        f'<rect width="{canvas_w:.0f}" height="{canvas_h:.0f}" rx="12" fill="url(#wbg)"/>',
        f'<rect x="0.5" y="0.5" width="{canvas_w-1:.0f}" height="{canvas_h-1:.0f}" rx="12" '
        f'fill="none" stroke="{FRAME}" stroke-width="1"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w:.0f}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{PAD + i*15}" cy="{TITLEBAR_H/2}" r="4.5" fill="{dot}"/>')
    p.append(f'<text x="{canvas_w/2:.0f}" y="{TITLEBAR_H/2 + 4:.0f}" fill="{TITLE_TEXT}" '
             f'font-size="11.5" text-anchor="middle">{USERNAME}@github: ~$ ./wordmark.sh --3d</text>')
             
    def frame_g(rows, extra=""):
        out_rows = []
        for ry, line in enumerate(rows):
            s = line.rstrip()
            if not s.strip():
                continue
            lead = len(s) - len(s.lstrip(" "))
            body = s[lead:]
            x = PAD + lead * CELL_W
            y = art_top + ry * CELL_H + CELL_H * 0.78
            out_rows.append(
                f'<text xml:space="preserve" x="{x:.1f}" y="{y:.1f}" font-size="{fs:.1f}" '
                f'textLength="{len(body)*CELL_W:.1f}" lengthAdjust="spacing">{html.escape(body)}</text>'
            )
        return f'<g fill="{INK}"{extra}>' + "".join(out_rows) + "</g>"
        
    # Intro wipe animation
    reveal = 1.6
    dur = 5.0
    p.append(f'<clipPath id="wipe"><rect x="{PAD}" y="{art_top:.1f}" height="{art_h:.1f}" width="0">'
             f'<animate attributeName="width" from="0" to="{art_w:.0f}" begin="0s" '
             f'dur="{reveal:.2f}s" fill="freeze"/></clipPath>')
    p.append(f'<g clip-path="url(#wipe)">{frame_g(frames[0])}'
             f'<set attributeName="opacity" to="0" begin="{reveal:.2f}s"/></g>')
    p.append(f'<rect x="{PAD}" y="{art_top+2:.1f}" width="{CELL_W*1.6:.1f}" height="{art_h-4:.1f}" '
             f'fill="{INK}" opacity="0.16">'
             f'<animate attributeName="x" from="{PAD}" to="{PAD+art_w:.0f}" begin="0s" '
             f'dur="{reveal:.2f}s" fill="freeze"/>'
             f'<set attributeName="opacity" to="0" begin="{reveal:.2f}s"/></rect>')
             
    # Infinite rocking loop
    n = len(frames)
    for i, rows in enumerate(frames):
        if i == 0:
            vals, kt = "1;0", f"0;{1/n:.5f}"
        else:
            vals, kt = "0;1;0", f"0;{i/n:.5f};{(i+1)/n:.5f}"
        anim = (f'<animate attributeName="opacity" calcMode="discrete" values="{vals}" '
                f'keyTimes="{kt}" dur="{dur:.2f}s" begin="{reveal:.2f}s" '
                f'repeatCount="indefinite"/>')
        p.append(frame_g(rows, ' opacity="0"').replace("</g>", anim + "</g>"))
        
    p.append("</svg>")
    
    out_path = os.path.join("assets", "wordmark.svg")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("".join(p))
    print(f"Successfully generated wordmark: {out_path}")
    return True

# -----------------------------------------------------------------------------
# 2. ASCII Portrait SVG Generator (Pure PIL/NumPy Fallback)
# -----------------------------------------------------------------------------
def generate_portrait():
    if not os.path.exists(PHOTO_PATH):
        print(f"Portrait source image '{PHOTO_PATH}' not found. Skipping portrait.")
        return False
        
    COLS = 100
    ROWS = 53
    CELL_W = 8
    CELL_H = 15
    RAMP = " .`:-=+*cs#%@"
    
    CONTRAST = 1.25
    BRIGHTNESS = 1.05
    GAMMA = 1.20
    WHITE_FLOOR = 0.82
    
    PAD = 20
    TITLEBAR_H = 30
    STATUS_H = 30
    ART_W = COLS * CELL_W
    ART_H = ROWS * CELL_H
    CANVAS_W = ART_W + PAD * 2
    CANVAS_H = TITLEBAR_H + ART_H + STATUS_H + PAD
    
    # Load image and apply enhancements using pure PIL
    im = Image.open(PHOTO_PATH).convert("L")
    im = ImageEnhance.Brightness(im).enhance(BRIGHTNESS)
    im = ImageEnhance.Contrast(im).enhance(CONTRAST)
    im = im.resize((COLS, ROWS), Image.Resampling.LANCZOS)
    px = im.load()
    
    rows_txt = []
    for y in range(ROWS):
        chars = []
        for x in range(COLS):
            lum = px[x, y] / 255.0
            lum = pow(lum, GAMMA)
            
            if lum >= WHITE_FLOOR:
                chars.append(" ")
                continue
                
            idx = int((1.0 - lum) * (len(RAMP) - 1) + 0.5)
            idx = max(0, min(len(RAMP) - 1, idx))
            chars.append(RAMP[idx])
        rows_txt.append("".join(chars))
        
    art_top = TITLEBAR_H + PAD * 0.35
    ROW_DUR = 0.11
    STAGGER = 0.11
    
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
        f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, '
        f'Menlo, Consolas, monospace">',
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
        f'</linearGradient></defs>',
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" '
        f'fill="none" stroke="{FRAME}" stroke-width="1"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    
    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
    parts.append(f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="12" '
                 f'text-anchor="middle">{USERNAME}@github: ~$ ./portrait.sh</text>')
                 
    font_size = CELL_H * 0.86
    for ry, line in enumerate(rows_txt):
        y = art_top + ry * CELL_H + CELL_H * 0.74
        row_y = art_top + ry * CELL_H
        delay = ry * STAGGER
        safe = html.escape(line)
        text = (f'<text xml:space="preserve" x="{PAD}" y="{y:.1f}" fill="{INK}" '
                f'font-size="{font_size:.1f}" textLength="{ART_W}" lengthAdjust="spacing">{safe}</text>')
                
        parts.append(
            f'<clipPath id="r{ry}"><rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H}" width="0">'
            f'<animate attributeName="width" from="0" to="{ART_W}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.2f}s" fill="freeze"/></rect></clipPath>'
        )
        parts.append(f'<g clip-path="url(#r{ry})">{text}</g>')
        parts.append(
            f'<rect y="{row_y+1:.1f}" width="{CELL_W}" height="{CELL_H-2}" fill="{CURSOR}" opacity="0">'
            f'<animate attributeName="x" from="{PAD}" to="{PAD+ART_W}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.85" begin="{delay:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>'
        )
        
    status_line_y = TITLEBAR_H + ART_H + PAD * 0.35
    status_y = status_line_y + 19
    parts.append(f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W}" y2="{status_line_y:.1f}" stroke="{FRAME}"/>')
    parts.append(f'<text x="{PAD}" y="{status_y:.1f}" fill="{TITLE_TEXT}" font-size="13">'
                 f'{USERNAME}@github:~$ whoami <tspan fill="{INK}">{DISPLAY_NAME}</tspan></text>')
    parts.append(f'<rect x="{PAD+196 + len(DISPLAY_NAME)*4}" y="{status_y-12:.1f}" width="8" height="14" fill="{INK}">'
                 f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
                 f'dur="1s" repeatCount="indefinite"/></rect>')
                 
    parts.append("</svg>")
    
    out_path = os.path.join("assets", "portrait.svg")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("".join(parts))
    print(f"Successfully generated portrait: {out_path}")
    return True

# -----------------------------------------------------------------------------
# 3. Live Contribution Heatmap Graph SVG Generator (Scraping)
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
# 4. README.md Generator
# -----------------------------------------------------------------------------
def generate_readme(has_portrait, has_wordmark, has_contrib):
    md = []
    md.append('<div align="center">\n\n')
    
    # 1. Whoami / Terminal Header section
    md.append(f'<h3><code>{USERNAME}@github ~ $ whoami</code></h3>\n\n')
    md.append('<table>\n<tr>\n')
    
    if has_portrait:
        md.append(f'<td valign="top"><img src="./assets/portrait.svg" width="370" alt="{DISPLAY_NAME} — ASCII portrait" /></td>\n')
    else:
        md.append(f'<td valign="middle" align="center" width="370"><code>[Photo not provided]</code></td>\n')
        
    if has_wordmark:
        md.append(f'<td valign="top"><img src="./assets/wordmark.svg" width="490" alt="{WORDMARK_TEXT} — 3D ASCII wordmark" /></td>\n')
    else:
        md.append(f'<td valign="middle" align="center" width="490"><code>{WORDMARK_TEXT}</code></td>\n')
        
    md.append('</tr>\n</table>\n\n<br>\n<br>\n\n')
    
    # 2. Contributions Heatmap
    if has_contrib:
        md.append(f'<h3><code>{USERNAME}@github ~ $ ./contributions.sh</code></h3>\n\n')
        md.append(f'<img src="./assets/contrib-heatmap.svg" width="860" alt="{DISPLAY_NAME}\'s GitHub contribution graph — auto-refreshed daily" />\n\n')
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
# 5. Generate GitHub Action Workflow
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
          file_pattern: "assets/contrib-heatmap.svg assets/wordmark.svg README.md"
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
    
    has_wordmark = generate_wordmark()
    has_portrait = generate_portrait()
    has_contrib = generate_contributions()
    
    generate_readme(has_portrait, has_wordmark, has_contrib)
    generate_workflow()
    
    print("="*60)
    print("Done! You can commit the files in 'assets/', '.github/' and 'README.md'")
    print("to your personal GitHub profile repository.")
    print("="*60)
