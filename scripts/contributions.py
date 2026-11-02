"""Render the public GitHub contribution calendar as assets/contributions.svg.

GitHub's calendar includes private contributions only when "Include private
contributions on my profile" is enabled in the profile settings.
"""
import html
import re
import sys
import urllib.request

USER = "Jayanth19524"
BG, LINE, DIM, ACC = "#0a0a0d", "#1e1e26", "#8b8b96", "#fcee0a"
MONO = "'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
LEVEL_OPACITY = {0: None, 1: 0.28, 2: 0.5, 3: 0.75, 4: 1.0}
CELL, GAP, LEFT, TOP = 11, 3, 48, 78


def fetch():
    req = urllib.request.Request(
        f"https://github.com/users/{USER}/contributions",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    return urllib.request.urlopen(req, timeout=30).read().decode()


def parse(page):
    tips = {}
    for tid, text in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', page):
        m = re.match(r"(\d+) contribution", text)
        tips[tid] = int(m.group(1)) if m else 0
    days = []
    for tag in re.findall(r"<td [^>]*data-date=[^>]*>", page):
        date = re.search(r'data-date="([^"]+)"', tag).group(1)
        level = int(re.search(r'data-level="(\d)"', tag).group(1))
        cid = re.search(r'id="([^"]+)"', tag)
        days.append((date, level, tips.get(cid.group(1), 0) if cid else 0))
    return sorted(days)


def render(days):
    from datetime import date
    first = date.fromisoformat(days[0][0])
    offset = (first.weekday() + 1) % 7  # weeks start on Sunday
    total = sum(c for _, _, c in days)
    active = sum(1 for _, _, c in days if c)
    cols = (len(days) + offset + 6) // 7
    width = LEFT * 2 + cols * (CELL + GAP) - GAP
    height = TOP + 7 * (CELL + GAP) + 44
    rects = []
    for i, (d, level, count) in enumerate(days):
        col, row = divmod(i + offset, 7)
        x, y = LEFT + col * (CELL + GAP), TOP + row * (CELL + GAP)
        op = LEVEL_OPACITY[level]
        fill = f'fill="{ACC}" fill-opacity="{op}"' if op else f'fill="{LINE}"'
        delay = f"{col * 0.015:.2f}"
        title = html.escape(f"{count} contribution{'s' if count != 1 else ''} on {d}")
        rects.append(
            f'<rect class="c" style="animation-delay:{delay}s" x="{x}" y="{y}" '
            f'width="{CELL}" height="{CELL}" rx="2" {fill}><title>{title}</title></rect>'
        )
    legend_x = width - LEFT - 5 * (CELL + GAP) - 70
    legend = f'<text x="{legend_x}" y="{height - 16}" font-family="{MONO}" font-size="11" fill="{DIM}">less</text>'
    for i in range(5):
        op = LEVEL_OPACITY[i]
        fill = f'fill="{ACC}" fill-opacity="{op}"' if op else f'fill="{LINE}"'
        legend += f'<rect x="{legend_x + 34 + i * (CELL + GAP)}" y="{height - 26}" width="{CELL}" height="{CELL}" rx="2" {fill}/>'
    legend += f'<text x="{legend_x + 34 + 5 * (CELL + GAP) + 4}" y="{height - 16}" font-family="{MONO}" font-size="11" fill="{DIM}">more</text>'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
<style>.c{{animation:in .5s ease-out both}}@keyframes in{{from{{opacity:0}}to{{opacity:1}}}}</style>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="14" fill="{BG}" stroke="{LINE}"/>
<text x="{LEFT}" y="40" font-family="{MONO}" font-size="12" fill="{DIM}" letter-spacing="3">COMMIT ACTIVITY  /  LAST 12 MONTHS</text>
<text x="{width - LEFT}" y="40" text-anchor="end" font-family="{MONO}" font-size="12" fill="{ACC}">{total} contributions  ·  {active} active days</text>
{''.join(rects)}
{legend}
</svg>"""


if __name__ == "__main__":
    days = parse(fetch())
    if len(days) < 300:
        sys.exit(f"unexpected calendar size: {len(days)} days")
    open("assets/contributions.svg", "w").write(render(days))
    print(f"wrote assets/contributions.svg ({len(days)} days)")
