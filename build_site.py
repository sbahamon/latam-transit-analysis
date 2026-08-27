#!/usr/bin/env python3
"""Build index.html for GitHub Pages from data/*.json and the analysis markdown.

Standard library only, so it runs anywhere. The JSON files in data/ are the
single source of truth for board membership; this script inlines them into the
page so the site needs no fetch and works from file:// too.

Usage:  python3 build_site.py
"""

import decimal
import html
import json
import pathlib
import re
import collections

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "data"
# Chicago comparison cohort, researched here, kept out of the LatAm composite.
COMPARISON = ROOT / "data_chicago"
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
    """rows: list of raw '| a | b |' lines, including the |---| separator.

    Each cell carries data-label with its column heading, so the responsive
    CSS can stack the table into labelled rows on a narrow screen instead of
    forcing a sideways scroll.
    """
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    header, body = cells[0], cells[2:]  # cells[1] is the alignment separator
    labels = [re.sub(r"[*`]", "", c) for c in header]
    out = ['<div class="scroll"><table class="stack">', "<thead><tr>"]
    out += [f"<th>{_inline(c)}</th>" for c in header]
    out.append("</tr></thead><tbody>")
    for row in body:
        tds = "".join(
            f'<td data-label="{html.escape(labels[i] if i < len(labels) else "")}">{_inline(c)}</td>'
            for i, c in enumerate(row)
        )
        out.append("<tr>" + tds + "</tr>")
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


def pct(k, n):
    """Half-up. Python's round() is banker's rounding, which turns 12.5% into
    12% - the exact discrepancy that showed up against Day's TfL row."""
    return int(decimal.Decimal(k * 100 / n).quantize(decimal.Decimal("1"),
                                                     rounding=decimal.ROUND_HALF_UP))


def _load_dir(directory):
    """Shared by both cohorts: read one JSON per agency, count, compute shares."""
    out = []
    for path in sorted(directory.glob("*.json")):
        d = json.load(open(path, encoding="utf-8"))
        counts = collections.Counter(m["classification"] for m in d["members"])
        unknown = set(counts) - set(CATEGORIES)
        if unknown:
            raise SystemExit(f"{path.name}: unknown classification(s) {unknown}")
        n = len(d["members"])
        d["counts"] = counts
        d["pct"] = [pct(counts.get(c, 0), n) for c in CATEGORIES]
        out.append(d)
    out.sort(key=lambda d: -d["pct"][0])
    return out


def load_agencies():
    """The five LatAm agencies. data/ is the source of truth."""
    return _load_dir(DATA)


def load_comparison():
    """The Chicago cohort researched here (NITA). Deliberately NOT part of the
    LatAm composite - it is the comparator, not the subject."""
    return _load_dir(COMPARISON)


def alt_counts(d):
    """Day's stated rules and his applied classifications diverge. Where a member
    classifies differently under his applied practice, the record carries
    day_alt_classification; this recomputes the board under that reading so both
    can be published rather than one being asserted over the other."""
    counts = collections.Counter(
        m.get("day_alt_classification") or m["classification"] for m in d["members"]
    )
    n = len(d["members"])
    return counts, [pct(counts.get(c, 0), n) for c in CATEGORIES]


def has_alt(d):
    return any(m.get("day_alt_classification") for m in d["members"])


def count_judgment_calls(*groups):
    """Derived, never hardcoded. The provenance statement names this number, and
    a stale count there is a false claim about what Steffany reviewed."""
    return sum(1 for g in groups for d in g for m in d["members"] if m.get("judgment_call"))


def load_day():
    return json.load(open(ROOT / "day_chart_reference.json", encoding="utf-8"))


def bar(pct, label, sub="", is_own=False, n=None):
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
            f' data-agency="{html.escape(label)}"{f" data-n={n}" if n else ""}>{text}</i>'
        )
    cls = "row own" if is_own else "row"
    subhtml = f'<span class="sub">{html.escape(sub)}</span>' if sub else ""
    return (
        f'<div class="{cls}"><div class="rowlab">{html.escape(label)}{subhtml}</div>'
        f'<div class="track" style="--total:{total}">' + "".join(cells) + "</div></div>"
    )


