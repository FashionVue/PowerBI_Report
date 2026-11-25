---
name: dax-measure
description: Write, fix or optimize a DAX measure for the Power BI model and validate it against the data. Use when the user asks for a new measure (e.g. YoY growth, running total, % of total, YTD), reports a wrong number, or wants a slow measure rewritten.
---

# DAX measure

Delegate the work to the `powerbi-desktop` agent and have it follow these steps.

1. **Understand the request.** Restate the business definition in one line (what is counted, over which period, with which filters). Ask if anything is ambiguous, for example fiscal vs calendar year, or whether returns are included.
2. **Inspect the model.** Find the fact table, the date table (and whether it is marked), the relevant relationships, and existing base measures to reuse (e.g. reuse `[Total Sales]` instead of re-summing the column).
3. **Write the measure** following the DAX standards in the agent prompt: `VAR`/`RETURN`, `DIVIDE`, column filters in `CALCULATE`, format string, display folder, description.
4. **Validate.** Run a DAX query that slices the measure by a meaningful dimension (year, month, category), compare with a base measure or a hand calculation, and show the result table. Check blanks, totals, and the first period (where previous-period measures return blank).
5. **Deliver** the final DAX in a code block, a two-line explanation, and where it was created (table / display folder). If you could not create or validate it live, say so and give the user the steps to paste it in Desktop (Modeling → New measure).

## Patterns to reach for

```dax
-- % of total, respecting other filters
Sales % of Category =
VAR _Sales = [Total Sales]
VAR _All   = CALCULATE ( [Total Sales], REMOVEFILTERS ( 'Product'[Product Name] ) )
RETURN DIVIDE ( _Sales, _All )

-- Year over year growth
Sales YoY % =
VAR _Current = [Total Sales]
VAR _PY      = CALCULATE ( [Total Sales], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )
RETURN IF ( NOT ISBLANK ( _PY ), DIVIDE ( _Current - _PY, _PY ) )

-- Running total over dates
Sales Running Total =
VAR _MaxDate = MAX ( 'Date'[Date] )
RETURN
    CALCULATE ( [Total Sales], 'Date'[Date] <= _MaxDate, REMOVEFILTERS ( 'Date' ) )
```

Adapt table and column names to the actual model; never paste these unchanged.
