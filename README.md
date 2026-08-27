# Latin American Transit Board Composition

**Live site: https://sbahamon.github.io/latam-transit-analysis/**

Board composition for five major Latin American metro agencies — Metro de Santiago,
Metro de Medellín, STC Metro (Mexico City), Metrô de São Paulo, and SBASE/SBASAU (Buenos
Aires) — classified using the five-category framework from Richard Day's
["Put real experts in charge of transit"](https://citythatworks.substack.com/p/who-should-lead-our-transit-agencies)
(A City That Works, March 2026).

Day's analysis covered 16 agencies across Asia, Europe, and the United States, and
found that boards dominated by transit-operations experts tend to run better systems.
It included no Latin American agencies. This repository is an addendum that runs the
same classification over every seat on those five boards and compares the result, with an
eye toward the Northern Illinois Transit Authority (NITA) board appointments replacing
Chicago's RTA in 2026.

**Rosters are current as of 27 August 2026** (42 members). An earlier March 2026 snapshot
is archived in `data_2026_03/`; the March version contained errors serious enough to change
its headline findings, and they are documented in the analysis under Methodology.

## How this was made — please read before citing

The board rosters and classifications here were **researched and written by Claude
(Anthropic's AI)** from agency filings, official gazettes, and regulatory disclosures. The
classifications are **Claude's judgment** applied to Day's five categories — not an
official designation by any agency.

The research was done in March 2026 and then **independently re-verified and fully
re-researched on 27 August 2026**. That second pass found real errors in the first,
including two biographies attributed to the wrong people. **Steffany Bahamon adjudicated
the seven classification calls that could reasonably have gone either way**; each is
flagged in the data (`judgment_call: true`) and on the site. Beyond those, this has **not**
been verified line by line.

Every member record carries a confidence rating and its source URLs, so any individual
claim can be checked. Treat medium- and low-confidence rows as leads, not findings. Board
composition changes fast — four of these five boards replaced members within five months.

## What's here

| Path | What it is |
|---|---|
| `index.html` | The published site. **Generated** — edit `build_site.py`, not this. |
| `data/*.json` | Source of truth: one file per agency, 42 member records, verified 2026-08-27 |
| `data_2026_03/*.json` | Archived March 2026 snapshot, kept for the longitudinal comparison |
| `latam_transit_board_analysis.md` | The full written analysis |
| `build_site.py` | Builds `index.html` from the JSON + the markdown. Standard library only. |
| `create_spreadsheet.py` | Builds the xlsx from the JSON. Requires `openpyxl`. |
| `latam_transit_boards.xlsx` | Generated spreadsheet: member-level sheet + agency summary |
| `day_chart_reference.json` | Day's 16 agencies, computed from his published member-level list |
| `transit_board_chart.png` | Richard Day's original chart, kept for reference. Not republished on the site. |

## Data shape

Each `data/<city>.json` is one object:

```json
{
  "agency": "...", "city": "...", "country": "...",
  "governance_model": "...", "board_size": 7,
  "date_verified": "2026-08-27", "notes": "...",
  "members": [
    {
      "name": "...", "position": "...", "appointment_method": "...",
      "background": "...", "education": "...",
      "classification": "Transit Ops/Management",
      "rationale": "...", "sources": ["https://..."],
      "confidence": "High",
      "judgment_call": true,
      "classification_note": "why this call could have gone the other way"
    }
  ]
}
```

`classification` is one of: `Transit Ops/Management`, `Other Management/Policy`,
`Labor Representative`, `Community Advocate`, `Elected Official`.

## Rebuilding

```sh
python3 build_site.py                      # regenerates index.html (stdlib only)
pip install openpyxl && python3 create_spreadsheet.py   # regenerates the xlsx
```

`build_site.py` asserts the member count so a silent roster edit cannot slip through; if
you change `data/`, update that check. `judgment_call` and `classification_note` are
optional per-member fields — where present they render as a visible marker and an
explanation on the site.

Edit the JSON, rerun, commit. The site is served by GitHub Pages from `main` at the
repository root.

## Credit

The comparison chart on the site includes Day's 16 agencies alongside the five studied
here. Those 16 rows and the five-category framework are his work, computed from the
[member-level list](https://docs.google.com/spreadsheets/d/12KmU7QuP1y_RL8nuinrsIOYETISfXiLqXqi0EtSa_1Y/edit?gid=0)
he published alongside
[“Put real experts in charge of transit”](https://citythatworks.substack.com/p/who-should-lead-our-transit-agencies)
(222 board members), not read off his chart image.

One figure differs from his published chart: LTA Singapore's other-management share is
76% in his data (13 of 17 seats) where the chart labels it 77%. `day_chart_reference.json`
follows the data.

## License

MIT — see [LICENSE](LICENSE).