def build_chart(agencies, day, comparison):
    """Every row carries the date it was verified. Day's sixteen are March 2026
    and were not re-verified here; the rows researched for this site are August."""
    parts = []
    for region in day["regions"]:
        parts.append(f'<div class="region"><h4>{html.escape(region["region"])}'
                     f'<span class="rcount">{len(region["agencies"])} agencies · '
                     f'Day · Mar 2026</span></h4>')
        for a in region["agencies"]:
            parts.append(bar(a["pct"], a["name"], n=a.get("n")))
        parts.append("</div>")
    parts.append(f'<div class="region new"><h4>Latin America'
                 f'<span class="rcount">{len(agencies)} agencies · this research · '
                 f'Aug 2026</span></h4>')
    for d in agencies:
        parts.append(bar(d["pct"], d["city"], sub=d["country"], is_own=True,
                         n=len(d["members"])))
    parts.append("</div>")
    parts.append(f'<div class="region new"><h4>Chicago'
                 f'<span class="rcount">{len(comparison)} agency · this research · '
                 f'Aug 2026</span></h4>')
    for d in comparison:
        parts.append(bar(d["pct"], d["agency_short"], sub=d["country"], is_own=True,
                         n=len(d["members"])))
        # Both readings are published rather than one being asserted. The second
        # row is the same twenty people under Day's applied practice.
        if has_alt(d):
            _, apct = alt_counts(d)
            parts.append(bar(apct, d["agency_short"], sub="under Day's applied practice",
                             is_own=True, n=len(d["members"])))
    parts.append("</div>")
    return "".join(parts)


def build_legend():
    return "".join(
        f'<span class="key"><i class="sw s{i}"></i>{html.escape(SHORT[c])}</span>'
        for i, c in enumerate(CATEGORIES)
    )


