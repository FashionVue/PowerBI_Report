---
name: power-query
description: Write, fix or optimize Power Query (M) for the Power BI model — cleaning and shaping data, merges, appends, unpivots, parameters, custom functions and query-folding problems. Use when the user asks about data import, transformation, refresh errors or slow refresh.
---

# Power Query (M)

Delegate to the `powerbi-desktop` agent and follow these steps.

1. **Find the query.** Read its M from the PBIP (`*.SemanticModel/definition/tables/<Table>.tmdl`, the `partition ... = m` block, or `expressions.tmdl` for shared queries and parameters) or from the live model through MCP. Identify the source type (SQL, Excel, CSV, SharePoint, web) because it decides what can fold.
2. **Write or change the M** following the agent's Power Query standards: filter and remove columns early, keep folding, meaningful step names, explicit types once, parameters for paths/servers, no credentials in code.
3. **Explain folding.** For SQL-type sources, say which steps fold and which step (if any) breaks folding, and propose a reordering or a native query when it matters.
4. **Deliver** the full `let ... in` expression in a code block. When editing PBIP files, keep the TMDL indentation of the partition block exact and remind the user to close Desktop before the edit and to refresh after reopening. When working live, remind the user that a refresh is needed to see the new data.

## Refresh errors

Read the error text, find the failing step, and check the usual causes in order: changed source column names, type conversion errors (`DataFormat.Error`), privacy-level / firewall errors (`Formula.Firewall`) when combining sources, credentials or gateway, and file paths that only exist on one machine.
