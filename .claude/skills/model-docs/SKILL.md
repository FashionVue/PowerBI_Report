---
name: model-docs
description: Generate documentation for the Power BI model — tables, columns, relationships, measures with their DAX and business meaning, RLS roles and data sources — and optionally write missing measure descriptions back to the model. Use when the user asks to document, describe or explain the model or report.
---

# Model documentation

Delegate to the `powerbi-desktop` agent.

1. Read the full model (live via MCP or from the PBIP `definition/` folder).
2. Write `docs/model.md` (create the folder if needed) in the user's language, with:
   - **Overview:** purpose of the report, data sources, refresh notes, a relationship diagram as a Mermaid `erDiagram`.
   - **Tables:** one section per table — role (fact / dimension / measures / parameter), row grain, key columns, visible columns with a one-line meaning.
   - **Measures:** grouped by display folder — name, business definition in plain language, DAX in a code block, format.
   - **Security:** RLS roles and their filter expressions.
   - **Known issues:** anything odd you noticed (link the user to the `model-review` skill for a full audit).
3. List measures that have no description, propose a description for each, and **only after the user approves** write them into the model (via MCP, or into the `///` description lines in TMDL with Desktop closed).
