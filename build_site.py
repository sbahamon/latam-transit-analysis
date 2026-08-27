#!/usr/bin/env python3
"""Build index.html for GitHub Pages from data/*.json and the analysis markdown.

Standard library only, so it runs anywhere. The JSON files in data/ are the
single source of truth for board membership; this script inlines them into the
page so the site needs no fetch and works from file:// too.

Usage:  python3 build_site.py
"""

import html
import json
import pathlib
import re
import collections

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "data"
ANALYSIS = ROOT / "latam_transit_board_analysis.md"
OUT = ROOT / "index.html"

CATEGORIES = [
    "Transit Ops/Management",
    "Other Management/Policy",
    "Labor Representative",
    "Community Advocate",
    "Elected Official",
]
# Short labels for tight spaces (chart axis, dot legend).
SHORT = {
    "Transit Ops/Management": "Transit ops",
    "Other Management/Policy": "Other mgmt / policy",
    "Labor Representative": "Labor",
    "Community Advocate": "Community advocate",
    "Elected Official": "Elected official",
}


# --------------------------------------------------------------------------
# Markdown subset -> HTML
#
# Covers exactly what latam_transit_board_analysis.md uses: h1-h3, paragraphs,
# unordered and ordered lists, pipe tables, horizontal rules, bold, italic,
# inline code, and links. verify_no_markdown_leaked() below is the check that
# this stayed true.
# --------------------------------------------------------------------------

def _inline(text):
    """Inline spans. Escapes first, so no user content can inject markup."""
    out = html.escape(text, quote=False)
    # Links before emphasis: link text may itself be bold.
    out = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        r'<a href="\2" rel="noopener">\1</a>',
        out,
    )
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", out)
    # The document uses `---` mid-sentence as an em dash and `--` as an en dash.
    out = out.replace("---", "—").replace("--", "–")
    return out


