---
name: pbi-report-design
description: Design and build executive-grade Power BI reports in PBIR (PBIP) as text - designed page backgrounds, transparent visuals, KPI tiles with sparklines, dynamic insight text, dark/light twin pages - and validate them before opening Desktop. Use when the user wants a dashboard redesigned, made "professional", given a dark or light mode, or built from scratch as PBIP files.
---

# Power BI report design (PBIR)

The tooling lives in `tools/pbip-builder/` (README there). Run `setup.sh` once, then `build.sh`; look at the previews in `tools/pbip-builder/.cache/previews/` before handing anything over.

## Design system

- **Canvas:** 1920×1080 pages, `displayOption: FitToPage`. 8px grid. Left nav rail 96px; content x=128 to 1880 (12 columns of 124px, 24px gutters); header 0–120px; KPI tiles from y=136 (200px tall with a sparkline); panels from y=360 to 1048.
- **Palettes** (validated with the dataviz skill's `validate_palette.js`, `--pairs all`, against the real surface):
  - Dark: canvas `#0A0E17`, rail `#0E1421`, panel `#131A28`, border `#212B3E`, grid `#222C3F`, text `#F3EFE7` / `#9AA3B5`, accent text `#D9B97A`, series `#BF9640` / `#6A86C9` / `#1FA38C`, up `#4CC38A`, down `#F2706C`, amber `#E0B04C`, grey `#8B93A7`.
  - Light: canvas `#F3EFE8`, rail `#FBF9F5`, panel `#FFFFFF`, border `#E4DDD2`, grid `#ECE6DC`, text `#1E2230` / `#5B6273`, accent text `#8A6A2A`, series `#97701F` / `#4466AD` / `#00876A`, up `#1E7F4F`, down `#C23B33`, amber `#9A6700`, grey `#6B7280`.
  - One accent (gold) for the main series; prior year in steel; target in teal, dashed. Bars that compare named items use one colour.
- **Fonts and type scale:** KPI values DIN 28pt (theme `card.labels.fontFamily`); KPI change text Segoe UI Semibold 11pt; insight text Segoe UI 11pt; axis labels 11pt; data labels and legends 10pt (legend `Top`, i.e. top-left). Panel titles 18px and subtitles 13px are drawn in the background. Text baked into backgrounds uses Inter (OFL), because Segoe UI isn't available on Linux and Selawik isn't on npm.
- **Numbers:** data labels use auto display units with 1 decimal (`labelDisplayUnits 0D`, `labelPrecision 1L`); ratios use 2 decimals.

## Workflow

1. **Backgrounds:** draw each page as SVG (rail with icons and the active item, header, rounded panels with border and soft shadow, tile icons, panel titles, insight lead-ins). Render to a 3840×2160 JPEG at quality 90 with Playwright Chromium (about 300 KB each; PNG was about 1.1 MB). Register them in `report.json` under the `RegisteredResources` package with `type: Image`, files under `StaticResources/RegisteredResources/`. Set the page `objects.background` to `image.image{name, url: ResourcePackageItem{PackageName RegisteredResources, PackageType 1, ItemName}, scaling 'Fit'}`, transparency `0D`, and `objects.outspace` colour = canvas.
2. **Transparent visuals:** a custom theme (registered as `CustomTheme` next to the base theme) sets `visualStyles["*"]["*"]` background, border, dropShadow and title off, padding 0, plus axis, legend, label and tooltip styles. Visuals sit exactly on the drawn panels: the visual area is `(x+16, y+80, w-32, h-96)`.
3. **Dark/light:** twin pages from one spec with two palettes.
   - A sun/moon `actionButton` (PageNavigation) goes to the twin page, and the nav rail links within the same mode.
   - Light pages have `visibility: HiddenInViewMode`.
   - Slicers carry `syncGroup {groupName, fieldChanges, filterChanges}` so filters persist across pages.
   - The theme defaults to dark, so every visual also sets its own colours for its mode (axes, legend, labels, table and matrix colours, slicer items, tooltip, header).
4. **KPI tile recipe (tile 200px):**
   - Icon chip and an uppercase label drawn in the background.
   - Classic `card` for the value (60px tall, DIN 28).
   - Classic `card` for the change text (30px tall, 11pt), coloured by a measure returning hex (`labels.color = {solid:{color:{expr:{Measure}}}}`). Use a separate colour measure per mode.
   - Small `lineChart` sparkline (38px; axes, legend and header off; `strokeWidth 2L`; series colour = accent).
   - The change text comes from a label measure, e.g. "▲ 18.9%  vs PY 7.6M" built with `UNICHAR(9650/9660)`.
5. **Insights:** one measure per sentence (e.g. TOPN/CONCATENATEX to name the weakest region). Show each in a classic `card` with `wordWrap` on and Segoe UI 11pt, at least 45px tall for 2 lines. The bold lead-in and bulb icon are drawn in the background. Put at most 3 per panel.
6. **Latest-year rule:** with no year selected, KPIs show the latest year vs the year before (`CALCULATE(x, KEEPFILTERS('Date'[Year] = MAX('Date'[Year])))` and the PY version through `SAMEPERIODLASTYEAR`), so tiles are never blank.
7. **Validate** with `build.sh`. Run `themeprops.py` before guessing any formatting property name.

## Pitfalls found the hard way

- The new card (`cardVisual`) rendered in Desktop as a solid dark box showing the measure name and no value, even on light pages. Use the classic `card` with `categoryLabels.show false`, a transparent container and an explicit label colour.
- Values clip when a card is short: give at least 60px for a 28pt value and 30px for an 11pt line with padding 0.
- Waterfall category labels rotate when the visual is narrow: give it at least ~100px per category (5 columns for 7 bars).
- The Filters pane is open by default. Set `report.json` `objects.outspacePane` to `expanded false, visible false` (the property is in the report schema).
- Theme schema validation checks types and enums but not unknown property names; `check_props.py` does.
- With sort-by columns (e.g. Month sorted by Month Number), any `ALLSELECTED` used to scale a heatmap must include the sort columns too.
- The schemas don't validate formatting expressions (measure-driven colours, data bars, images); confirm those visually in Desktop.
- Desktop needs Ctrl+click on buttons while editing; reading view doesn't.
- Never edit files while the project is open in Desktop; never commit `.pbi/localSettings.json` or `.pbi/cache.abf`.
