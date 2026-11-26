# PowerBI_Report

This repository holds Power BI Desktop reports, ideally saved as Power BI projects (`.pbip`) so the semantic model (TMDL) and report (PBIR) are plain text under version control.

- For any Power BI task (DAX, modeling, Power Query, visuals, PBIP files, performance, documentation), use the `powerbi-desktop` agent in `.claude/agents/powerbi-desktop.md`.
- Skills: `dax-measure`, `model-review`, `power-query`, `model-docs`, `pbi-report-design` (in `.claude/skills/`). Build and validation tooling for PBIP projects: `tools/pbip-builder/`.
- Live access to an open Power BI Desktop file goes through the `powerbi-modeling` MCP server configured in `.mcp.json` (Windows only; see `README.md`).
- Do not edit PBIP files while the same file is open in Power BI Desktop, and never commit `.pbi/cache.abf` or `.pbi/localSettings.json`.
- Reply to the user in the language they write in (usually Arabic); keep code and object names in English.
