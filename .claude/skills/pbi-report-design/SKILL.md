---
name: pbi-report-design
description: Design and build executive-grade Power BI reports in PBIR (PBIP) as text - designed page backgrounds, transparent visuals, KPI tiles with sparklines, dynamic insight text, dark/light twin pages - and validate them before opening Desktop. Use when the user wants a dashboard redesigned, made "professional", given a dark or light mode, or built from scratch as PBIP files.
---

# Power BI report design (PBIR)

The tooling lives in `tools/pbip-builder/` (README there). Run `setup.sh` once, then `build.sh <project>` (e.g. `salessample`, `vehicles`); look at the previews in `tools/pbip-builder/.cache/previews/` before handing anything over.

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

## Arabic and right-to-left reports (learned on VehicleSales)

Template: `tools/pbip-builder/projects/vehicles/` (`build.sh vehicles`).

- **Names:** keep TMDL object names in English. Everything the reader sees is Arabic:
  - Arabic data values.
  - Arabic month and day names in Date (with Month Number / Day of Week Number sort columns).
  - `displayName` on every projection (axis, legend and column titles).
  - Arabic DAX text for labels, insights and recommendations.
  - Western digits, with units written as "مليون"/"ألف" by label measures.
- **Mirrored layout:**
  - Nav rail on the right (x 1824–1920); content x=40 to 1792. Use a right-anchored grid helper `rx(col_from_right, span)`.
  - The most important KPI sits on the right, and the title is right-aligned.
  - Header controls go on the left: mode, year, branch, comparison.
- **Charts in RTL:**
  - Horizontal bars: set `valueAxis.invertAxis true` and `categoryAxis.switchAxisPosition true`, so categories sit on the right and bars grow to the left (both properties are in the schema).
  - Time axes stay left-to-right.
  - Tables are laid out left-to-right, so list projections in reverse order (name column ends up rightmost), set `columnFormatting.alignment 'Right'` on the name column and `columnHeaders.alignment 'Right'`, and use `dataBars.reverseDirection true`.
- **Font (Tajawal):**
  - Take the TTFs from the npm package `@expo-google-fonts/tajawal` (OFL font, MIT wrapper).
  - Ship Regular/Medium/Bold/ExtraBold plus `OFL.txt` in `fonts/` next to the `.pbip`, and tell users to install them for all users before opening.
  - Theme: `textClasses.fontFace` and every visual-style `fontFamily` set to "Tajawal". Don't use comma lists in the theme (the format is strict). Card labels also get a visual-level literal `'Tajawal'`.
  - Desktop falls back silently if the font isn't installed. The Power BI Service shows a fallback font unless the viewer has it installed.
- **Arabic in the backgrounds:**
  - Install the TTFs into `~/.fonts` and run `fc-cache`.
  - In SVG use `direction="rtl"` with `text-anchor="start"` for right-aligned text.
  - Chromium shapes Arabic correctly. Numeric ranges such as "2023-2025" display as 2025-2023 inside an RTL run, which reads correctly (2023 first) for Arabic readers.
  - Verify every page visually.
- **Cover and conclusion pages:**
  - Cover: a hero block (title, company, period chip, purpose statement, 4 all-years headline cards from measures with `REMOVEFILTERS('Date')`) and a table of contents whose rows are PageNavigation buttons.
  - Conclusion: dynamic findings (insight measures), numbered recommendations (measures with numbers in the text), static next steps drawn in the background, and a back-to-cover button.
  - They are first and last in `pageOrder`.
- **Identity:** a new brand needs new palettes validated in both modes (`validate_palette.js --pairs all`). Shapes drive the feel too: an angled corner cut, small radii, speed-line motifs and a blueprint grid read "automotive"; large radii and soft glows read "luxury fashion".
- **Insight panels:** the lead-in and bulb icon (or a number for recommendations) go on the right. With the classic card the text is centred; give each sentence at least 58px.

## Bidi, animated SVG and button states (learned on VehicleSales v2)

- **Bidi.** Classic cards lay text out with a left-to-right base, so mixed Arabic + numbers + % + arrows come out jumbled. In DAX:
  - Wrap every Arabic string in `UNICHAR(8295)` (RLI) … `UNICHAR(8297)` (PDI).
  - Wrap every number group (`FORMAT(...)` result, with its %) in `UNICHAR(8294)` (LRI) … PDI.
  - Put the arrow first, so it lands on the right.
  - `projects/vehicles/build_model.py` does this automatically for every label, insight and recommendation measure.
  - Check by rendering the strings in Chromium under both `dir="ltr"` (centred) and `dir="rtl"`; the check script is `v2checks/bidi.js` in the session scratchpad.
- **Arabic values.** For money tiles show a text measure such as `"244.8 مليون"` (bidi-wrapped). It returns `"لا توجد بيانات للفترة"` when blank, which is the empty state. On the cover, print the unit in the label line ("مليون ريال") so the value stays short and never truncates.
- **SVG sparklines** (replace tiny line charts; native ones rendered as grey stubs):
  - A measure with `dataCategory: ImageUrl` returns `"data:image/svg+xml;utf8,<svg …>"`, with `#` written as `%23` and only single quotes inside.
  - Monthly points come from `ADDCOLUMNS(VALUES('Date'[Month Number]), "@v", VAR m = … RETURN CALCULATE(base, REMOVEFILTERS('Date'), Year = latest, Month = m))`, joined into a path with `CONCATENATEX`.
  - Show it in a one-column `tableEx`: projection `displayName " "`; header font 8 in the panel colour; `grid.imageWidth/imageHeight` (e.g. 240×28); no grid; value back colours = panel colour.
- **Animation (SMIL inside the SVG, plays on load and on every filter change):**
  - Line draw-in: `pathLength='1' stroke-dasharray='1' stroke-dashoffset='1'` with `<animate attributeName='stroke-dashoffset' from='1' to='0' dur='1.1s' fill='freeze' calcMode='spline' keySplines='0.25 0.8 0.25 1'/>`.
  - Area fade-in, then the end dot pops (`r` 0 → 3.2).
  - RTL bullet bar: animate `width` and `x` together so the bar grows from the right; the target is a thin marker.
  - Give elements with delayed animations `opacity='0'` so they don't flash before they start.
  - Only one infinite motion: a subtle pulse.
  - Capture frames at 0/400/1200/2600 ms to prove the animation runs and ends in the right state.
- **Button states.** `@microsoft/powerbi-core-visual-schema` (MIT, `data/instance-selectors.json`) lists actionButton states `default/hover/selected/disabled` for fill, outline, text and icon. Transparent nav buttons over drawn icons get `fill.show true` plus `fillColor` = accent with `transparency` 100 (default) / 84 (hover) / 72 (selected).
- **Skipped (not validatable here):**
  - Report-page tooltips, drill-through pages and bookmarks/overlays: their PBIR shapes weren't confirmable from a schema or a Desktop-saved sample.
  - The image visual's `sourceType` / `sourceField` enum values.
  - Translating the slicer's "All" text.
