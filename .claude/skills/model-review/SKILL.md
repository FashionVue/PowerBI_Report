---
name: model-review
description: Audit the Power BI semantic model against modeling, DAX and performance best practices and return a prioritized list of fixes. Use when the user asks to review, audit, check or clean up a model, or asks why a report is slow or large.
---

# Model review

Delegate to the `powerbi-desktop` agent. The review is **read-only**: make no changes until the user picks which fixes to apply.

## Steps

1. Connect (live Desktop via MCP, or read the PBIP `definition/` folder) and collect:
   - tables with row counts, column counts and, if available, size / cardinality of the largest columns;
   - all relationships (cardinality, cross-filter direction, active / inactive);
   - all measures with their expressions, format strings, display folders and descriptions;
   - calculated columns and calculated tables;
   - date table(s) and whether they are marked; Auto date/time setting;
   - RLS roles; Power Query sources and parameters.
2. Check each area:
   - **Schema:** star schema? snowflaked dimensions? facts joined to facts? many-to-many or bi-directional relationships?
   - **Size:** unused or high-cardinality columns, date-time columns that should be split, text keys, Auto date/time on.
   - **DAX:** `FILTER` over whole tables inside `CALCULATE`, `/` instead of `DIVIDE`, missing variables for repeated expressions, iterators over large facts, `IFERROR`, measures without format strings / folders / descriptions, duplicated logic.
   - **Usability:** visible foreign keys, numeric columns that will auto-sum, inconsistent naming, implicit measures, missing descriptions.
   - **Power Query:** steps that break folding, hard-coded paths or servers, staging queries loaded to the model.
   - **Security:** RLS on fact tables instead of dimensions, roles never tested.
3. Report as a table per priority — **Critical**, **Recommended**, **Nice to have** — with columns *Object*, *Problem*, *Fix*. Start with a 3–5 line summary of the model's overall health.
4. Offer to apply the fixes the user selects, grouped so each batch can be confirmed and validated on its own.
