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
eye toward the Northern Illinois Transit Authority (NITA) replacing Chicago's RTA.

Those NITA appointments have now been made, so **the 20-member NITA board is included as its
own agency**, classified the same way and verified the same day as the Latin American
rosters. Day
[graded the appointments](https://citythatworks.substack.com/p/lets-grade-some-nita-appointments)
(A City That Works, 27 August 2026) but did not classify them into his five categories, so
the NITA classifications here are Claude's. NITA is a **comparison row and is excluded from
the 42-member Latin American composite** — it is the comparator, not the subject.

**Rosters are current as of 27 August 2026** — 42 Latin American members in `data/`, plus
the 20 NITA members in `data_chicago/`. An earlier March 2026 snapshot is archived in
`data_2026_03/`; the March version contained errors serious enough to change its headline
findings, and they are documented in the analysis under Methodology.

**On dates.** Every row in the chart carries the date it was verified, and they are not all
the same. Day's sixteen agencies are as of March 2026 and have not been re-verified here.
His four Chicago rows are kept as he published them, as the **pre-reform baseline**: the RTA
is being wound up, and the CTA, Metra and Pace boards were re-appointed in July and August
2026. New rows for those three service boards are deliberately not published — more
appointments were still outstanding, and a board that cannot be confirmed to its full seat
list does not get a row here (the same call made earlier for TransMilenio and Empresa Metro
de Bogotá).

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
| `index.html` | Published site: findings, chart, provenance. **Generated** — edit `build_site.py`, not this. |
| `members.html` | Published site: the member-by-member table. Generated. |
| `analysis.html` | Published site: the full write-up. Generated. |
| `data/*.json` | Source of truth: one file per agency, 42 member records, verified 2026-08-27 |
| `data_chicago/*.json` | The Chicago comparison cohort: NITA's 20 members, verified 2026-08-27 |
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

Records in `data_chicago/` add two fields: `agency_short` (the chart row label) and a
per-member `confirmation_status`, because an announced appointment is not a seated one —
the Governor's five NITA appointees still required Illinois Senate confirmation when this
was published, and each row says so.

## Rebuilding

```sh
python3 build_site.py                      # regenerates index.html (stdlib only)
pip install openpyxl && python3 create_spreadsheet.py   # regenerates the xlsx
```

`build_site.py` emits three pages that share one stylesheet and script, and asserts **both**
member counts so a silent roster edit cannot slip through: 42 for `data/` and 20 for
`data_chicago/`. If you change either directory, update the matching check. The number of
judgment calls quoted in the provenance statement is derived from the data rather than
hardcoded, because that sentence names what Steffany personally reviewed. Tables carry `data-label` on every cell so they stack into labelled cards below 760px
rather than scrolling sideways. `judgment_call` and `classification_note` are
optional per-member fields — where present they render as a visible marker and an
explanation on the site.

Edit the JSON, rerun, commit. The site is served by GitHub Pages from `main` at the
repository root.

## Credit

The comparison chart on the site includes Day's 16 agencies alongside the five studied
here and the NITA board. Those 16 rows and the five-category framework are his work,
computed from the
[member-level list](https://docs.google.com/spreadsheets/d/12KmU7QuP1y_RL8nuinrsIOYETISfXiLqXqi0EtSa_1Y/edit?gid=0)
he published alongside
[“Put real experts in charge of transit”](https://citythatworks.substack.com/p/who-should-lead-our-transit-agencies)
(222 board members), not read off his chart image.

One figure differs from his published chart: LTA Singapore's other-management share is
76% in his data (13 of 17 seats) where the chart labels it 77%. `day_chart_reference.json`
follows the data. Every other figure in it was re-checked against his sheet during the NITA
work and matched exactly, including all four Chicago agencies (44 members).

His NITA piece states that transit-operations experience across these boards rose "from 8%
to 18%". The 8% is not reproducible from his own published data, which gives 4 of 44 Chicago
seats (9%) counting the RTA, or 1 of 30 (3%) without it. His 18% is treated here as external
corroboration, not as a target to match.

## License

MIT — see [LICENSE](LICENSE).
