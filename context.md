# LatAm Transit Board Research — Claude Code Prompt

## Context

Richard Day's "A City That Works" Substack published [Put real experts in charge of transit](https://citythatworks.substack.com/p/who-should-lead-our-transit-agencies) (March 2026), analyzing transit board composition across Asia, Europe, and the US. The chart (see `transit_board_chart.png` in this directory) categorizes every board member of 16 agencies into five buckets:

1. **Transit Ops/Management** — significant experience managing transit operations or capital projects
2. **Other Management/Policy** — complementary skills: finance, IT, law, public policy, engineering (non-transit)
3. **Labor Representative** — designated labor/union seat
4. **Community Advocate** — rider advocates, demographic group representatives, community orgs
5. **Elected Official** — current or recently-retired elected officials without other qualifying experience

The piece argues Asian/European boards are loaded with transit experts and engineers while US boards are dominated by community advocates and elected officials — and that this explains much of the performance gap.

**The gap**: The analysis only covers Asia, Europe, and the US. No Latin American agencies are included. We want to fill that gap.

## Objective

Research the **board/directorio/junta directiva** of these five LatAm transit agencies, identify every current member, classify them using Day's five categories, produce a spreadsheet for spot-checking, and write an analysis.

## Target Agencies

| Agency | City | Country | Governance Type |
|---|---|---|---|
| **Metro de Santiago (Metro S.A.)** | Santiago | Chile | State-owned corporation, 7-member board appointed by national government |
| **Metro de Medellín (Empresa de Transporte Masivo del Valle de Aburrá)** | Medellín | Colombia | Mixed-ownership company, 9-member board (national + regional + city seats) |
| **STC Metro (Sistema de Transporte Colectivo)** | Mexico City | Mexico | Decentralized public body of CDMX government — may not have a traditional board; research the Consejo de Administración or equivalent governing body |
| **Metrô de São Paulo (Companhia do Metropolitano de São Paulo)** | São Paulo | Brazil | State-owned company (São Paulo state), Conselho de Administração + Diretoria |
| **SBASE (Subterráneos de Buenos Aires)** | Buenos Aires | Argentina | City-owned state enterprise, Directorio appointed by GCBA |

## Known Starting Points

These URLs and facts were verified in prior research — use them as starting points, but verify everything is still current.

### Metro de Santiago
- Governance page: `https://www.metro.cl/gobierno-corporativo/informacion-del-directorio-y-del-personal`
- CMF filings (Chilean securities regulator): `https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=61219000&tipoentidad=EMPUB&vig=VI&control=svs&pestania=46`
- 7-member board, all appointed by national government via shareholder meeting

### Metro de Medellín
- Board page: `https://www.metrodemedellin.gov.co/en/who-we-are/corporate-governance/board-of-directors`
- 9 seats with structurally-assigned roles (mix of national, regional, and city government appointees plus presidential independents) — research the exact seat allocation
- Board composition may have changed with political cycles; verify current membership

### STC Metro (CDMX)
- Structure page: `https://www.metro.cdmx.gob.mx/secretaria/estructura/1`
- Research whether STC has a Consejo de Administración, a traditional board, or a different governance model entirely
- If no board exists, document the top leadership team (DG + subdirectors) and note the governance model — this is itself a finding

### Metrô de São Paulo
- Governance page: `https://governancacorporativa.metrosp.com.br/Paginas/Conselho-de-Administra%C3%A7%C3%A3o.aspx`
- It's publicly traded (ADR on NYSE) — SEC EDGAR filings (6-K, 20-F) contain governance data
- Also try `diariodotransporte.com.br` for recent board change coverage
- Search in Portuguese

### SBASE (Buenos Aires)
- News source with good SBASE coverage: `https://enelsubte.com/noticias/category/subte/sbase/`
- City-owned state enterprise, Directorio appointed by GCBA (Buenos Aires city government)
- Board composition changes with city political cycles; verify current membership

## Research Instructions

For **each board member**, collect:

1. **Full name**
2. **Agency**
3. **Position on board** (President, VP, Director, etc.)
4. **How appointed** (elected official ex officio, national government, state/city government, employee rep, etc.)
5. **Professional background** — education, career history, key roles
6. **Classification** (one of the 5 Day categories)
7. **Classification rationale** — 1-2 sentences explaining why
8. **Source URL(s)** for the bio/background info
9. **Confidence level** (High / Medium / Low) — how sure are you about the classification?

### Classification Rules (match Day's methodology)