def _table(rows):
    """rows: list of raw '| a | b |' lines, including the |---| separator."""
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    header, body = cells[0], cells[2:]  # cells[1] is the alignment separator
    out = ['<div class="scroll"><table>', "<thead><tr>"]
    out += [f"<th>{_inline(c)}</th>" for c in header]
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def markdown_to_html(md):
    lines = md.split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped == "---":
            out.append("<hr>")
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            text = m.group(2)
            # Section numbers ("## 3. Comparative Analysis") become a separate
            # marker element so the number can be styled as a station label.
            num = re.match(r"^(\d+)\.\s+(.*)$", text)
            slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
            if num:
                out.append(
                    f'<h{level} id="{slug}">'
                    f'<span class="secnum">{num.group(1)}</span>'
                    f"{_inline(num.group(2))}</h{level}>"
                )
            else:
                out.append(f'<h{level} id="{slug}">{_inline(text)}</h{level}>')
            i += 1
            continue

        if stripped.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            out.append(_table(block))
            continue

        if re.match(r"^[-*]\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            out.append("<ul>" + "".join(f"<li>{_inline(x)}</li>" for x in items) + "</ul>")
            continue

        if re.match(r"^\d+\.\s+", stripped):
            items, start = [], int(re.match(r"^(\d+)\.", stripped).group(1))
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            out.append(
                f'<ol start="{start}">'
                + "".join(f"<li>{_inline(x)}</li>" for x in items)
                + "</ol>"
            )
            continue

        para = []
        while i < len(lines) and lines[i].strip() and not re.match(
            r"^(#{1,6}\s|\||[-*]\s|\d+\.\s|---$)", lines[i].strip()
        ):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{_inline(' '.join(para))}</p>")

    return "\n".join(out)


def verify_no_markdown_leaked(html_text):
    """Fail loudly rather than publish a page with raw markdown in it."""
    body = re.sub(r"<script[\s\S]*?</script>", "", html_text)
    problems = []
    for pattern, label in [
        (r"\*\*", "unconverted bold"),
        (r"^\s*\|", "unconverted table row"),
        (r"^#{1,6}\s", "unconverted heading"),
        (r"\]\(http", "unconverted link"),
    ]:
        hits = re.findall(pattern, body, re.MULTILINE)
        if hits:
            problems.append(f"{label}: {len(hits)}")
    return problems


# --------------------------------------------------------------------------
# Palette
#
# Not hand-picked. Hue families were fixed per category, then lightness and
# chroma were searched in OKLCH and scored with the dataviz skill's
# validate_palette.js under --pairs all (every pair, because 8 of the 10
# possible category pairs actually end up adjacent somewhere in this data).
#
#   light  CVD ΔE 14.7  ·  normal-vision ΔE 17.2  ·  all checks pass
#   dark   CVD ΔE  9.9  ·  normal-vision ΔE 15.4  ·  all checks pass
#
# One colour per mode sits under 3:1 against the surface. That obligates a
# relief channel, which the direct labels and the full member table provide.
# --------------------------------------------------------------------------

PALETTE_LIGHT = {
    "Transit Ops/Management":  "#488fe6",
    "Other Management/Policy": "#ca6a10",
    "Labor Representative":    "#94362a",
    "Community Advocate":      "#68c294",
    "Elected Official":        "#733b97",
}
PALETTE_DARK = {
    "Transit Ops/Management":  "#2489fa",
    "Other Management/Policy": "#ce6d16",
    "Labor Representative":    "#a63629",
    "Community Advocate":      "#3d996d",
    "Elected Official":        "#8b49b5",
}


def load_agencies():
    """The five LatAm agencies, as researched. data/ is the source of truth."""
    out = []
    for path in sorted(DATA.glob("*.json")):
        d = json.load(open(path, encoding="utf-8"))
        counts = collections.Counter(m["classification"] for m in d["members"])
        unknown = set(counts) - set(CATEGORIES)
        if unknown:
            raise SystemExit(f"{path.name}: unknown classification(s) {unknown}")
        n = len(d["members"])
        d["counts"] = counts
        d["pct"] = [round(counts.get(c, 0) / n * 100) for c in CATEGORIES]
        out.append(d)
    out.sort(key=lambda d: -d["pct"][0])
    return out


def load_day():
    return json.load(open(ROOT / "day_chart_reference.json", encoding="utf-8"))


def bar(pct, label, sub="", is_latam=False):
    """One stacked row. 2px surface gaps between segments (never a border);
    the free end of the last segment gets the 4px round."""
    segs = [(i, p) for i, p in enumerate(pct) if p > 0]
    total = sum(p for _, p in segs) or 100
    cells = []
    for k, (i, p) in enumerate(segs):
        last = k == len(segs) - 1
        # Only label a segment wide enough to hold the text with padding.
        text = f"{p}%" if p >= 11 else ""
        cells.append(
            f'<i class="seg s{i}{" end" if last else ""}" style="flex:{p}"'
            f' data-cat="{html.escape(CATEGORIES[i])}" data-pct="{p}"'
            f' data-agency="{html.escape(label)}">{text}</i>'
        )
    cls = "row latam" if is_latam else "row"
    subhtml = f'<span class="sub">{html.escape(sub)}</span>' if sub else ""
    return (
        f'<div class="{cls}"><div class="rowlab">{html.escape(label)}{subhtml}</div>'
        f'<div class="track" style="--total:{total}">' + "".join(cells) + "</div></div>"
    )


def build_chart(agencies, day):
    parts = []
    for region in day["regions"]:
        parts.append(f'<div class="region"><h4>{html.escape(region["region"])}'
                     f'<span class="rcount">{len(region["agencies"])} agencies · Day</span></h4>')
        for a in region["agencies"]:
            parts.append(bar(a["pct"], a["name"]))
        parts.append("</div>")
    parts.append('<div class="region new"><h4>Latin America'
                 '<span class="rcount">5 agencies · this research</span></h4>')
    for d in agencies:
        parts.append(bar(d["pct"], d["city"], sub=d["country"], is_latam=True))
    parts.append("</div>")
    return "".join(parts)


def build_legend():
    return "".join(
        f'<span class="key"><i class="sw s{i}"></i>{html.escape(SHORT[c])}</span>'
        for i, c in enumerate(CATEGORIES)
    )


def build_hero(agencies):
    """Every one of the 43 members as a single mark, grouped by agency.

    The whole dataset fits above the fold, and the finding reads straight off
    it: the community-advocate colour never appears.
    """
    rows = []
    for d in agencies:
        dots = []
        for cat_i, cat in enumerate(CATEGORIES):
            for _ in range(d["counts"].get(cat, 0)):
                dots.append(f'<i class="dot s{cat_i}" title="{html.escape(cat)}"></i>')
        rows.append(
            f'<div class="hrow"><span class="hname">{html.escape(d["city"])}'
            f'<em>{html.escape(d["country"])}</em></span>'
            f'<span class="dots">{"".join(dots)}</span>'
            f'<span class="hn">{len(d["members"])}</span></div>'
        )
    return "".join(rows)


def build_table(agencies):
    rows = []
    for d in agencies:
        for m in d["members"]:
            cat_i = CATEGORIES.index(m["classification"])
            srcs = " ".join(
                f'<a href="{html.escape(u)}" rel="noopener nofollow" title="{html.escape(u)}">{i+1}</a>'
                for i, u in enumerate(m.get("sources", []))
                if u.startswith("http")
            )
            conf = m.get("confidence", "Unknown")
            rows.append(
                f'<tr data-agency="{html.escape(d["city"])}"'
                f' data-cat="{html.escape(m["classification"])}"'
                f' data-conf="{html.escape(conf)}">'
                f'<td class="tname">{html.escape(m["name"])}</td>'
                f'<td>{html.escape(d["city"])}</td>'
                f'<td class="tpos">{html.escape(m.get("position",""))}</td>'
                f'<td class="tcat"><i class="sw s{cat_i}"></i>{html.escape(SHORT[m["classification"]])}</td>'
                f'<td><span class="conf c{html.escape(conf.lower())}">{html.escape(conf)}</span></td>'
                f'<td class="tsrc">{srcs or "—"}</td>'
                f'<td class="trat">{html.escape(m.get("rationale",""))}</td></tr>'
            )
    return "".join(rows)


def build_composite(agencies):
    total = sum(len(d["members"]) for d in agencies)
    counts = collections.Counter()
    for d in agencies:
        counts += d["counts"]
    return total, counts


CSS = """
:root{
  --paper:#e8e9e6; --panel:#fcfcfb; --ink:#12161a; --ink2:#4f5a64; --ink3:#7c8792;
  --rule:#cdd2d6; --rule2:#e2e5e6;
  --s0:#488fe6; --s1:#ca6a10; --s2:#94362a; --s3:#68c294; --s4:#733b97;
}
@media (prefers-color-scheme:dark){
  :root{
    --paper:#0e0e0d; --panel:#1a1a19; --ink:#e9eaea; --ink2:#a3aab0; --ink3:#767d83;
    --rule:#2d2f31; --rule2:#232525;
    --s0:#2489fa; --s1:#ce6d16; --s2:#a63629; --s3:#3d996d; --s4:#8b49b5;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:Newsreader,Georgia,'Times New Roman',serif;
  font-size:19px; line-height:1.62; font-optical-sizing:auto;
}
.wrap{max-width:1180px; margin:0 auto; padding:0 28px}
.narrow{max-width:720px}

/* ---- signage type ---------------------------------------------------- */
.dsp{
  font-family:Archivo,'Helvetica Neue',Arial,sans-serif;
  font-variation-settings:'wdth' 112;
  font-weight:800; letter-spacing:-.018em; line-height:1.02;
  text-transform:none;
}
.mono{font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace}
.eyebrow{
  font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:500;
  letter-spacing:.16em; text-transform:uppercase; color:var(--ink3);
}

/* ---- masthead -------------------------------------------------------- */
header.mast{border-bottom:2px solid var(--ink); background:var(--panel)}
.mast .wrap{padding-top:44px; padding-bottom:34px}
h1.title{margin:14px 0 0; font-size:clamp(38px,6.6vw,76px)}
.standfirst{
  margin:20px 0 0; max-width:60ch; font-size:21px; color:var(--ink2);
}
.byline{margin-top:26px; display:flex; flex-wrap:wrap; gap:8px 22px; align-items:baseline}

/* ---- provenance ------------------------------------------------------ */
.prov{
  background:var(--panel); border:2px solid var(--ink); border-radius:3px;
  padding:22px 24px; margin:34px 0 0;
}
.prov h2{
  margin:0 0 10px; font-size:13px; letter-spacing:.14em; text-transform:uppercase;
  font-family:'JetBrains Mono',monospace; font-weight:700;
}
.prov p{margin:0 0 10px; font-size:17px; line-height:1.55; color:var(--ink2)}
.prov p:last-child{margin-bottom:0}
.prov strong{color:var(--ink)}

/* ---- sections -------------------------------------------------------- */
main{padding:0 0 80px}
section{padding:64px 0 8px; border-top:1px solid var(--rule)}
section:first-of-type{border-top:0}
.sechead{display:flex; align-items:baseline; gap:16px; margin-bottom:8px}
h2.sec{margin:0; font-size:clamp(25px,3.4vw,38px)}
.lede{max-width:62ch; color:var(--ink2); margin:10px 0 30px}

/* ---- hero unit chart ------------------------------------------------- */
.hero{background:var(--panel); border:1px solid var(--rule); border-radius:3px; padding:26px 26px 20px}
.hrow{display:grid; grid-template-columns:150px 1fr 34px; align-items:center; gap:16px; padding:9px 0}
.hrow+.hrow{border-top:1px solid var(--rule2)}
.hname{font-family:Archivo,sans-serif; font-variation-settings:'wdth' 108; font-weight:700; font-size:15px; line-height:1.2}
.hname em{display:block; font-style:normal; font-weight:400; font-size:11.5px; color:var(--ink3); letter-spacing:.04em; text-transform:uppercase}
.dots{display:flex; flex-wrap:wrap; gap:4px}
.dot{width:17px; height:17px; border-radius:3px; display:block}
.hn{font-family:'JetBrains Mono',monospace; font-size:13px; color:var(--ink3); text-align:right}
.herofoot{margin-top:18px; padding-top:16px; border-top:2px solid var(--ink); display:flex; flex-wrap:wrap; gap:12px 28px; align-items:baseline}
.zero{font-family:Archivo,sans-serif; font-variation-settings:'wdth' 118; font-weight:800; font-size:44px; line-height:.9}
.zerolab{max-width:44ch; font-size:16px; color:var(--ink2)}

/* ---- stacked bar chart ---------------------------------------------- */
.chartbox{background:var(--panel); border:1px solid var(--rule); border-radius:3px; padding:26px 26px 22px}
.legend{display:flex; flex-wrap:wrap; gap:10px 22px; margin:0 0 22px; padding-bottom:18px; border-bottom:1px solid var(--rule2)}
.key{display:inline-flex; align-items:center; gap:8px; font-size:13.5px; color:var(--ink2); font-family:Archivo,sans-serif; font-variation-settings:'wdth' 100}
.sw{width:13px; height:13px; border-radius:3px; display:inline-block; flex:none}
.region{margin:0 0 26px}
.region h4{
  margin:0 0 12px; font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700;
  letter-spacing:.16em; text-transform:uppercase; color:var(--ink);
  display:flex; align-items:baseline; gap:12px;
}
.region h4::after{content:""; flex:1; height:1px; background:var(--rule)}
.rcount{font-weight:400; letter-spacing:.08em; color:var(--ink3); text-transform:none; order:3}
.region.new h4{color:var(--s0)}
.row{display:grid; grid-template-columns:172px 1fr; align-items:center; gap:16px; padding:5px 0}
.rowlab{font-family:Archivo,sans-serif; font-variation-settings:'wdth' 104; font-size:14px; font-weight:500; line-height:1.15; text-align:right; color:var(--ink2)}
.row.latam .rowlab{font-weight:800; color:var(--ink)}
.rowlab .sub{display:block; font-size:10.5px; color:var(--ink3); text-transform:uppercase; letter-spacing:.05em}
/* 2px gaps in the surface colour separate segments - never a border. */
.track{display:flex; gap:2px; height:22px; align-items:stretch}
.seg{
  display:flex; align-items:center; justify-content:center; min-width:2px;
  font-family:'JetBrains Mono',monospace; font-size:10.5px; font-style:normal;
  color:#fff; letter-spacing:-.01em; cursor:default;
  transition:filter .12s ease;
}
.seg.end{border-radius:0 4px 4px 0}
.seg:hover{filter:brightness(1.14)}
.s0{background:var(--s0)} .s1{background:var(--s1)} .s2{background:var(--s2)}
.s3{background:var(--s3)} .s4{background:var(--s4)}
.seg.s3{color:#10231a}
.chartnote{margin:6px 0 0; font-size:13.5px; color:var(--ink3); line-height:1.5}
.chartnote a{color:var(--ink2)}

/* ---- tooltip --------------------------------------------------------- */
#tip{
  position:fixed; z-index:60; pointer-events:none; opacity:0; transition:opacity .1s;
  background:var(--ink); color:var(--paper); padding:7px 10px; border-radius:4px;
  font-family:'JetBrains Mono',monospace; font-size:11.5px; line-height:1.45; max-width:240px;
}
#tip b{display:block; font-size:12.5px}

/* ---- member table ---------------------------------------------------- */
.controls{display:flex; flex-wrap:wrap; gap:12px; margin:0 0 18px; align-items:center}
.controls select,.controls input{
  font-family:Archivo,sans-serif; font-size:14px; padding:8px 11px; color:var(--ink);
  background:var(--panel); border:1px solid var(--rule); border-radius:3px;
}
.controls input{min-width:210px}
.count{font-family:'JetBrains Mono',monospace; font-size:12px; color:var(--ink3); margin-left:auto}
.scroll{overflow-x:auto; -webkit-overflow-scrolling:touch}
table{border-collapse:collapse; width:100%; font-size:15px; background:var(--panel)}
#members{min-width:1080px}
th,td{text-align:left; padding:10px 13px; border-bottom:1px solid var(--rule2); vertical-align:top}
thead th{
  position:sticky; top:0; background:var(--panel); z-index:2;
  font-family:'JetBrains Mono',monospace; font-size:10.5px; font-weight:700;
  letter-spacing:.1em; text-transform:uppercase; color:var(--ink3);
  border-bottom:2px solid var(--ink); white-space:nowrap;
}
#members thead th{cursor:pointer; user-select:none}
#members thead th:hover{color:var(--ink)}
#members thead th[aria-sort]::after{content:" ▲"; font-size:9px}
#members thead th[aria-sort=descending]::after{content:" ▼"}
.tname{font-family:Archivo,sans-serif; font-weight:600; font-size:14.5px; white-space:nowrap}
.tpos{width:190px; font-size:13.5px; color:var(--ink2)}
.trat{width:430px; font-size:13.5px; line-height:1.5; color:var(--ink2)}
#members td:nth-child(2){white-space:nowrap; font-size:14px}
.tcat{white-space:nowrap; font-size:13.5px}
.tcat .sw{margin-right:7px; vertical-align:-1px}
.tsrc a{
  display:inline-block; min-width:19px; text-align:center; margin-right:3px;
  font-family:'JetBrains Mono',monospace; font-size:11px; padding:1px 4px;
  border:1px solid var(--rule); border-radius:3px; color:var(--ink2); text-decoration:none;
}
.tsrc a:hover{border-color:var(--ink); color:var(--ink)}
.conf{font-family:'JetBrains Mono',monospace; font-size:10.5px; letter-spacing:.06em; text-transform:uppercase; padding:2px 7px; border-radius:99px; border:1px solid var(--rule); color:var(--ink2); white-space:nowrap}
.chigh{border-color:var(--ink2); color:var(--ink)}
.clow{border-color:var(--s2); color:var(--s2)}

/* ---- prose ----------------------------------------------------------- */
.prose h1{display:none}
.prose h2{margin:56px 0 4px; font-family:Archivo,sans-serif; font-variation-settings:'wdth' 112; font-weight:800; font-size:clamp(24px,3.2vw,34px); letter-spacing:-.015em; line-height:1.1}
.prose h3{margin:38px 0 2px; font-family:Archivo,sans-serif; font-variation-settings:'wdth' 104; font-weight:700; font-size:20px; letter-spacing:-.005em}
.prose .secnum{
  display:inline-block; min-width:1.9em; margin-right:.5em; color:var(--s0);
  font-family:'JetBrains Mono',monospace; font-size:.55em; font-weight:700;
  vertical-align:.35em; letter-spacing:0;
}
.prose p{margin:14px 0}
.prose ul,.prose ol{margin:14px 0; padding-left:1.25em}
.prose li{margin:7px 0}
.prose hr{border:0; border-top:1px solid var(--rule); margin:44px 0}
.prose table{font-size:14.5px; margin:20px 0}
.prose code{font-family:'JetBrains Mono',monospace; font-size:.85em; background:var(--rule2); padding:1px 5px; border-radius:3px}
.prose a{color:var(--ink); text-decoration-color:var(--s0); text-underline-offset:3px}
.prose strong{font-weight:700}
.prose>p:first-of-type{font-size:17px; color:var(--ink2)}

footer{border-top:2px solid var(--ink); background:var(--panel); padding:40px 0; font-size:15px; color:var(--ink2)}
footer a{color:var(--ink)}
a{color:var(--ink)}

@media (max-width:760px){
  body{font-size:17px}
  .wrap{padding:0 18px}
  .hrow{grid-template-columns:1fr; gap:6px}
  .hn{display:none}
  .row{grid-template-columns:1fr; gap:4px; padding:8px 0}
  .rowlab{text-align:left}
  .rowlab .sub{display:inline; margin-left:8px}
  .hero,.chartbox{padding:18px 16px}
  .count{margin-left:0}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important; animation:none!important}}
"""

JS = """
(function(){
  var tip=document.getElementById('tip');
  function show(e,t){tip.innerHTML=t;tip.style.opacity=1;move(e);}
  function move(e){
    var r=tip.getBoundingClientRect(), x=e.clientX+14, y=e.clientY+16;
    if(x+r.width>innerWidth-8) x=e.clientX-r.width-14;
    if(y+r.height>innerHeight-8) y=e.clientY-r.height-16;
    tip.style.left=x+'px'; tip.style.top=y+'px';
  }
  document.querySelectorAll('.seg').forEach(function(s){
    s.addEventListener('mouseenter',function(e){
      show(e,'<b>'+s.dataset.agency+'</b>'+s.dataset.cat+' — '+s.dataset.pct+'%');
    });
    s.addEventListener('mousemove',move);
    s.addEventListener('mouseleave',function(){tip.style.opacity=0;});
  });
  document.querySelectorAll('.dot').forEach(function(d){
    d.addEventListener('mouseenter',function(e){show(e,d.getAttribute('title'));});
    d.addEventListener('mousemove',move);
    d.addEventListener('mouseleave',function(){tip.style.opacity=0;});
  });

  var tbl=document.getElementById('members'); if(!tbl) return;
  var body=tbl.tBodies[0], rows=[].slice.call(body.rows);
  var fa=document.getElementById('f-agency'), fc=document.getElementById('f-cat'),
      fq=document.getElementById('f-q'), out=document.getElementById('f-count');
  function apply(){
    var a=fa.value, c=fc.value, q=(fq.value||'').toLowerCase().trim(), n=0;
    rows.forEach(function(r){
      var ok=(!a||r.dataset.agency===a)&&(!c||r.dataset.cat===c)&&
             (!q||r.textContent.toLowerCase().indexOf(q)>-1);
      r.hidden=!ok; if(ok)n++;
    });
    out.textContent=n+' of '+rows.length+' members';
  }
  [fa,fc].forEach(function(el){el.addEventListener('change',apply);});
  fq.addEventListener('input',apply);
  [].slice.call(tbl.tHead.rows[0].cells).forEach(function(th,i){
    th.addEventListener('click',function(){
      var desc=th.getAttribute('aria-sort')==='ascending';
      [].slice.call(tbl.tHead.rows[0].cells).forEach(function(o){o.removeAttribute('aria-sort');});
      th.setAttribute('aria-sort',desc?'descending':'ascending');
      rows.sort(function(x,y){
        var p=x.cells[i].textContent.trim(), q2=y.cells[i].textContent.trim();
        return (desc?-1:1)*p.localeCompare(q2,'es');
      });
      rows.forEach(function(r){body.appendChild(r);});
    });
  });
  apply();
})();
"""


PROVENANCE = """<h2>How this was made — read before citing</h2>
<p>The board rosters and classifications on this page were <strong>researched and
written by Claude (Anthropic's AI)</strong>, in a single session on
<strong>17 March 2026</strong>, from agency websites, government gazettes, and
regulatory filings. The classifications are <strong>Claude's judgment</strong>
applied to Richard Day's five categories — not an official designation by any
agency.</p>
<p><strong>Steffany Bahamon spot-checked portions by hand. This has not been
verified line by line.</strong> Every one of the 43 member records below carries a
confidence rating and its source links, so any individual claim can be checked.
Treat medium- and low-confidence rows as leads, not findings.</p>
<p>Board composition also changes. These rosters are a snapshot of March 2026 and
will go stale.</p>"""

PAGE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Who Runs Latin America's Metros</title>
<meta name="description" content="Board composition for five major Latin American metro agencies, classified with Richard Day's five-category framework. AI-assisted research; sources and confidence ratings per member.">
<meta property="og:title" content="Who Runs Latin America's Metros">
<meta property="og:description" content="43 board members across Santiago, Medellin, Mexico City, Sao Paulo and Buenos Aires, classified and sourced.">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http%3A//www.w3.org/2000/svg' viewBox='0 0 16 16'><rect width='16' height='16' rx='2' fill='%23fcfcfb'/><rect x='2' y='3'  width='12' height='2.4' rx='.6' fill='%23488fe6'/><rect x='2' y='6.8' width='12' height='2.4' rx='.6' fill='%23ca6a10'/><rect x='2' y='10.6' width='8'  height='2.4' rx='.6' fill='%23733b97'/></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..125,400..800&family=Newsreader:ital,opsz,wght@0,6..72,300..700;1,6..72,300..600&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>__CSS__</style>
</head><body>
<div id="tip" role="status" aria-live="polite"></div>

<header class="mast"><div class="wrap">
  <p class="eyebrow">Addendum · A City That Works · March 2026</p>
  <h1 class="title dsp">Who runs Latin&nbsp;America's metros</h1>
  <p class="standfirst">Richard Day found that the world's best transit systems are run by
  boards of transit experts, and the worst by boards of politicians. He measured sixteen
  agencies across Asia, Europe and the United States. He measured none in Latin America.
  This is that missing column: <strong>43 board members, five agencies, five countries.</strong></p>
  <div class="byline">
    <span class="eyebrow">Research by Claude (AI)</span>
    <span class="eyebrow">Edited by Steffany Bahamon</span>
    <span class="eyebrow">Verified 17 Mar 2026</span>
  </div>
  <div class="prov">__PROV__</div>
</div></header>

<main>
<section><div class="wrap">
  <div class="sechead"><h2 class="sec dsp">Every seat, all forty-three</h2></div>
  <p class="lede">One mark per board member, coloured by category. The whole dataset,
  before any averaging.</p>
  <div class="hero">
    __HERO__
    <div class="legend" style="margin:20px 0 0;padding:16px 0 0;border-top:1px solid var(--rule2);border-bottom:0">__LEGEND__</div>
    <div class="herofoot">
      <span class="zero dsp">0</span>
      <span class="zerolab">community advocates among all 43 members. Not one seat, in any
      of the five agencies. In Day's US sample the same category runs as high as 50%.</span>
    </div>
  </div>
</div></section>

<section><div class="wrap">
  <div class="sechead"><h2 class="sec dsp">A fourth region on Day's chart</h2></div>
  <p class="lede">The five Latin American agencies placed alongside Day's sixteen, same
  five categories, same measure. Hover any segment for the exact figure.</p>
  <div class="chartbox">
    <div class="legend">__LEGEND__</div>
    __CHART__
    <p class="chartnote">The sixteen Asian, European and US rows are Richard Day's work,
    read from his chart in
    <a href="https://citythatworks.substack.com/p/who-should-lead-our-transit-agencies" rel="noopener">“Put real experts in charge of transit”</a>
    (A City That Works, March 2026); a few of his rows sum to 99% or 101% from his own
    rounding. The five Latin American rows are computed from the member records below.
    Chart rebuilt rather than reproduced.</p>
  </div>
</div></section>

<section><div class="wrap">
  <div class="sechead"><h2 class="sec dsp">The 43 members</h2></div>
  <p class="lede">Every classification with its rationale, confidence rating and sources.
  This table is the evidence for everything above — if a claim matters to you, check it here.</p>
  <div class="controls">
    <select id="f-agency"><option value="">All agencies</option>__OPT_AGENCY__</select>
    <select id="f-cat"><option value="">All categories</option>__OPT_CAT__</select>
    <input id="f-q" type="search" placeholder="Search names, roles, rationale…" aria-label="Search members">
    <span class="count" id="f-count"></span>
  </div>
  <div class="scroll"><table id="members">
    <thead><tr><th>Member</th><th>Agency</th><th>Position</th><th>Classification</th>
    <th>Confidence</th><th>Sources</th><th>Rationale</th></tr></thead>
    <tbody>__ROWS__</tbody>
  </table></div>
</div></section>

<section><div class="wrap narrow">
  <div class="sechead"><h2 class="sec dsp">The full analysis</h2></div>
  <div class="prose">__PROSE__</div>
</div></section>
</main>

<footer><div class="wrap">
  <p><strong>Source data and code:</strong>
  <a href="https://github.com/sbahamon/latam-transit-analysis" rel="noopener">github.com/sbahamon/latam-transit-analysis</a>.
  The five JSON files in <code>data/</code> are the source of truth; this page is generated
  from them by <code>build_site.py</code>.</p>
  <p>Framework and the sixteen comparison agencies: Richard Day,
  <a href="https://citythatworks.substack.com/p/who-should-lead-our-transit-agencies" rel="noopener">A City That Works</a>.
  Research by Claude, edited by Steffany Bahamon. MIT licensed.</p>
</div></footer>
<script>__JS__</script>
</body></html>
"""


def main():
    agencies = load_agencies()
    day = load_day()
    total, counts = build_composite(agencies)
    if total != 43:
        raise SystemExit(f"expected 43 members, found {total}")

    md = ANALYSIS.read_text(encoding="utf-8")
    prose = markdown_to_html(md)

    opt_agency = "".join(
        f'<option value="{html.escape(d["city"])}">{html.escape(d["city"])}</option>'
        for d in sorted(agencies, key=lambda x: x["city"])
    )
    opt_cat = "".join(
        f'<option value="{html.escape(c)}">{html.escape(SHORT[c])}</option>'
        for c in CATEGORIES
    )

    page = (PAGE
            .replace("__CSS__", CSS)
            .replace("__JS__", JS)
            .replace("__PROV__", PROVENANCE)
            .replace("__HERO__", build_hero(agencies))
            .replace("__CHART__", build_chart(agencies, day))
            .replace("__LEGEND__", build_legend())
            .replace("__ROWS__", build_table(agencies))
            .replace("__OPT_AGENCY__", opt_agency)
            .replace("__OPT_CAT__", opt_cat)
            .replace("__PROSE__", prose))

    leaks = verify_no_markdown_leaked(page)
    if leaks:
        raise SystemExit("markdown leaked into the page: " + "; ".join(leaks))
    left = re.findall(r"__[A-Z_]+__", page)
    if left:
        raise SystemExit("unfilled placeholders: " + ", ".join(sorted(set(left))))

    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.name}  {len(page):,} bytes")
    print(f"  {total} members, {len(agencies)} LatAm agencies + "
          f"{sum(len(r['agencies']) for r in day['regions'])} from Day")
    for c in CATEGORIES:
        print(f"  {c:26s} {counts.get(c,0):2d}  {counts.get(c,0)/total*100:4.1f}%")


if __name__ == "__main__":
    main()