def build_hero(agencies):
    """Every board member as a single mark, grouped by agency.

    The whole dataset fits above the fold, and the finding reads straight off
    it: the community-advocate colour never appears.
    """
    rows = []
    for d in agencies:
        dots = []
        for cat_i, cat in enumerate(CATEGORIES):
            for _ in range(d["counts"].get(cat, 0)):
                dots.append(f'<i class="dot s{cat_i}" title="{html.escape(cat)}"></i>')
        seats = (f'{len(d["members"])}/{d["seats_total"]}'
                 if d.get("seats_total") and d["seats_total"] != len(d["members"])
                 else str(len(d["members"])))
        rows.append(
            f'<div class="hrow"><span class="hname">{html.escape(d["city"])}'
            f'<em>{html.escape(d["country"])}</em></span>'
            f'<span class="dots">{"".join(dots)}</span>'
            f'<span class="hn">{seats}</span></div>'
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
            # A judgment call is a classification that could defensibly have gone the
            # other way. The reasoning is published beside it rather than buried.
            jc = ('<a class="jc" href="analysis.html#judgment-calls" '
                  'title="This classification could reasonably have gone the other way. '
                  'Read what was weighed.">judgment call</a>') if m.get("judgment_call") else ""
            alt = ""
            if m.get("day_alt_classification"):
                basis = m.get("day_alt_basis", "")
                alt = ('<span class="altcat">Under Day\'s applied practice: <b>'
                       + html.escape(SHORT[m["day_alt_classification"]]) + "</b>"
                       + (" — " + html.escape(basis) if basis else "") + "</span>")
            note = ('<span class="jcnote">' + html.escape(m["classification_note"]) + "</span>"
                    if m.get("classification_note") else "")
            # Announced is not the same as seated. Where a seat is still pending a
            # confirmation vote, the row says so rather than implying it is filled.
            cstat = ('<span class="cstat">' + html.escape(m["confirmation_status"]) + "</span>"
                     if m.get("confirmation_status") else "")
            rows.append(
                f'<tr data-agency="{html.escape(d["city"])}"'
                f' data-cat="{html.escape(m["classification"])}"'
                f' data-conf="{html.escape(conf)}">'
                f'<td class="tname" data-label="Member">{html.escape(m["name"])}</td>'
                f'<td data-label="Agency">{html.escape(d["city"])}</td>'
                f'<td class="tpos" data-label="Position">{html.escape(m.get("position",""))}'
                f'{cstat}</td>'
                f'<td class="tcat" data-label="Classification"><i class="sw s{cat_i}"></i>'
                f'{html.escape(SHORT[m["classification"]])}{jc}</td>'
                f'<td data-label="Confidence"><span class="conf c{html.escape(conf.lower())}">'
                f'{html.escape(conf)}</span></td>'
                f'<td class="tsrc" data-label="Sources">{srcs or "—"}</td>'
                f'<td class="trat" data-label="Rationale"><details open>'
                f'<summary>Why this classification</summary>'
                f'{html.escape(m.get("rationale",""))}{note}{alt}</details></td></tr>'
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
.altcat{display:block; margin-top:7px; padding-top:7px; border-top:1px dotted var(--rule);
  font-size:12px; line-height:1.5; color:var(--ink2)}
.cstat{display:block; margin-top:5px; font-size:11.5px; line-height:1.45; color:var(--ink3)}
.mgh{margin:38px 0 6px}
.mgroup[hidden]{display:none}
.row.own .rowlab{font-weight:800; color:var(--ink)}
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
.trat details{display:block} .trat summary{display:none}
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
.jc{display:inline-block; margin-left:7px; padding:1px 6px; border-radius:99px; font-family:'JetBrains Mono',monospace; font-size:9.5px; letter-spacing:.06em; text-transform:uppercase; border:1px solid var(--s1); color:var(--s1); white-space:nowrap; vertical-align:1px}
.jcnote{display:block; margin-top:7px; padding-top:7px; border-top:1px dashed var(--rule); color:var(--ink3); font-size:12.5px; line-height:1.5}
.lede .jc{margin-left:2px}
.conf{font-family:'JetBrains Mono',monospace; font-size:10.5px; letter-spacing:.06em; text-transform:uppercase; padding:2px 7px; border-radius:99px; border:1px solid var(--rule); color:var(--ink2); white-space:nowrap}
.chigh{border-color:var(--ink2); color:var(--ink)}
.clow{border-color:var(--s2); color:var(--s2)}

/* ---- headline result cards on the front page ------------------------ */
.cards{display:grid; grid-template-columns:repeat(auto-fit,minmax(248px,1fr)); gap:2px; background:var(--rule); border:1px solid var(--rule); border-radius:3px; overflow:hidden}
.card{background:var(--panel); padding:24px 22px 22px}
.cardnum{display:block; font-size:44px; line-height:.95; letter-spacing:-.03em; color:var(--s0)}
.cardlab{display:block; margin:8px 0 12px; font-family:'JetBrains Mono',monospace; font-size:10.5px; letter-spacing:.13em; text-transform:uppercase; color:var(--ink3)}
.card p{margin:0; font-size:15.5px; line-height:1.55; color:var(--ink2)}

/* ---- site nav & cross-page provenance strip ------------------------- */
nav.site{border-bottom:1px solid var(--rule); background:var(--panel); position:sticky; top:0; z-index:40}
nav.site .wrap{display:flex; gap:4px; align-items:center; padding-top:0; padding-bottom:0; flex-wrap:wrap}
nav.site a{
  display:block; padding:14px 14px; text-decoration:none; color:var(--ink2);
  font-family:'JetBrains Mono',monospace; font-size:11px; letter-spacing:.11em;
  text-transform:uppercase; border-bottom:2px solid transparent; margin-bottom:-1px;
}
nav.site a:hover{color:var(--ink)}
nav.site a[aria-current]{color:var(--ink); border-bottom-color:var(--ink)}
nav.site .home{font-family:Archivo,sans-serif; font-variation-settings:'wdth' 112; font-weight:800; font-size:14px; letter-spacing:-.01em; text-transform:none; padding-right:20px}
.strip{background:var(--panel); border-bottom:1px solid var(--rule)}
.strip .wrap{padding-top:14px; padding-bottom:14px}
.strip p{margin:0; font-size:14.5px; color:var(--ink2); line-height:1.5; max-width:75ch}
.strip strong{color:var(--ink)}
.pagehead{padding:44px 0 0}
.pagehead h1{margin:8px 0 0; font-size:clamp(30px,5vw,52px)}
.pagehead .lede{margin-top:14px}

/* ---- responsive tables: stack into labelled cards, never scroll sideways ---- */
@media (max-width:760px){
  .scroll{overflow-x:visible}
  table.stack, #members{min-width:0; width:100%; background:transparent}
  table.stack thead, #members thead{position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap}
  table.stack tr, #members tbody tr{
    display:block; background:var(--panel); border:1px solid var(--rule);
    border-radius:4px; padding:4px 2px; margin:0 0 12px;
  }
  table.stack td, #members tbody td{
    display:block; border:0; border-bottom:1px solid var(--rule2);
    padding:9px 13px; width:auto; max-width:none; font-size:15px;
  }
  table.stack tr td:last-child, #members tbody tr td:last-child{border-bottom:0}
  table.stack td::before, #members tbody td::before{
    content:attr(data-label); display:block; margin-bottom:4px;
    font-family:'JetBrains Mono',monospace; font-size:9.5px;
    letter-spacing:.09em; text-transform:uppercase; color:var(--ink3);
  }
  table.stack td:empty{display:none}
  .tname{font-size:16px}
  .trat,.tpos{width:auto}
  .controls{position:sticky; top:47px; z-index:30; background:var(--paper); padding:10px 0; margin:0 0 14px}
  .controls select,.controls input{flex:1 1 100%}
  .trat summary{
    display:block; cursor:pointer; color:var(--s0); font-size:13px;
    font-family:'JetBrains Mono',monospace; letter-spacing:.03em; padding:2px 0;
  }
  .trat details[open] summary{margin-bottom:7px}
  .tsrc a{margin:0 5px 5px 0}
  .controls{position:static; padding:0}
  nav.site a{padding:12px 10px; font-size:10px}
  nav.site .home{padding-right:10px; font-size:13px}
}

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
      var n=s.dataset.n?' of '+s.dataset.n+' seats':'';
      show(e,'<b>'+s.dataset.agency+'</b>'+s.dataset.cat+' — '+s.dataset.pct+'%'+n);
    });
    s.addEventListener('mousemove',move);
    s.addEventListener('mouseleave',function(){tip.style.opacity=0;});
  });
  document.querySelectorAll('.dot').forEach(function(d){
    d.addEventListener('mouseenter',function(e){show(e,d.getAttribute('title'));});
    d.addEventListener('mousemove',move);
    d.addEventListener('mouseleave',function(){tip.style.opacity=0;});
  });

  if(matchMedia('(max-width:760px)').matches){
    document.querySelectorAll('.trat details[open]').forEach(function(d){d.removeAttribute('open');});
  }

  // Two tables (Latin America, NITA) kept deliberately separate so no total is
  // ever computed across both. The filters span them; the counts do not merge.
  var tbls=[].slice.call(document.querySelectorAll('table.mtable'));
  if(!tbls.length) return;
  var groups=tbls.map(function(t){
    return {tbl:t, body:t.tBodies[0], rows:[].slice.call(t.tBodies[0].rows),
            box:t.closest('.mgroup')};
  });
  var all=groups.reduce(function(a,g){return a.concat(g.rows);},[]);
  var fa=document.getElementById('f-agency'), fc=document.getElementById('f-cat'),
      fq=document.getElementById('f-q'), out=document.getElementById('f-count');
  function apply(){
    var a=fa.value, c=fc.value, q=(fq.value||'').toLowerCase().trim(), n=0;
    groups.forEach(function(g){
      var shown=0;
      g.rows.forEach(function(r){
        var ok=(!a||r.dataset.agency===a)&&(!c||r.dataset.cat===c)&&
               (!q||r.textContent.toLowerCase().indexOf(q)>-1);
        r.hidden=!ok; if(ok){shown++; n++;}
      });
      if(g.box) g.box.hidden = shown===0;
    });
    out.textContent=n+' of '+all.length+' members';
  }
  [fa,fc].forEach(function(el){el.addEventListener('change',apply);});
  fq.addEventListener('input',apply);
  groups.forEach(function(g){
    [].slice.call(g.tbl.tHead.rows[0].cells).forEach(function(th,i){
      th.addEventListener('click',function(){
        var desc=th.getAttribute('aria-sort')==='ascending';
        [].slice.call(g.tbl.tHead.rows[0].cells).forEach(function(o){o.removeAttribute('aria-sort');});
        th.setAttribute('aria-sort',desc?'descending':'ascending');
        g.rows.sort(function(x,y){
          var p=x.cells[i].textContent.trim(), q2=y.cells[i].textContent.trim();
          return (desc?-1:1)*p.localeCompare(q2,'es');
        });
        g.rows.forEach(function(r){g.body.appendChild(r);});
      });
    });
  });
  apply();
})();
"""


PROVENANCE = """<h2>How this was made — read before citing</h2>
<p>The board rosters and classifications on this page were <strong>researched and
written by Claude (Anthropic's AI)</strong>, from agency filings, official gazettes,
and regulatory disclosures. The classifications are <strong>Claude's judgment</strong>
applied to Richard Day's five categories — not an official designation by any agency.</p>
<p>The research was done in <strong>March 2026</strong> and then <strong>independently
re-verified and fully re-researched on 27 August 2026</strong>. That second pass found
real errors in the first, including two biographies attributed to the wrong people. They
are documented in the methodology section below rather than quietly removed.</p>
<p>The <strong>NITA board</strong> was researched separately on 27 August 2026 from the
appointing authorities' own announcements. Richard Day
<a href="https://citythatworks.substack.com/p/lets-grade-some-nita-appointments" rel="noopener">graded
these appointments</a> on the same day, but he <strong>did not classify them into his five
categories</strong> — so the NITA classifications here are Claude's, not his. Five of the
twenty seats are the Governor's appointees and were <strong>still awaiting Illinois Senate
confirmation</strong> when this was published; that status is recorded on each member's row.</p>
<p><strong>Steffany Bahamon adjudicated the __JC__ classification calls that could
reasonably have gone either way</strong>, and each is flagged on this page. Beyond those,
this has <strong>not been verified line by line</strong>. Every member record carries a
confidence rating and its source links, so any individual claim can be checked. Treat
medium- and low-confidence rows as leads, not findings.</p>
<p>Board composition changes fast — four of the five Latin American boards replaced members
within five months, and the entire Chicago regional system was reorganised in the same
period. These rosters are current as of 27 August 2026 and will go stale.</p>"""

NAV = """<nav class="site"><div class="wrap">
  <a class="home" href="index.html">Who runs Latin America's metros</a>
  <a href="index.html"__C_INDEX__>The findings</a>
  <a href="members.html"__C_MEMBERS__>The members</a>
  <a href="analysis.html"__C_ANALYSIS__>Full analysis</a>
</div></nav>"""

# Deep links land on members.html or analysis.html without passing the masthead,
# so the provenance travels with them.
STRIP = """<div class="strip"><div class="wrap"><p>
<strong>AI-assisted research.</strong> These rosters and classifications were researched
and written by Claude (Anthropic's AI), verified 27 August 2026, and are Claude's judgment
applied to Richard Day's categories — not an official designation by any agency. Day
published the categories and graded the NITA appointments, but did not classify them; those
calls are Claude's. __JC__ classification calls were adjudicated by Steffany Bahamon and are
flagged individually.
<a href="index.html#how-this-was-made">Read the full statement</a>.
</p></div></div>"""

SHELL = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<meta name="description" content="__DESC__">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="__DESC__">
<link rel="icon" href="__FAVICON__">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..125,400..800&family=Newsreader:ital,opsz,wght@0,6..72,300..700;1,6..72,300..600&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>__CSS__</style>
</head><body>
<div id="tip" role="status" aria-live="polite"></div>
__NAV__
__BODY__
<footer><div class="wrap">
  <p><strong>Source data and code:</strong>
  <a href="https://github.com/sbahamon/latam-transit-analysis" rel="noopener">github.com/sbahamon/latam-transit-analysis</a>.
  The five JSON files in <code>data/</code> are the source of truth; these pages are
  generated from them by <code>build_site.py</code>; <code>data_chicago/</code> holds the
  NITA board. The March 2026 rosters this supersedes are archived in
  <code>data_2026_03/</code>.</p>
  <p>Framework and the sixteen comparison agencies: Richard Day,
  <a href="https://citythatworks.substack.com/p/who-should-lead-our-transit-agencies" rel="noopener">“Put real experts in charge of transit”</a>
  and
  <a href="https://citythatworks.substack.com/p/lets-grade-some-nita-appointments" rel="noopener">“Let's grade some NITA appointments”</a>,
  A City That Works.
  Research by Claude, edited by Steffany Bahamon. MIT licensed.</p>
</div></footer>
<script>__JS__</script>
</body></html>
"""

INDEX_BODY = """
<header class="mast"><div class="wrap">
  <p class="eyebrow">Addendum · A City That Works</p>
  <h1 class="title dsp">Who runs Latin&nbsp;America's metros</h1>
  <p class="standfirst">Richard Day found that the world's best transit systems are run by
  boards of transit experts, and the worst by boards of politicians. He measured sixteen
  agencies across Asia, Europe and the United States. He measured none in Latin America.
  This is that missing column: <strong>__N__ board members, five agencies, five countries.</strong>
  Alongside them sits the board that prompted the question in Chicago: <strong>all __NITA_N__
  members of the new NITA</strong>, classified the same way and verified the same day.</p>
  <div class="byline">
    <span class="eyebrow">Research by Claude (AI)</span>
    <span class="eyebrow">Edited by Steffany Bahamon</span>
    <span class="eyebrow">Rosters verified 27 Aug 2026</span>
  </div>
  <div class="prov" id="how-this-was-made">__PROV__</div>
</div></header>

<main>
<section><div class="wrap">
  <div class="sechead"><h2 class="sec dsp">Every seat on every board</h2></div>
  <p class="lede">One mark per board member, coloured by category. The whole dataset,
  before any averaging.</p>
  <div class="hero">
    __HERO__
    <div class="legend" style="margin:20px 0 0;padding:16px 0 0;border-top:1px solid var(--rule2);border-bottom:0">__LEGEND__</div>
    <div class="herofoot">
      <span class="zero dsp">0</span>
      <span class="zerolab">community advocates among all __N__ <strong>Latin American</strong>
      board members. Not one seat, in any of the five agencies, in either the March or the
      August roster. In Day's US sample the same category runs as high as 50%, and Chicago's
      new NITA board has one — so this is a Latin American pattern, not a universal one.</span>
    </div>
  </div>
</div></section>

<section><div class="wrap">
  <div class="sechead"><h2 class="sec dsp">A fourth region on Day's chart</h2></div>
  <p class="lede">The five Latin American agencies placed alongside Day's sixteen, same
  five categories, same measure — plus Chicago's new NITA board, the comparison that
  prompted the question. Hover any segment for the exact figure. Note the dates: the rows
  researched here are August 2026, Day's are March.</p>
  <div class="chartbox">
    <div class="legend">__LEGEND__</div>
    __CHART__
    __CAPTION__
  </div>
</div></section>

<section><div class="wrap">
  <div class="sechead"><h2 class="sec dsp">What the data shows</h2></div>
  <div class="cards">__FINDINGS__</div>
  <p class="lede" style="margin-top:30px">The evidence for all of this is the
  <a href="members.html">member-by-member table</a>, and the reasoning is in the
  <a href="analysis.html">full analysis</a>.</p>
</div></section>
</main>
"""

MEMBERS_BODY = """
__STRIP__
<main><div class="wrap">
  <div class="pagehead">
    <p class="eyebrow">The evidence</p>
    <h1 class="dsp">The __N__ members, and NITA&#8217;s __NITA_N__</h1>
    <p class="lede">Every classification with its rationale, confidence rating and sources.
    If a claim on this site matters to you, check it here. Rows marked
    <span class="jc">judgment call</span> could reasonably have been classified the other
    way; the rationale says what was weighed.</p>
  </div>
  <div class="controls">
    <select id="f-agency"><option value="">All agencies</option>__OPT_AGENCY__</select>
    <select id="f-cat"><option value="">All categories</option>__OPT_CAT__</select>
    <input id="f-q" type="search" placeholder="Search names, roles, rationale…" aria-label="Search members">
    <span class="count" id="f-count"></span>
  </div>
  <div class="mgroup">
    <h2 class="sec dsp mgh">Latin America · __N__ members</h2>
    <p class="lede">The five agencies this study is about. Rosters verified 27 August 2026.</p>
    <div class="scroll"><table id="members" class="stack mtable">
      <thead><tr><th>Member</th><th>Agency</th><th>Position</th><th>Classification</th>
      <th>Confidence</th><th>Sources</th><th>Rationale</th></tr></thead>
      <tbody>__ROWS__</tbody>
    </table></div>
  </div>
  <div class="mgroup">
    <h2 class="sec dsp mgh">Chicago · NITA · __NITA_N__ members</h2>
    <p class="lede">The comparison board, verified the same day. Richard Day graded these
    appointments but did not classify them, so these classifications are Claude's rather than
    his. The Governor's five appointees were still awaiting Illinois Senate confirmation;
    each row says where it stands. These members are counted separately and are
    <strong>not</strong> part of the __N__-member Latin American totals anywhere on this site.</p>
    <div class="scroll"><table id="members-nita" class="stack mtable">
      <thead><tr><th>Member</th><th>Agency</th><th>Position</th><th>Classification</th>
      <th>Confidence</th><th>Sources</th><th>Rationale</th></tr></thead>
      <tbody>__NITA_ROWS__</tbody>
    </table></div>
  </div>
</div></main>
"""

ANALYSIS_BODY = """
__STRIP__
<main><div class="wrap narrow">
  <div class="pagehead">
    <p class="eyebrow">The argument</p>
    <h1 class="dsp">Full analysis</h1>
    <p class="lede">The complete write-up, including the corrections made to the March 2026
    version and the seven classification calls that could have gone either way.</p>
  </div>
  <div class="prose">__PROSE__</div>
</div></main>
"""

FAVICON = ("data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%20"
           "viewBox%3D%270%200%2016%2016%27%3E%3Crect%20width%3D%2716%27%20height%3D%2716%27%20"
           "rx%3D%272%27%20fill%3D%27%23fcfcfb%27/%3E%3Crect%20x%3D%272%27%20y%3D%273%27%20"
           "width%3D%2712%27%20height%3D%272.4%27%20rx%3D%27.6%27%20fill%3D%27%23488fe6%27/%3E"
           "%3Crect%20x%3D%272%27%20y%3D%276.8%27%20width%3D%2712%27%20height%3D%272.4%27%20"
           "rx%3D%27.6%27%20fill%3D%27%23ca6a10%27/%3E%3Crect%20x%3D%272%27%20y%3D%2710.6%27%20"
           "width%3D%278%27%20height%3D%272.4%27%20rx%3D%27.6%27%20fill%3D%27%23733b97%27/%3E%3C/svg%3E")


CAPTION = """<p class="chartnote"><strong>Every row carries its own date, and they are not
    all the same date.</strong> The sixteen Asian, European and US rows are Richard Day's
    work, <strong>as of March 2026</strong>, computed from the
    <a href="https://docs.google.com/spreadsheets/d/12KmU7QuP1y_RL8nuinrsIOYETISfXiLqXqi0EtSa_1Y/edit?gid=0" rel="noopener">member-level list he published</a>
    alongside
    <a href="https://citythatworks.substack.com/p/who-should-lead-our-transit-agencies" rel="noopener">“Put real experts in charge of transit”</a>
    (A City That Works, March 2026) — 222 board members — rather than read off his chart
    image. They have not been re-verified here.</p>
    <p class="chartnote"><strong>His four Chicago rows describe a system that has since been
    reorganised.</strong> The RTA is being wound up and replaced by NITA, and the CTA, Metra
    and Pace boards were re-appointed in July and August 2026. Those four rows are kept here
    as Day published them, as the pre-reform baseline — not as a description of who governs
    Chicago transit today. New CTA, Metra and Pace rows are deliberately <em>not</em>
    published: more service-board appointments were still outstanding at the time of writing,
    and a board that cannot be confirmed to its full seat list does not get a row on this
    site.</p>
    <p class="chartnote">The five Latin American rows and the NITA row are computed from the
    member records on this site and are current as of <strong>27 August 2026</strong>. Two of
    Day's rows sum to 99% or 101% from rounding; one figure differs from his published chart,
    where LTA Singapore's other-management share is 76% in his data (13 of 17 seats) but
    labelled 77%. Chart rebuilt, not reproduced.</p>"""


def build_findings(agencies, total, counts):
    """The headline results, so the front page carries the conclusions itself
    rather than making people read the whole analysis to reach them."""
    other = pct(counts.get("Other Management/Policy", 0), total)
    transit = pct(counts.get("Transit Ops/Management", 0), total)
    items = [
        ("0", "community advocates in Latin America",
         f"Across {total} Latin American members, five agencies, five countries and two rounds "
         "of research five months apart, not one seat belongs to a rider advocate or community "
         "organisation. In Day's US sample the same category reaches 50%. Chicago's new NITA "
         "board, counted separately below, has one."),
        (f"{other}%", "generalist managers",
         "Finance people, lawyers, career civil servants and non-transit engineers. Higher "
         "than any single region in Day's dataset, and the profile held steady even as the "
         "boards themselves turned over."),
        (f"{transit}%", "transit operations experts",
         f"{counts.get('Transit Ops/Management', 0)} of {total} members. Three of those six "
         "rest on judgment calls that could have gone the other way — under the stricter "
         "reading this figure is 7%, which is why it is published with its workings."),
        ("2 of 20", "NITA directors with transit operations experience",
         "Chicago's new regional board replaced the RTA in 2026. Under the classification "
         "rules used throughout this site, two of its twenty directors have transit "
         "operations experience, and only one of those is unambiguous. Under Richard Day's "
         "looser applied practice the figure is five. Both readings are published, because "
         "the difference is the whole argument."),
        ("4 of 5", "Latin American boards changed since March",
         "Santiago replaced its entire board; Medellín, São Paulo and Buenos Aires each "
         "replaced or lost members. The aggregate composition barely moved, which suggests "
         "structure rather than appointments determines who governs transit."),
    ]
    return "".join(
        f'<div class="card"><span class="cardnum dsp">{html.escape(n)}</span>'
        f'<span class="cardlab">{html.escape(lab)}</span>'
        f'<p>{html.escape(body)}</p></div>'
        for n, lab, body in items
    )


def render(body, title, desc, current):
    page = (SHELL
            .replace("__CSS__", CSS)
            .replace("__JS__", JS)
            .replace("__NAV__", NAV)
            .replace("__BODY__", body)
            .replace("__TITLE__", title)
            .replace("__DESC__", desc)
            .replace("__FAVICON__", FAVICON))
    for key in ("INDEX", "MEMBERS", "ANALYSIS"):
        page = page.replace(f"__C_{key}__", ' aria-current="page"' if key == current else "")
    return page


def main():
    agencies = load_agencies()
    comparison = load_comparison()
    day = load_day()
    total, counts = build_composite(agencies)
    # Deliberate: 42 across the 2026-08-27 rosters (Medellin carries 2 vacant seats).
    # Update when data/ changes, so a silent roster edit cannot slip through unnoticed.
    if total != 42:
        raise SystemExit(f"expected 42 members, found {total} — update this check if data/ changed")
    # Same guard for the Chicago cohort: NITA is a 20-seat board, 5 each from the
    # Governor, Cook County, Chicago and the collar counties. Update if data_chicago/ changes.
    nita_total = sum(len(d["members"]) for d in comparison)
    if nita_total != 20:
        raise SystemExit(f"expected 20 NITA members, found {nita_total} — update this "
                         "check if data_chicago/ changed")
    # Derived, so the provenance line can never claim a number Steffany did not review.
    jc = count_judgment_calls(agencies, comparison)

    prose = markdown_to_html(ANALYSIS.read_text(encoding="utf-8"))
    opt_agency = "".join(
        f'<option value="{html.escape(d["city"])}">{html.escape(d["city"])}</option>'
        for d in sorted(agencies + comparison, key=lambda x: x["city"])
    )
    opt_cat = "".join(
        f'<option value="{html.escape(c)}">{html.escape(SHORT[c])}</option>'
        for c in CATEGORIES
    )

    pages = {
        "index.html": (
            render(INDEX_BODY
                   .replace("__PROV__", PROVENANCE)
                   .replace("__HERO__", build_hero(agencies))
                   .replace("__CHART__", build_chart(agencies, day, comparison))
                   .replace("__CAPTION__", CAPTION)
                   .replace("__FINDINGS__", build_findings(agencies, total, counts))
                   .replace("__LEGEND__", build_legend()),
                   "Who Runs Latin America's Metros",
                   "Board composition for five major Latin American metro agencies, "
                   "classified with Richard Day's framework, sourced and confidence-rated.",
                   "INDEX")),
        "members.html": (
            render(MEMBERS_BODY
                   .replace("__STRIP__", STRIP)
                   .replace("__ROWS__", build_table(agencies))
                   .replace("__NITA_ROWS__", build_table(comparison))
                   .replace("__OPT_AGENCY__", opt_agency)
                   .replace("__OPT_CAT__", opt_cat),
                   f"The {total} Members · Who Runs Latin America's Metros",
                   f"All {total} Latin American board members plus the {nita_total} NITA "
                   "appointees, with classification, rationale, confidence and sources.",
                   "MEMBERS")),
        "analysis.html": (
            render(ANALYSIS_BODY
                   .replace("__STRIP__", STRIP)
                   .replace("__PROSE__", prose),
                   "Full Analysis · Who Runs Latin America's Metros",
                   "The complete write-up, including corrections to the March 2026 version "
                   f"and the {jc} classification judgment calls.",
                   "ANALYSIS")),
    }

    for name, page in pages.items():
        page = (page.replace("__NITA_N__", str(nita_total))
                    .replace("__N__", str(total))
                    .replace("__JC__", str(jc)))
        leaks = verify_no_markdown_leaked(page)
        if leaks:
            raise SystemExit(f"{name}: markdown leaked — " + "; ".join(leaks))
        left = re.findall(r"__[A-Z_]+__", page)
        if left:
            raise SystemExit(f"{name}: unfilled placeholders — " + ", ".join(sorted(set(left))))
        (ROOT / name).write_text(page, encoding="utf-8")
        print(f"wrote {name:16s} {len(page):>8,} bytes")

    print(f"\n  {total} members, {len(agencies)} LatAm agencies + "
          f"{sum(len(r['agencies']) for r in day['regions'])} from Day"
          f" + {nita_total} NITA ({len(comparison)} agency, this research)")
    for c in CATEGORIES:
        print(f"  {c:26s} {counts.get(c,0):2d}  {pct(counts.get(c,0), total):3d}%")
    print(f"\n  NITA, kept out of the composite above:")
    for d in comparison:
        for i, c in enumerate(CATEGORIES):
            print(f"  {c:26s} {d['counts'].get(c,0):2d}  {d['pct'][i]:3d}%")
    print(f"\n  {jc} judgment calls across both cohorts")


if __name__ == "__main__":
    main()