- **Transit Ops/Management**: Person has **significant direct experience** managing transit systems, rail/bus operations, or transit capital projects. Transit engineering professors count. Urban planners with transit focus count. General civil engineers do NOT count unless they worked in transit.
- **Other Management/Policy**: Finance executives, lawyers, IT leaders, non-transit engineers, public policy experts, management consultants. Government planning officials who are not elected go here.
- **Labor Representative**: Explicitly designated employee/union representative seat.
- **Community Advocate**: Rider advocacy orgs, demographic group representatives, community organizations. NOT the same as "community advocate who is also a finance executive" — use primary background.
- **Elected Official**: Current or recently-retired mayors, governors, legislators, council members sitting on the board *in their capacity as elected officials*. Political party operatives who have held elected office also go here. Government planning directors who serve ex officio as delegates of elected officials are tricky — classify them as Other Management/Policy if they have professional planning credentials, Elected Official if they're pure political appointees.

### Important Nuances

- **Search in Spanish/Portuguese**. Most of these agencies publish in their national language. Use Spanish-language searches for Santiago, Medellín, CDMX, Buenos Aires. Use Portuguese for São Paulo.
- **LinkedIn is your friend** for individual bios when agency websites are thin.
- **Annual reports (memorias anuales / relatórios anuais)** often have the most detailed board member bios.
- **SEC filings** for São Paulo Metrô (it trades as an ADR).
- **Verify currency**. LatAm boards change with political cycles. A board composition from 2023 may be stale.

## Deliverables

### 1. Spreadsheet (`latam_transit_boards.xlsx`)

Create an Excel file with two sheets:

**Sheet 1: "Board Members"** — One row per board member with columns:
- Agency
- City
- Country
- Member Name
- Position
- Appointment Method
- Professional Background (brief)
- Education
- Day Classification
- Classification Rationale
- Source URL
- Confidence Level
- Date Verified

**Sheet 2: "Agency Summary"** — One row per agency with columns:
- Agency
- City
- Country
- Board Size
- % Transit Ops/Management
- % Other Management/Policy
- % Labor Representative
- % Community Advocate
- % Elected Official
- Governance Model (brief description)
- Notes

### 2. Analysis (`latam_transit_board_analysis.md`)

Write a markdown analysis that:

1. Summarizes findings per agency — governance model, board composition, classification breakdown
2. Compares LatAm agencies to the patterns in Day's chart (Asia heavy on transit experts, Europe mixed, US heavy on elected officials/advocates — where do LatAm agencies fall on this spectrum?)
3. Surface any surprising findings, paradoxes, or notable patterns — e.g., mismatches between system reputation and board expertise, unusual governance structures, agencies that defy the regional pattern, or cases where the governance model itself is the story
4. Identifies which LatAm agencies most closely resemble which Asian/European/US agencies in Day's chart, and which don't fit neatly into any existing pattern
5. Suggests implications for the NITA governance reform in Chicago (the new Northern Illinois Transit Authority replacing the RTA, with new board appointments coming in 2026)
6. Flags uncertainties, low-confidence classifications, and areas needing further verification

## Agent Team Setup (if using swarms)

This task is a great fit for agent teams because each agency is an independent research unit.

### Recommended team structure:

```
Team Lead: Orchestrates research, handles synthesis and final analysis
├── Agent Santiago: Research Metro de Santiago board members + bios
├── Agent Medellín: Research Metro de Medellín board members + bios  
├── Agent CDMX: Research STC Metro governance structure + leadership
├── Agent SãoPaulo: Research Metrô de São Paulo Conselho + bios
└── Agent BuenosAires: Research SBASE directorio + bios
```

### To enable agent teams:

```bash
# Add to your Claude Code settings.json:
# "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"

# Or set as environment variable:
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# For split-pane visibility (recommended), use tmux:
tmux new-session -s transit-research

# Then run claude code inside the tmux session:
claude
```

### Prompt for the team lead:

```
Spawn 5 research agents, one per transit agency. Each agent should:
1. Search for the current board/directorio composition (search in Spanish/Portuguese)
2. For each member, find their professional background via LinkedIn, annual reports, news articles
3. Classify each member using Day's 5 categories (rules are in the prompt file)
4. Write findings to a per-agency JSON file in /home/user/transit-research/data/

After all agents complete, synthesize the data into:
- An xlsx spreadsheet (using openpyxl with uv)
- A markdown analysis document

Reference the full research prompt at: latam_transit_board_research.md
```

## Notes

- **uv for Python**: Use `uv` for all Python scripts (e.g., `uv run --with openpyxl script.py`)
- The reference chart image is at `transit_board_chart.png` — include it in the analysis for context
- This is intended as an addendum to Day's piece for the "A City That Works" Substack — keep the tone analytical and data-driven
- The person running this (Steffany) has housing policy advocacy experience with AHIL in Chicago and is familiar with the NITA governance reform context