# pbip-builder

Scripts that generate Power BI projects (TMDL model + PBIR report) as text and check them before they ever reach Power BI Desktop. One pipeline builds any project folder under `projects/`:

| Project | Output | Notes |
|---|---|---|
| `salessample` | `SalesSample.pbip` | English, left-to-right, FashionVue identity (navy + gold), 6 pages × dark/light |
| `vehicles` | `VehicleSales.pbip` | Arabic, right-to-left, Tajawal font, Masar Horizon identity (graphite + teal/orange), cover + 5 sections + conclusion × dark/light |

Each project folder holds `project.conf` (name, data generator, workbook, theme file), `build_model.py`, `build_report.py`, `render.js` (backgrounds) and `expected_values.py`. Shared code: `pbitmdl.py` (TMDL writer used by `vehicles`) and the validators in this folder.

## Setup (once per machine)

Requirements: Python 3 (`pip install jsonschema openpyxl`), Node 18+ with `playwright` and its Chromium (`npm i -g playwright && npx playwright install chromium`), and the .NET 8 SDK for the TMDL check.

```bash
tools/pbip-builder/setup.sh
```

It downloads into `tools/pbip-builder/.cache/` (git-ignored): the Fabric PBIR/PBIP JSON schemas (from github.com/microsoft/json-schemas), Microsoft's report theme schema (from github.com/microsoft/powerbi-desktop-samples), the lucide-static icons (ISC licence), `@microsoft/powerquery-parser`, and it builds the TMDL checker (`Microsoft.AnalysisServices` TmdlSerializer).

## Build and check

Close the project in Power BI Desktop first; Desktop doesn't pick up file edits while it's open.

```bash
tools/pbip-builder/build.sh salessample          # model + report + every check
tools/pbip-builder/build.sh vehicles --data      # also regenerate data/VehicleSales.xlsx
```

The `vehicles` backgrounds need Tajawal installed for Chromium: `mkdir -p ~/.fonts && cp fonts/*.ttf ~/.fonts && fc-cache -f`.

| Step | Script | What it does |
|---|---|---|
| Model | `projects/<p>/build_model.py` | Writes all TMDL (tables, Power Query, relationships, ~200 measures); lineage tags are uuid5 of the object path, so they're stable |
| TMDL check | `tmdlcheck/` | Loads the folder with TmdlSerializer and re-saves it; the canonical output is copied back |
| M check | `extract_m.py` + `mparse/check.js` | Parses every partition query with Microsoft's Power Query parser |
| Report | `projects/<p>/build_report.py` | One spec → 6 pages × Dark/Light twin pages, theme, `layout.json` |
| Layout check | `check_layout.py` | No overlapping visuals; every visual sits on a drawn panel |
| Backgrounds | `projects/<p>/render.js` | SVG → 3840×2160 JPEG per page and mode, plus labelled preview PNGs in `.cache/previews/` |
| JSON schemas | `validate_json.py` | Every PBIR/PBIP JSON file against its `$schema` |
| Formatting names | `check_props.py` | Every object/property name in the theme and visuals against the official theme schema |
| Cross-check | `crosscheck.py` | Fields used by visuals exist in the model, selectors match queries, navigation targets and resources exist |
| Expected values | `projects/<p>/expected_values.py` | Recomputes KPIs from the workbook in Python to compare with the report |

Helpers: `themeprops.py <themeSchema> <visualType> [object]` lists the formatting objects and properties a visual supports; `fetch_schemas.py` mirrors more schema versions.

Open the previews after every build and look at them. The checks catch format errors, not ugly layouts.

## Adapting to another dashboard

1. Copy a project folder (`vehicles` is the cleaner template: it uses `pbitmdl.py`). Replace `build_model.py` with your tables (or keep a Desktop-made model and skip that step).
2. In `build_report.py`, keep the `Page` helpers (`tile`, `panel`, `insights`, `card`, `sparkline`, `button`, `header`) and rewrite `build()` for your pages. Positions use the 12-column grid (`cx`, `span`).
3. Change the palettes in `PAL` and validate them with the dataviz skill's `validate_palette.js` for both surfaces.

See `.claude/skills/pbi-report-design/SKILL.md` for the design system and the pitfalls behind these choices.
