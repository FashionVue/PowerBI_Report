# Writes the VehicleSales semantic model (TMDL). Object names are English; everything the reader sees comes from
# Arabic data values, Arabic month/day names in Date, Arabic display names in the report and Arabic DAX text.
# Usage: python3 build_model.py <VehicleSales.SemanticModel/definition>
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from pbitmdl import Model, T, cy, py, growth, diff

m = Model(sys.argv[1], "masar-horizon-vehicles")
WB = "VehicleSales.xlsx"
I64, TXT, DT, NUM, CUR, LOG = "Int64.Type", "type text", "type date", "type number", "Currency.Type", "type logical"
col = m.column

# ------------------------------------------------------------------ Sales
S = "Sales"
sales_steps = [
    ("Added Stock Age Band", 'Table.AddColumn({prev}, "Stock Age Band", each if [DaysInStock] <= 30 then "حتى 30 يوماً" else if [DaysInStock] <= 60 then "31-60 يوماً" else if [DaysInStock] <= 90 then "61-90 يوماً" else "أكثر من 90 يوماً")'),
    ("Added Stock Age Order", 'Table.AddColumn({prev}, "Stock Age Order", each if [DaysInStock] <= 30 then 1 else if [DaysInStock] <= 60 then 2 else if [DaysInStock] <= 90 then 3 else 4)'),
    ("Added Price Band", 'Table.AddColumn({prev}, "Price Band", each if [SalePrice] < 75000 then "أقل من 75 ألف" else if [SalePrice] < 150000 then "75-150 ألف" else if [SalePrice] < 300000 then "150-300 ألف" else "أكثر من 300 ألف")'),
    ("Added Price Band Order", 'Table.AddColumn({prev}, "Price Band Order", each if [SalePrice] < 75000 then 1 else if [SalePrice] < 150000 then 2 else if [SalePrice] < 300000 then 3 else 4)'),
]
sales_types = [("DealID", I64), ("DealDate", DT), ("BranchID", I64), ("EmployeeID", I64), ("CustomerID", I64), ("VehicleID", I64), ("Condition", TXT),
               ("ListPrice", CUR), ("DiscountAmount", CUR), ("SalePrice", CUR), ("VehicleCost", CUR), ("PaymentType", TXT), ("FinancePartner", TXT),
               ("DownPayment", CUR), ("TermMonths", I64), ("FinanceCommission", CUR), ("AddOnRevenue", CUR), ("AddOnCost", CUR), ("TradeIn", LOG),
               ("TradeInValue", CUR), ("DaysInStock", I64), ("Stock Age Band", TXT), ("Stock Age Order", I64), ("Price Band", TXT), ("Price Band Order", I64)]
sales_cols = [col(S, "DealID", "int64", "0"), col(S, "DealDate", "dateTime", "Short Date", hidden=True, date_only=True)]
sales_cols += [col(S, k, "int64", "0", hidden=True) for k in ("BranchID", "EmployeeID", "CustomerID", "VehicleID")]
sales_cols += [col(S, "Condition", "string"), col(S, "ListPrice", "decimal", "#,##0", summarize="sum"), col(S, "DiscountAmount", "decimal", "#,##0", summarize="sum"),
               col(S, "SalePrice", "decimal", "#,##0", summarize="sum"), col(S, "VehicleCost", "decimal", "#,##0", summarize="sum"),
               col(S, "PaymentType", "string"), col(S, "FinancePartner", "string"), col(S, "DownPayment", "decimal", "#,##0", summarize="sum"),
               col(S, "TermMonths", "int64", "0"), col(S, "FinanceCommission", "decimal", "#,##0", summarize="sum"),
               col(S, "AddOnRevenue", "decimal", "#,##0", summarize="sum"), col(S, "AddOnCost", "decimal", "#,##0", summarize="sum"),
               col(S, "TradeIn", "boolean"), col(S, "TradeInValue", "decimal", "#,##0", summarize="sum"), col(S, "DaysInStock", "int64", "0"),
               col(S, "Stock Age Band", "string", sort_by="Stock Age Order"), col(S, "Stock Age Order", "int64", "0", hidden=True),
               col(S, "Price Band", "string", sort_by="Price Band Order"), col(S, "Price Band Order", "int64", "0", hidden=True)]
m.table(S, "Vehicle deals (one row per vehicle sold), 2023-2025.", sales_cols, m.excel(WB, "Sales", sales_steps, sales_types))

L = "Leads"
m.table(L, "Sales leads and test drives (funnel).",
        [col(L, "LeadID", "int64", "0"), col(L, "LeadDate", "dateTime", "Short Date", hidden=True, date_only=True), col(L, "Source", "string"),
         col(L, "BranchID", "int64", "0", hidden=True), col(L, "VehicleID", "int64", "0", hidden=True), col(L, "TestDrive", "boolean"),
         col(L, "Converted", "boolean"), col(L, "DealID", "int64", "0", hidden=True)],
        m.excel(WB, "Leads", [], [("LeadID", I64), ("LeadDate", DT), ("Source", TXT), ("BranchID", I64), ("VehicleID", I64), ("TestDrive", LOG),
                                  ("Converted", LOG), ("DealID", I64)]))
SV = "Service"
sv_steps = [("Added Turnaround Band", 'Table.AddColumn({prev}, "Turnaround Band", each if [TurnaroundHours] <= 24 then "حتى 24 ساعة" else if [TurnaroundHours] <= 48 then "24-48 ساعة" else if [TurnaroundHours] <= 72 then "48-72 ساعة" else "أكثر من 72 ساعة")'),
            ("Added Turnaround Order", 'Table.AddColumn({prev}, "Turnaround Order", each if [TurnaroundHours] <= 24 then 1 else if [TurnaroundHours] <= 48 then 2 else if [TurnaroundHours] <= 72 then 3 else 4)')]
m.table(SV, "After-sales service visits.",
        [col(SV, "VisitID", "int64", "0"), col(SV, "VisitDate", "dateTime", "Short Date", hidden=True, date_only=True)] +
        [col(SV, k, "int64", "0", hidden=True) for k in ("BranchID", "EmployeeID", "CustomerID", "VehicleID")] +
        [col(SV, "ServiceType", "string"), col(SV, "LaborRevenue", "decimal", "#,##0", summarize="sum"), col(SV, "PartsRevenue", "decimal", "#,##0", summarize="sum"),
         col(SV, "ServiceCost", "decimal", "#,##0", summarize="sum"), col(SV, "TurnaroundHours", "double", "0.0"),
         col(SV, "Turnaround Band", "string", sort_by="Turnaround Order"), col(SV, "Turnaround Order", "int64", "0", hidden=True),
         col(SV, "CSAT", "int64", "0"), col(SV, "IsComeback", "boolean")],
        m.excel(WB, "Service", sv_steps, [("VisitID", I64), ("VisitDate", DT), ("BranchID", I64), ("EmployeeID", I64), ("CustomerID", I64), ("VehicleID", I64),
                                          ("ServiceType", TXT), ("LaborRevenue", CUR), ("PartsRevenue", CUR), ("ServiceCost", CUR), ("TurnaroundHours", NUM),
                                          ("CSAT", I64), ("IsComeback", LOG), ("Turnaround Band", TXT), ("Turnaround Order", I64)]))
V = "Vehicles"
m.table(V, "Vehicle models by model year (car makes are real data values; no logos).",
        [col(V, "VehicleID", "int64", "0", hidden=True), col(V, "Make", "string"), col(V, "Model", "string"), col(V, "Vehicle", "string"),
         col(V, "Segment", "string", hidden=True), col(V, "Powertrain", "string"), col(V, "Origin", "string"), col(V, "ModelYear", "int64", "0"),
         col(V, "MSRP", "decimal", "#,##0"), col(V, "Cost", "decimal", "#,##0")],
        m.excel(WB, "Vehicles", [("Added Vehicle", 'Table.AddColumn({prev}, "Vehicle", each [Make] & " " & [Model])')],
                [("VehicleID", I64), ("Make", TXT), ("Model", TXT), ("Segment", TXT), ("Powertrain", TXT), ("Origin", TXT), ("ModelYear", I64),
                 ("MSRP", CUR), ("Cost", CUR), ("Vehicle", TXT)]))
BR = "Branches"
m.table(BR, "Showrooms and service centres.",
        [col(BR, "BranchID", "int64", "0", hidden=True), col(BR, "BranchName", "string"), col(BR, "City", "string"), col(BR, "Region", "string"),
         col(BR, "BranchType", "string"), col(BR, "OpenDate", "dateTime", "Short Date", date_only=True),
         col(BR, "MonthlyFixedCost", "decimal", "#,##0", hidden=True, desc="Monthly fixed overhead allocated to after-sales (absorption proxy).")],
        m.excel(WB, "Branches", [], [("BranchID", I64), ("BranchName", TXT), ("City", TXT), ("Region", TXT), ("BranchType", TXT), ("OpenDate", DT),
                                     ("MonthlyFixedCost", CUR)]))
E = "Employees"
m.table(E, "Sales consultants, service advisors and branch managers.",
        [col(E, "EmployeeID", "int64", "0", hidden=True), col(E, "EmployeeName", "string"),
         col(E, "BranchID", "int64", "0", hidden=True, desc="Home branch; not related to Branches to avoid a second filter path."),
         col(E, "Role", "string"), col(E, "HireDate", "dateTime", "Short Date", date_only=True)],
        m.excel(WB, "Employees", [], [("EmployeeID", I64), ("EmployeeName", TXT), ("BranchID", I64), ("Role", TXT), ("HireDate", DT)]))
C = "Customers"
m.table(C, "Customers (individuals, companies, government).",
        [col(C, "CustomerID", "int64", "0", hidden=True), col(C, "CustomerName", "string"), col(C, "Gender", "string"), col(C, "AgeGroup", "string"),
         col(C, "Nationality", "string"), col(C, "City", "string"), col(C, "Region", "string"), col(C, "CustomerType", "string"),
         col(C, "JoinDate", "dateTime", "Short Date", date_only=True)],
        m.excel(WB, "Customers", [], [("CustomerID", I64), ("CustomerName", TXT), ("Gender", TXT), ("AgeGroup", TXT), ("Nationality", TXT),
                                      ("City", TXT), ("Region", TXT), ("CustomerType", TXT), ("JoinDate", DT)]))
TG = "Targets"
m.table(TG, "Monthly revenue and unit targets by showroom and segment (first day of the month).",
        [col(TG, "Month", "dateTime", "Short Date", hidden=True, date_only=True), col(TG, "BranchID", "int64", "0", hidden=True),
         col(TG, "Segment", "string", hidden=True), col(TG, "RevenueTarget", "decimal", "#,##0", hidden=True, summarize="sum"),
         col(TG, "UnitsTarget", "int64", "0", hidden=True, summarize="sum")],
        m.excel(WB, "Targets", [], [("Month", DT), ("BranchID", I64), ("Segment", TXT), ("RevenueTarget", CUR), ("UnitsTarget", I64)]))
m.table("Segment", "Vehicle segment dimension shared by Vehicles and Targets.", [col("Segment", "Segment", "string")],
        ["let", f'{T}Source = Excel.Workbook(File.Contents(DataFolder & "{WB}"), null, true),',
         f'{T}#"Targets Table" = Source{{[Item="Targets",Kind="Table"]}}[Data],',
         f'{T}#"Kept Segment" = Table.Distinct(Table.SelectColumns(#"Targets Table", {{"Segment"}})),',
         f'{T}#"Set Column Types" = Table.TransformColumnTypes(#"Kept Segment", {{{{"Segment", type text}}}})', "in", f'{T}#"Set Column Types"'])
D = "Date"
AR_MONTHS = '{"يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"}'
AR_DAYS = '{"الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"}'
date_m = ["let", f"{T}StartDate = #date(2023, 1, 1),", f"{T}EndDate = #date(2025, 12, 31),", f"{T}ArabicMonths = {AR_MONTHS},", f"{T}ArabicDays = {AR_DAYS},",
          f'{T}#"Date List" = List.Dates(StartDate, Duration.Days(EndDate - StartDate) + 1, #duration(1, 0, 0, 0)),',
          f'{T}#"Date Table" = Table.FromList(#"Date List", Splitter.SplitByNothing(), {{"Date"}}),',
          f'{T}#"Added Year" = Table.AddColumn(#"Date Table", "Year", each Date.Year([Date])),',
          f'{T}#"Added Quarter" = Table.AddColumn(#"Added Year", "Quarter", each "الربع " & Text.From(Date.QuarterOfYear([Date]))),',
          f'{T}#"Added Month Number" = Table.AddColumn(#"Added Quarter", "Month Number", each Date.Month([Date])),',
          f'{T}#"Added Month" = Table.AddColumn(#"Added Month Number", "Month", each ArabicMonths{{Date.Month([Date]) - 1}}),',
          f'{T}#"Added Year Month Number" = Table.AddColumn(#"Added Month", "Year Month Number", each Date.Year([Date]) * 100 + Date.Month([Date])),',
          f'{T}#"Added Month Year" = Table.AddColumn(#"Added Year Month Number", "Month Year", each ArabicMonths{{Date.Month([Date]) - 1}} & " " & Text.From(Date.Year([Date]))),',
          f'{T}#"Added Day of Week Number" = Table.AddColumn(#"Added Month Year", "Day of Week Number", each Date.DayOfWeek([Date], Day.Sunday) + 1),',
          f'{T}#"Added Day Name" = Table.AddColumn(#"Added Day of Week Number", "Day Name", each ArabicDays{{Date.DayOfWeek([Date], Day.Sunday)}}),',
          f'{T}#"Added Is Weekend" = Table.AddColumn(#"Added Day Name", "Is Weekend", each Date.DayOfWeek([Date], Day.Sunday) >= 5),',
          f'{T}#"Set Column Types" = Table.TransformColumnTypes(#"Added Is Weekend", {{{{"Date", type date}}, {{"Year", Int64.Type}}, {{"Quarter", type text}}, {{"Month Number", Int64.Type}}, {{"Month", type text}}, {{"Year Month Number", Int64.Type}}, {{"Month Year", type text}}, {{"Day of Week Number", Int64.Type}}, {{"Day Name", type text}}, {{"Is Weekend", type logical}}}})',
          "in", f'{T}#"Set Column Types"']
m.table(D, "Calendar 2023-2025 with Arabic month and day names (week starts Sunday; Friday/Saturday weekend), marked as the date table.",
        [col(D, "Date", "dateTime", "Short Date", key=True, date_only=True), col(D, "Year", "int64", "0"), col(D, "Quarter", "string"),
         col(D, "Month Number", "int64", "0", hidden=True), col(D, "Month", "string", sort_by="Month Number"),
         col(D, "Year Month Number", "int64", "0", hidden=True), col(D, "Month Year", "string", sort_by="Year Month Number"),
         col(D, "Day of Week Number", "int64", "0", hidden=True), col(D, "Day Name", "string", sort_by="Day of Week Number"), col(D, "Is Weekend", "boolean")],
        date_m, props=["dataCategory: Time"])

# ------------------------------------------------------------------ measures
add = m.add
MONEY, PCT, INT, DELTA, PTS, DEC1 = "#,##0", "0.0%", "#,##0", "+0.0%;-0.0%;0.0%", "+0.0;-0.0;0.0", "#,##0.0"
F = dict(s="Sales", f="Finance", l="Leads", sv="Service", t="Targets", cy="KPI\\Current Year", py="KPI\\Prior Year", vs="KPI\\vs PY",
         lbl="KPI\\Labels", clr="KPI\\Colors", ins="Insights", rec="Conclusion", cov="Cover", ti="Time Intelligence")
add("Units", F["s"], INT, "Vehicles sold (one row per deal).", "COUNTROWS ( Sales )")
add("New Units", F["s"], INT, "New vehicles sold.", 'CALCULATE ( [Units], KEEPFILTERS ( Sales[Condition] = "جديد" ) )')
add("Revenue", F["s"], MONEY, "Vehicle sales revenue (sale price after discount).", "SUM ( Sales[SalePrice] )")
add("Vehicle Cost", F["s"], MONEY, "Cost of vehicles sold.", "SUM ( Sales[VehicleCost] )")
add("Front Gross", F["s"], MONEY, "Front-end gross profit: sale price minus vehicle cost.", "[Revenue] - [Vehicle Cost]")
add("Front Gross per Unit", F["s"], MONEY, "Front-end gross profit per vehicle.", "DIVIDE ( [Front Gross], [Units] )")
add("Discount Amount", F["s"], MONEY, "Discounts given.", "SUM ( Sales[DiscountAmount] )")
add("List Value", F["s"], MONEY, "List price of vehicles sold.", "SUM ( Sales[ListPrice] )")
add("Discount %", F["s"], PCT, "Discount as a share of list price.", "DIVIDE ( [Discount Amount], [List Value] )")
add("F&I Income", F["f"], MONEY, "Finance commission (F&I) earned on financed deals.", "SUM ( Sales[FinanceCommission] )")
add("Add-on Gross", F["f"], MONEY, "Accessories and insurance add-on profit.", "SUM ( Sales[AddOnRevenue] ) - SUM ( Sales[AddOnCost] )")
add("Back-end Gross", F["f"], MONEY, "Back-end profit: F&I income plus add-on profit.", "[F&I Income] + [Add-on Gross]")
add("Total Gross", F["s"], MONEY, "Front-end plus back-end gross profit.", "[Front Gross] + [Back-end Gross]")
add("Total Gross per Unit", F["s"], MONEY, "Total gross profit per vehicle.", "DIVIDE ( [Total Gross], [Units] )")
add("Financed Units", F["f"], INT, "Deals paid by bank finance or lease-to-own.", 'CALCULATE ( [Units], KEEPFILTERS ( Sales[PaymentType] <> "كاش" ) )')
add("Finance Penetration %", F["f"], PCT, "Financed Units / Units.", "DIVIDE ( [Financed Units], [Units] )")
add("Back-end Share from Financed %", F["f"], PCT, "Share of back-end gross earned on financed deals.",
    'DIVIDE ( CALCULATE ( [Back-end Gross], KEEPFILTERS ( Sales[PaymentType] <> "كاش" ) ), [Back-end Gross] )')
add("Trade-in Rate %", F["s"], PCT, "Share of deals with a trade-in.", "DIVIDE ( CALCULATE ( [Units], KEEPFILTERS ( Sales[TradeIn] = TRUE () ) ), [Units] )")
add("Avg Days in Stock", F["s"], DEC1, "Average days a sold vehicle spent in stock.", "AVERAGE ( Sales[DaysInStock] )")
add("Aged Stock %", F["s"], PCT, "Share of vehicles sold after more than 90 days in stock.", "DIVIDE ( CALCULATE ( [Units], KEEPFILTERS ( Sales[DaysInStock] > 90 ) ), [Units] )")
add("Electrified Share %", F["s"], PCT, "Hybrid and electric share of units.", 'DIVIDE ( CALCULATE ( [Units], KEEPFILTERS ( Vehicles[Powertrain] <> "بنزين" ) ), [Units] )')
add("Chinese Share %", F["s"], PCT, "Chinese-make share of units.", 'DIVIDE ( CALCULATE ( [Units], KEEPFILTERS ( Vehicles[Origin] = "صيني" ) ), [Units] )')
add("Leads", F["l"], INT, "Sales leads.", "COUNTROWS ( Leads )")
add("Test Drives", F["l"], INT, "Leads with a test drive.", "CALCULATE ( [Leads], KEEPFILTERS ( Leads[TestDrive] = TRUE () ) )")
add("Converted Leads", F["l"], INT, "Leads that became a deal.", "CALCULATE ( [Leads], KEEPFILTERS ( Leads[Converted] = TRUE () ) )")
add("Lead Conversion %", F["l"], PCT, "Converted Leads / Leads.", "DIVIDE ( [Converted Leads], [Leads] )")
add("Test Drive Rate %", F["l"], PCT, "Test Drives / Leads.", "DIVIDE ( [Test Drives], [Leads] )")
add("Visits", F["sv"], INT, "Service visits.", "COUNTROWS ( Service )")
add("Labor Revenue", F["sv"], MONEY, "Service labour revenue.", "SUM ( Service[LaborRevenue] )")
add("Parts Revenue", F["sv"], MONEY, "Service parts revenue.", "SUM ( Service[PartsRevenue] )")
add("Service Revenue", F["sv"], MONEY, "Labour plus parts revenue.", "[Labor Revenue] + [Parts Revenue]")
add("Labor Mix %", F["sv"], PCT, "Labour share of service revenue.", "DIVIDE ( [Labor Revenue], [Service Revenue] )")
add("Service Gross", F["sv"], MONEY, "Service revenue minus service cost.", "[Service Revenue] - SUM ( Service[ServiceCost] )")
add("Avg CSAT", F["sv"], "0.00", "Average customer satisfaction (1-5) of rated visits.", "AVERAGE ( Service[CSAT] )")
add("Comeback Rate %", F["sv"], PCT, "Share of visits that are comebacks (repeat repair).", "DIVIDE ( CALCULATE ( [Visits], KEEPFILTERS ( Service[IsComeback] = TRUE () ) ), [Visits] )")
add("Avg Turnaround (h)", F["sv"], DEC1, "Average service turnaround in hours.", "AVERAGE ( Service[TurnaroundHours] )")
add("Fixed Costs", F["sv"], MONEY, "Fixed overhead allocated to after-sales for the months in context (all branches in context).",
    "SUM ( Branches[MonthlyFixedCost] ) * DISTINCTCOUNT ( 'Date'[Year Month Number] )")
add("Absorption %", F["sv"], PCT, "Service absorption: Service Gross / Fixed Costs.", "DIVIDE ( [Service Gross], [Fixed Costs] )")
add("Revenue Target", F["t"], MONEY, "Monthly revenue target.", "SUM ( Targets[RevenueTarget] )")
add("Units Target", F["t"], INT, "Monthly unit target.", "SUM ( Targets[UnitsTarget] )")
KP = [("Units", "[Units]", INT), ("Revenue", "[Revenue]", MONEY), ("Front Gross", "[Front Gross]", MONEY), ("Back-end Gross", "[Back-end Gross]", MONEY),
      ("Total Gross", "[Total Gross]", MONEY), ("Financed Units", "[Financed Units]", INT), ("Discount Amount", "[Discount Amount]", MONEY),
      ("List Value", "[List Value]", MONEY), ("Leads", "[Leads]", INT), ("Test Drives", "[Test Drives]", INT), ("Converted Leads", "[Converted Leads]", INT),
      ("Visits", "[Visits]", INT), ("Service Revenue", "[Service Revenue]", MONEY), ("Labor Revenue", "[Labor Revenue]", MONEY),
      ("Parts Revenue", "[Parts Revenue]", MONEY), ("Service Gross", "[Service Gross]", MONEY), ("Fixed Costs", "[Fixed Costs]", MONEY),
      ("Avg CSAT", "[Avg CSAT]", "0.00"), ("Avg Days in Stock", "[Avg Days in Stock]", DEC1), ("Aged Stock %", "[Aged Stock %]", PCT),
      ("Electrified Share", "[Electrified Share %]", PCT), ("Chinese Share", "[Chinese Share %]", PCT), ("Comeback Rate", "[Comeback Rate %]", PCT),
      ("Avg Turnaround", "[Avg Turnaround (h)]", DEC1), ("Trade-in Rate", "[Trade-in Rate %]", PCT), ("Revenue Target", "[Revenue Target]", MONEY),
      ("Units Target", "[Units Target]", INT)]
for n, e, f in KP:
    add(f"{n} CY", F["cy"], f, f"{n} for the latest year in the current filter context.", *cy(e))
    if "Target" not in n:
        add(f"{n} PY", F["py"], f, f"{n} for the same period one year before the latest year in context.", *py(e))
for n, a, b, f in [("Front GPU", "Front Gross", "Units", MONEY), ("Total GPU", "Total Gross", "Units", MONEY), ("Finance Penetration", "Financed Units", "Units", PCT),
                   ("Lead Conversion", "Converted Leads", "Leads", PCT), ("Discount %", "Discount Amount", "List Value", PCT), ("Absorption", "Service Gross", "Fixed Costs", PCT)]:
    add(f"{n} CY", F["cy"], f, f"{n} for the latest year in context.", f"DIVIDE ( [{a} CY], [{b} CY] )")
    add(f"{n} PY", F["py"], f, f"{n} for the year before the latest year in context.", f"DIVIDE ( [{a} PY], [{b} PY] )")
add("Attainment CY", F["t"], PCT, "Revenue CY / Revenue Target CY.", "DIVIDE ( [Revenue CY], [Revenue Target CY] )")
add("Units Attainment CY", F["t"], PCT, "Units CY / Units Target CY.", "DIVIDE ( [Units CY], [Units Target CY] )")
add("Gap to Target CY", F["t"], "+#,##0;-#,##0;0", "Revenue CY minus Revenue Target CY.", "[Revenue CY] - [Revenue Target CY]")
add("Target FY", F["t"], MONEY, "Full-year revenue target of the latest year in context.",
    "VAR _LatestYear = MAX ( 'Date'[Year] )", "RETURN", "    CALCULATE ( [Revenue Target], REMOVEFILTERS ( 'Date' ), 'Date'[Year] = _LatestYear )")
add("Run-rate FY", F["ti"], MONEY, "Full-year revenue projection from the year-to-date pace up to the last deal date.",
    "VAR _LatestYear = MAX ( 'Date'[Year] )", "VAR _YearStart = DATE ( _LatestYear, 1, 1 )",
    "VAR _LastDeal = CALCULATE ( MAX ( Sales[DealDate] ), REMOVEFILTERS ( 'Date' ), 'Date'[Year] = _LatestYear )",
    "VAR _Ytd = CALCULATE ( [Revenue], REMOVEFILTERS ( 'Date' ), DATESBETWEEN ( 'Date'[Date], _YearStart, _LastDeal ) )", "RETURN",
    "    DIVIDE ( _Ytd, DATEDIFF ( _YearStart, _LastDeal, DAY ) + 1 ) * ( DATEDIFF ( _YearStart, DATE ( _LatestYear, 12, 31 ), DAY ) + 1 )")
CH = [("Units YoY %", growth("[Units CY]", "[Units PY]"), DELTA), ("Revenue YoY %", growth("[Revenue CY]", "[Revenue PY]"), DELTA),
      ("Total GPU vs PY %", growth("[Total GPU CY]", "[Total GPU PY]"), DELTA), ("Front GPU vs PY %", growth("[Front GPU CY]", "[Front GPU PY]"), DELTA),
      ("Leads vs PY %", growth("[Leads CY]", "[Leads PY]"), DELTA), ("Service Revenue vs PY %", growth("[Service Revenue CY]", "[Service Revenue PY]"), DELTA),
      ("Finance Penetration vs PY (pts)", diff("[Finance Penetration CY]", "[Finance Penetration PY]", 100), PTS),
      ("Lead Conversion vs PY (pts)", diff("[Lead Conversion CY]", "[Lead Conversion PY]", 100), PTS),
      ("Electrified vs PY (pts)", diff("[Electrified Share CY]", "[Electrified Share PY]", 100), PTS),
      ("Chinese vs PY (pts)", diff("[Chinese Share CY]", "[Chinese Share PY]", 100), PTS),
      ("Discount vs PY (pts)", diff("[Discount % CY]", "[Discount % PY]", 100), PTS), ("Aged vs PY (pts)", diff("[Aged Stock % CY]", "[Aged Stock % PY]", 100), PTS),
      ("Comeback vs PY (pts)", diff("[Comeback Rate CY]", "[Comeback Rate PY]", 100), PTS),
      ("Absorption vs PY (pts)", diff("[Absorption CY]", "[Absorption PY]", 100), PTS), ("CSAT vs PY", diff("[Avg CSAT CY]", "[Avg CSAT PY]"), "+0.00;-0.00;0.00"),
      ("Days in Stock vs PY", diff("[Avg Days in Stock CY]", "[Avg Days in Stock PY]"), "+0.0;-0.0;0.0")]
for n, lines, f in CH:
    add(n, F["vs"], f, f"Change: {n} (latest year in context vs the year before).", *lines)

POS = {"": "#4CC38A", " (Light)": "#1E7F4F"}; NEG = {"": "#F2706C", " (Light)": "#C23B33"}
NEU = {"": "#8B95A1", " (Light)": "#6B7280"}; AMB = {"": "#E0B04C", " (Light)": "#9A6700"}
AR_MONEY = 'IF ( ABS ( _Prior ) >= 1000000, FORMAT ( _Prior / 1000000, "0.0" ) & " مليون", FORMAT ( _Prior / 1000, "0.0" ) & " ألف" )'
PFMT = {"money": AR_MONEY, "pct": 'FORMAT ( _Prior, "0.0%" )', "count": 'FORMAT ( _Prior, "#,0" )', "num": 'FORMAT ( _Prior, "0.0" )', "csat": 'FORMAT ( _Prior, "0.00" )'}
LB = [("Units", "[Units YoY %]", "pct", 1, "[Units PY]", "count"), ("Revenue", "[Revenue YoY %]", "pct", 1, "[Revenue PY]", "money"),
      ("Total GPU", "[Total GPU vs PY %]", "pct", 1, "[Total GPU PY]", "money"), ("Front GPU", "[Front GPU vs PY %]", "pct", 1, "[Front GPU PY]", "money"),
      ("Leads", "[Leads vs PY %]", "pct", 1, "[Leads PY]", "count"), ("Service Revenue", "[Service Revenue vs PY %]", "pct", 1, "[Service Revenue PY]", "money"),
      ("Finance Penetration", "[Finance Penetration vs PY (pts)]", "pts", 1, "[Finance Penetration PY]", "pct"),
      ("Lead Conversion", "[Lead Conversion vs PY (pts)]", "pts", 1, "[Lead Conversion PY]", "pct"),
      ("Electrified", "[Electrified vs PY (pts)]", "pts", 1, "[Electrified Share PY]", "pct"), ("Chinese", "[Chinese vs PY (pts)]", "pts", 0, "[Chinese Share PY]", "pct"),
      ("Discount", "[Discount vs PY (pts)]", "pts", -1, "[Discount % PY]", "pct"), ("Aged", "[Aged vs PY (pts)]", "pts", -1, "[Aged Stock % PY]", "pct"),
      ("Comeback", "[Comeback vs PY (pts)]", "pts", -1, "[Comeback Rate PY]", "pct"), ("Absorption", "[Absorption vs PY (pts)]", "pts", 1, "[Absorption PY]", "pct"),
      ("CSAT", "[CSAT vs PY]", "num", 1, "[Avg CSAT PY]", "csat"), ("Days in Stock", "[Days in Stock vs PY]", "days", -1, "[Avg Days in Stock PY]", "num")]
for k, dlt, kind, good, prior, pk in LB:
    body = {"pct": 'FORMAT ( ABS ( _Delta ), "0.0%" )', "pts": 'FORMAT ( ABS ( _Delta ), "0.0" ) & " نقطة"', "num": 'FORMAT ( ABS ( _Delta ), "0.00" )',
            "days": 'FORMAT ( ABS ( _Delta ), "0.0" ) & " يوم"'}[kind]
    add(f"{k} vs PY Label", F["lbl"], None, f"Arabic tile text for {k}: arrow, change vs prior year and the prior-year value.",
        f"VAR _Delta = {dlt}", f"VAR _Prior = {prior}", "RETURN", "    IF (", "        ISBLANK ( _Delta ),", '        "لا توجد بيانات للعام السابق",',
        f'        IF ( _Delta >= 0, UNICHAR ( 9650 ), UNICHAR ( 9660 ) ) & " " & {body} & "  |  العام السابق " & {PFMT[pk]}', "    )")
    for sfx in ("", " (Light)"):
        up, down = (POS[sfx], NEG[sfx]) if good == 1 else (NEG[sfx], POS[sfx]) if good == -1 else (NEU[sfx], NEU[sfx])
        add(f"{k} vs PY Color{sfx}", F["clr"], None, f"Hex colour for the {k} change{' (light pages)' if sfx else ''}.",
            f"VAR _Delta = {dlt}", "RETURN", "    SWITCH (", "        TRUE (),", f'        ISBLANK ( _Delta ), "{NEU[sfx]}",', f'        _Delta >= 0, "{up}",', f'        "{down}"', "    )")
add("Attainment Label", F["lbl"], None, "Arabic tile text: gap to the revenue target.",
    "VAR _Gap = [Gap to Target CY]", "VAR _Target = [Revenue Target CY]", "RETURN", "    IF (", "        ISBLANK ( _Target ),", '        "لا يوجد هدف",',
    '        IF ( _Gap >= 0, UNICHAR ( 9650 ), UNICHAR ( 9660 ) ) & " " & FORMAT ( ABS ( _Gap ) / 1000000, "0.0" ) & " مليون " & IF ( _Gap >= 0, "فوق الهدف", "دون الهدف" )', "    )")
for sfx in ("", " (Light)"):
    add(f"Attainment Color{sfx}", F["clr"], None, "Hex colour by attainment: >=100% green, 90-100% amber, <90% red.",
        "VAR _A = [Attainment CY]", "RETURN", "    SWITCH (", "        TRUE (),", f'        ISBLANK ( _A ), "{NEU[sfx]}",', f'        _A >= 1, "{POS[sfx]}",',
        f'        _A >= 0.9, "{AMB[sfx]}",', f'        "{NEG[sfx]}"', "    )")
    add(f"Comeback Color{sfx}", F["clr"], None, "Hex colour for a comeback rate: red above 7%, amber above 5%.",
        "VAR _R = [Comeback Rate CY]", "RETURN", "    SWITCH (", "        TRUE (),", f'        ISBLANK ( _R ), "{NEU[sfx]}",', f'        _R > 0.07, "{NEG[sfx]}",',
        f'        _R > 0.05, "{AMB[sfx]}",', f'        "{POS[sfx]}"', "    )")
add("Period Label", F["lbl"], None, "Header text naming the compared years.", "VAR _Y = MAX ( 'Date'[Year] )", "RETURN", '    _Y & " مقابل " & ( _Y - 1 )')
for n, e in [("Revenue All Years", "[Revenue]"), ("Units All Years", "[Units]"), ("Total Gross All Years", "[Total Gross]"), ("Visits All Years", "[Visits]")]:
    add(n, F["cov"], MONEY, f"{n.replace(' All Years', '')} across 2023-2025 (ignores date filters) for the cover page.", f"CALCULATE ( {e}, REMOVEFILTERS ( 'Date' ) )")
add("Cover Revenue Label", F["cov"], None, "Cover headline: three-year revenue in SAR millions (unit is printed in the label line).", 'FORMAT ( [Revenue All Years] / 1000000, "#,0" )')
add("Cover Gross Label", F["cov"], None, "Cover headline: three-year total gross in SAR millions (unit is printed in the label line).", 'FORMAT ( [Total Gross All Years] / 1000000, "#,0.0" )')

INS = {
    "Insight Headline": ["VAR _Y = MAX ( 'Date'[Year] )", "VAR _G = [Revenue YoY %]", "VAR _A = [Attainment CY]", "RETURN",
                         '    "بلغت الإيرادات " & FORMAT ( [Revenue CY] / 1000000, "0.0" ) & " مليون ريال في " & _Y',
                         '        & IF ( NOT ISBLANK ( _G ), "، بتغير " & FORMAT ( _G, "+0.0%;-0.0%" ) & " عن " & ( _Y - 1 ), "" )',
                         '        & IF ( NOT ISBLANK ( _A ), "، وحققت " & FORMAT ( _A, "0.0%" ) & " من الهدف", "" ) & "."'],
    "Insight Branch Target": ["VAR _B = FILTER ( ADDCOLUMNS ( VALUES ( Branches[BranchName] ), \"@A\", [Attainment CY] ), NOT ISBLANK ( [@A] ) )",
                              "VAR _W = TOPN ( 1, _B, [@A], ASC )", "RETURN",
                              '    IF ( ISEMPTY ( _W ), "لا يوجد هدف لهذا الاختيار.", "فرع " & CONCATENATEX ( _W, Branches[BranchName], " / " ) & " الأبعد عن هدفه بنسبة تحقيق " & FORMAT ( MAXX ( _W, [@A] ), "0.0%" ) & "." )'],
    "Insight Chinese": ["VAR _Now = [Chinese Share CY]", "VAR _Before = [Chinese Share PY]", "RETURN",
                        '    "حصة العلامات الصينية " & FORMAT ( _Now, "0.0%" ) & " من الوحدات المباعة" & IF ( NOT ISBLANK ( _Before ), " مقابل " & FORMAT ( _Before, "0.0%" ) & " في العام السابق", "" ) & "."'],
    "Insight Electrified": ["VAR _Now = [Electrified Share CY]", "VAR _Before = [Electrified Share PY]", "RETURN",
                            '    "السيارات الهجينة والكهربائية " & FORMAT ( _Now, "0.0%" ) & " من المبيعات" & IF ( NOT ISBLANK ( _Before ), "، بزيادة " & FORMAT ( ( _Now - _Before ) * 100, "0.0" ) & " نقطة عن العام السابق", "" ) & "."'],
    "Insight Discount": ["VAR _B = FILTER ( ADDCOLUMNS ( VALUES ( Branches[BranchName] ), \"@D\", [Discount % CY], \"@G\", [Front GPU CY] ), NOT ISBLANK ( [@D] ) )",
                         "VAR _Top = TOPN ( 1, _B, [@D], DESC )", "RETURN",
                         '    "فرع " & CONCATENATEX ( _Top, Branches[BranchName], " / " ) & " يمنح أعلى خصم (" & FORMAT ( MAXX ( _Top, [@D] ), "0.0%" ) & ") فينخفض الربح الأمامي للسيارة إلى " & FORMAT ( MAXX ( _Top, [@G] ), "#,0" ) & " ريال فقط."'],
    "Insight Finance": ['"التمويل والتأجير يشملان " & FORMAT ( [Finance Penetration CY], "0.0%" ) & " من الصفقات ويولّدان " & FORMAT ( CALCULATE ( [Back-end Share from Financed %], KEEPFILTERS ( \'Date\'[Year] = MAX ( \'Date\'[Year] ) ) ), "0%" ) & " من الربح الخلفي."'],
    "Insight Leads": ["VAR _S = FILTER ( ADDCOLUMNS ( VALUES ( Leads[Source] ), \"@C\", [Lead Conversion CY], \"@N\", [Leads CY] ), NOT ISBLANK ( [@C] ) )",
                      "VAR _Best = TOPN ( 1, _S, [@C], DESC )", "VAR _Big = TOPN ( 1, _S, [@N], DESC )", "RETURN",
                      '    "مصدر " & CONCATENATEX ( _Best, Leads[Source], " / " ) & " يتحول بنسبة " & FORMAT ( MAXX ( _Best, [@C] ), "0.0%" ) & " مقابل " & FORMAT ( MAXX ( _Big, [@C] ), "0.0%" ) & " لـ" & CONCATENATEX ( _Big, Leads[Source], " / " ) & " رغم أنه الأعلى في عدد العملاء المحتملين."'],
    "Insight Aged": ["VAR _Aged = CALCULATE ( [Discount % CY], Sales[DaysInStock] > 90 )", "VAR _Fresh = CALCULATE ( [Discount % CY], Sales[DaysInStock] <= 90 )", "RETURN",
                     '    "السيارات التي بقيت أكثر من 90 يوماً في المخزون بيعت بخصم " & FORMAT ( _Aged, "0.0%" ) & " مقابل " & FORMAT ( _Fresh, "0.0%" ) & " للمخزون الأحدث."'],
    "Insight Service": ["VAR _Long = CALCULATE ( [Comeback Rate CY], Service[TurnaroundHours] > 48 )", "VAR _Short = CALCULATE ( [Comeback Rate CY], Service[TurnaroundHours] <= 48 )", "RETURN",
                        '    "الزيارات التي تجاوزت 48 ساعة عادت للإصلاح بنسبة " & FORMAT ( _Long, "0.0%" ) & " مقابل " & FORMAT ( _Short, "0.0%" ) & " للزيارات الأسرع."'],
    "Insight Absorption": ['"أرباح ما بعد البيع تغطي " & FORMAT ( [Absorption CY], "0.0%" ) & " من التكاليف الثابتة المخصصة للفروع."'],
}
for n, lines in INS.items():
    add(n, F["ins"], None, "Arabic insight sentence written from the data.", *lines)
REC = {
    "Recommendation Discount": ["VAR _B = FILTER ( ADDCOLUMNS ( VALUES ( Branches[BranchName] ), \"@D\", [Discount % CY], \"@L\", [List Value CY] ), NOT ISBLANK ( [@D] ) )",
                                "VAR _Top = TOPN ( 1, _B, [@D], DESC )", "VAR _Name = CONCATENATEX ( _Top, Branches[BranchName], \" / \" )",
                                "VAR _Others = CALCULATE ( [Discount % CY], Branches[BranchName] <> _Name )",
                                "VAR _Gain = ( MAXX ( _Top, [@D] ) - _Others ) * MAXX ( _Top, [@L] )", "RETURN",
                                '    "ضبط سياسة الخصم في فرع " & _Name & ": إعادته إلى متوسط بقية الفروع (" & FORMAT ( _Others, "0.0%" ) & ") يضيف نحو " & FORMAT ( _Gain / 1000000, "0.0" ) & " مليون ريال من الربح الأمامي سنوياً."'],
    "Recommendation Leads": ['"تحويل جزء من ميزانية سناب شات إلى برامج الإحالة ودعوات زيارة المعرض، فهي الأعلى تحويلاً، مع متابعة أسرع للعملاء المحتملين من الإعلانات."'],
    "Recommendation Stock": ['"خطة تصريف شهرية للمخزون الذي تجاوز 90 يوماً (" & FORMAT ( [Aged Stock % CY], "0.0%" ) & " من الوحدات المباعة) قبل أن يحتاج خصماً أعمق، وربط طلبيات الطرازات بسرعة دورانها."'],
    "Recommendation Service": ['"هدف زمن إنجاز أقل من 48 ساعة في مراكز الصيانة، مع فحص جودة قبل التسليم، لخفض الزيارات المتكررة ورفع رضا العملاء عن " & FORMAT ( [Avg CSAT CY], "0.00" ) & "."'],
}
for n, lines in REC.items():
    add(n, F["rec"], None, "Arabic recommendation for the conclusion page, with numbers from the data.", *lines)

# ------------------------------------------------------------------ Arabic value texts (empty state instead of blank)
for n, e in [("Revenue CY Text", "[Revenue CY]"), ("Service Revenue CY Text", "[Service Revenue CY]"), ("Target FY Text", "[Target FY]"), ("Run-rate FY Text", "[Run-rate FY]")]:
    add(n, F["lbl"], None, f"Arabic tile value for {e}: millions with the word مليون, or an empty-state note.",
        f"VAR _V = {e}", "RETURN", '    IF ( ISBLANK ( _V ), "لا توجد بيانات للفترة", FORMAT ( _V / 1000000, "0.0" ) & " مليون" )')

# ------------------------------------------------------------------ animated SVG measures (ImageUrl)
COLORS = {"": ("%2312A594", "%232A2F37"), " (Light)": ("%2300897A", "%23E6E9ED")}
SPARK = {"Revenue CY": "[Revenue]", "Units CY": "[Units]", "Total GPU CY": "[Total Gross per Unit]", "Attainment CY": "DIVIDE ( [Revenue], [Revenue Target] )",
         "Finance Penetration CY": "[Finance Penetration %]", "Service Revenue CY": "[Service Revenue]", "Front GPU CY": "[Front Gross per Unit]",
         "Discount % CY": "[Discount %]", "Avg Days in Stock CY": "[Avg Days in Stock]", "Aged Stock % CY": "[Aged Stock %]",
         "Electrified Share CY": "[Electrified Share %]", "Chinese Share CY": "[Chinese Share %]", "Leads CY": "[Leads]",
         "Lead Conversion CY": "[Lead Conversion %]", "Avg CSAT CY": "[Avg CSAT]", "Comeback Rate CY": "[Comeback Rate %]", "Absorption CY": "[Absorption %]"}
SW, SH = 240, 28
for cyname, base in SPARK.items():
    for sfx, (acc, _) in COLORS.items():
        name = f"Spark {cyname}{sfx}"
        m.categories[name] = "ImageUrl"
        add(name, "KPI\\Sparklines", None, f"Animated SVG sparkline (latest year by month) for {cyname}{' on light pages' if sfx else ''}: the line draws in, the area fades in, the end dot pops.",
            "VAR _LatestYear = MAX ( 'Date'[Year] )",
            "VAR _Months = CALCULATETABLE ( VALUES ( 'Date'[Month Number] ), REMOVEFILTERS ( 'Date' ) )",
            f"VAR _Pts = FILTER ( ADDCOLUMNS ( _Months, \"@v\", VAR _M = 'Date'[Month Number] RETURN CALCULATE ( {base}, REMOVEFILTERS ( 'Date' ), 'Date'[Year] = _LatestYear, 'Date'[Month Number] = _M ) ), NOT ISBLANK ( [@v] ) )",
            "VAR _Min = MINX ( _Pts, [@v] )", "VAR _Max = MAXX ( _Pts, [@v] )", "VAR _Range = IF ( _Max = _Min, 1, _Max - _Min )",
            f"VAR _Line = CONCATENATEX ( _Pts, FORMAT ( ( 'Date'[Month Number] - 1 ) * {(SW - 8) / 11:.3f} + 4, \"0.0\" ) & \",\" & FORMAT ( {SH - 4} - ( [@v] - _Min ) / _Range * {SH - 10}, \"0.0\" ), \" L \", 'Date'[Month Number], ASC )",
            "VAR _LastM = MAXX ( _Pts, 'Date'[Month Number] )", "VAR _FirstM = MINX ( _Pts, 'Date'[Month Number] )",
            "VAR _LastV = MAXX ( FILTER ( _Pts, 'Date'[Month Number] = _LastM ), [@v] )",
            f"VAR _X = FORMAT ( ( _LastM - 1 ) * {(SW - 8) / 11:.3f} + 4, \"0.0\" )", f"VAR _X0 = FORMAT ( ( _FirstM - 1 ) * {(SW - 8) / 11:.3f} + 4, \"0.0\" )",
            f"VAR _Y = FORMAT ( {SH - 4} - ( _LastV - _Min ) / _Range * {SH - 10}, \"0.0\" )",
            "VAR _Svg =",
            f"    \"<svg xmlns='http://www.w3.org/2000/svg' width='{SW}' height='{SH}' viewBox='0 0 {SW} {SH}'>\"",
            f"        & \"<defs><linearGradient id='g' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='{acc}' stop-opacity='0.35'/><stop offset='1' stop-color='{acc}' stop-opacity='0'/></linearGradient></defs>\"",
            f"        & \"<path d='M\" & _Line & \" L\" & _X & \",{SH} L\" & _X0 & \",{SH} Z' fill='url(%23g)' opacity='0'><animate attributeName='opacity' from='0' to='1' begin='0.5s' dur='0.7s' fill='freeze'/></path>\"",
            f"        & \"<path d='M\" & _Line & \"' fill='none' stroke='{acc}' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' pathLength='1' stroke-dasharray='1' stroke-dashoffset='1'><animate attributeName='stroke-dashoffset' from='1' to='0' dur='1.1s' fill='freeze' calcMode='spline' keyTimes='0;1' keySplines='0.25 0.8 0.25 1'/></path>\"",
            f"        & \"<circle cx='\" & _X & \"' cy='\" & _Y & \"' r='0' fill='{acc}'><animate attributeName='r' from='0' to='3.2' begin='1s' dur='0.3s' fill='freeze'/></circle></svg>\"",
            "RETURN", "    IF ( COUNTROWS ( _Pts ) > 1, \"data:image/svg+xml;utf8,\" & _Svg )")
BW, BH = 300, 22
for sfx, (acc, track) in COLORS.items():
    name = f"Branch Bullet SVG{sfx}"
    m.categories[name] = "ImageUrl"
    tgt = "%238A93F2" if not sfx else "%234A5FA8"
    add(name, "KPI\\Sparklines", None, f"Animated right-to-left bullet chart per branch{' (light pages)' if sfx else ''}: revenue bar grows from the right, target shown as a marker.",
        "VAR _Rev = [Revenue CY]", "VAR _Tgt = [Revenue Target CY]",
        "VAR _Max = MAXX ( ALLSELECTED ( Branches[BranchName] ), MAX ( [Revenue CY], [Revenue Target CY] ) )",
        f"VAR _W = DIVIDE ( _Rev, _Max ) * {BW - 4}", f"VAR _T = {BW - 2} - DIVIDE ( _Tgt, _Max ) * {BW - 4}",
        "VAR _Svg =",
        f"    \"<svg xmlns='http://www.w3.org/2000/svg' width='{BW}' height='{BH}' viewBox='0 0 {BW} {BH}'>\"",
        f"        & \"<rect x='2' y='6' width='{BW - 4}' height='10' rx='2' fill='{track}'/>\"",
        f"        & \"<rect x='{BW - 2}' y='6' width='0' height='10' rx='2' fill='{acc}'><animate attributeName='width' from='0' to='\" & FORMAT ( _W, \"0.0\" ) & \"' dur='0.9s' fill='freeze' calcMode='spline' keyTimes='0;1' keySplines='0.25 0.8 0.25 1'/><animate attributeName='x' from='{BW - 2}' to='\" & FORMAT ( {BW - 2} - _W, \"0.0\" ) & \"' dur='0.9s' fill='freeze' calcMode='spline' keyTimes='0;1' keySplines='0.25 0.8 0.25 1'/></rect>\"",
        f"        & IF ( NOT ISBLANK ( _Tgt ), \"<rect x='\" & FORMAT ( _T - 1, \"0.0\" ) & \"' y='2' width='3' height='18' rx='1' fill='{tgt}'/>\", \"\" ) & \"</svg>\"",
        "RETURN", "    IF ( NOT ISBLANK ( _Rev ), \"data:image/svg+xml;utf8,\" & _Svg )")
for sfx, (acc, track) in COLORS.items():
    name = f"Cover Hero SVG{sfx}"
    m.categories[name] = "ImageUrl"
    o2 = "%23E8793A" if not sfx else "%23C2560F"
    lines = "".join(f"<line x1='{40 + i * 30}' y1='300' x2='{170 + i * 30}' y2='20' stroke='{acc}' stroke-width='3' stroke-opacity='{0.10 + i * 0.05:.2f}' opacity='0'><animateTransform attributeName='transform' type='translate' from='-60 0' to='0 0' begin='{i * 0.08:.2f}s' dur='0.9s' fill='freeze' calcMode='spline' keyTimes='0;1' keySplines='0.2 0.8 0.2 1'/><animate attributeName='opacity' from='0' to='1' begin='{i * 0.08:.2f}s' dur='0.6s' fill='freeze'/></line>" for i in range(8))
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='360' height='300' viewBox='0 0 360 300'>{lines}"
           f"<path d='M180 40 L250 120 L222 120 L180 72 L138 120 L110 120 Z' fill='none' stroke='{acc}' stroke-width='3' pathLength='1' stroke-dasharray='1' stroke-dashoffset='1'><animate attributeName='stroke-dashoffset' from='1' to='0' begin='0.4s' dur='1.2s' fill='freeze'/></path>"
           f"<path d='M180 110 L232 172 L204 172 L180 144 L156 172 L128 172 Z' fill='none' stroke='{o2}' stroke-width='3' pathLength='1' stroke-dasharray='1' stroke-dashoffset='1'><animate attributeName='stroke-dashoffset' from='1' to='0' begin='0.8s' dur='1.2s' fill='freeze'/></path>"
           f"<circle cx='180' cy='230' r='6' fill='{acc}' opacity='0.9'><animate attributeName='r' values='6;10;6' dur='2.4s' begin='2s' repeatCount='indefinite'/><animate attributeName='opacity' values='0.9;0.3;0.9' dur='2.4s' begin='2s' repeatCount='indefinite'/></circle></svg>")
    add(name, F["cov"], None, "Animated cover mark: speed lines sweep in, the two chevrons draw, then one subtle pulse repeats.", f'"data:image/svg+xml;utf8,{svg}"')

# ------------------------------------------------------------------ bidi: isolate Arabic text runs (RLI...PDI) and number groups (LRI...PDI)
def _wrap_formats(text):
    out, i = "", 0
    while True:
        j = text.find("FORMAT (", i)
        if j < 0:
            return out + text[i:]
        depth, k = 0, j + len("FORMAT")
        while True:
            if text[k] == "(":
                depth += 1
            elif text[k] == ")":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        out += text[i:j] + "UNICHAR ( 8294 ) & " + text[j:k + 1] + " & UNICHAR ( 8297 )"
        i = k + 1


BIDI_FOLDERS = {F["lbl"], F["ins"], F["rec"]}
for idx, (name, folder, fmt, desc, lines) in enumerate(m.measures):
    if not (folder in BIDI_FOLDERS or name in ("Cover Revenue Label", "Cover Gross Label")) or "Color" in name:
        continue
    lines = [_wrap_formats(l) for l in lines]
    if "RETURN" in lines:
        r = lines.index("RETURN")
        lines[r + 1] = lines[r + 1][:4] + "UNICHAR ( 8295 ) & ( " + lines[r + 1][4:]
        lines[-1] = lines[-1] + " ) & UNICHAR ( 8297 )"
    else:
        lines = ["UNICHAR ( 8295 ) & ( " + lines[0]] + lines[1:-1] + [lines[-1] + " ) & UNICHAR ( 8297 )"] if len(lines) > 1 else ["UNICHAR ( 8295 ) & ( " + lines[0] + " ) & UNICHAR ( 8297 )"]
    m.measures[idx] = (name, folder, fmt, desc + " Text is wrapped in Unicode bidi isolates (RLI/LRI/PDI) so it reads correctly in left-to-right cards.", lines)


m.finish(["Sales", "Leads", "Service", "Vehicles", "Branches", "Employees", "Customers", "Targets", "Segment", "Date"],
         [("Sales.DealDate", "Date.Date"), ("Sales.BranchID", "Branches.BranchID"), ("Sales.EmployeeID", "Employees.EmployeeID"),
          ("Sales.CustomerID", "Customers.CustomerID"), ("Sales.VehicleID", "Vehicles.VehicleID"), ("Leads.LeadDate", "Date.Date"),
          ("Leads.BranchID", "Branches.BranchID"), ("Leads.VehicleID", "Vehicles.VehicleID"), ("Service.VisitDate", "Date.Date"),
          ("Service.BranchID", "Branches.BranchID"), ("Service.EmployeeID", "Employees.EmployeeID"), ("Service.CustomerID", "Customers.CustomerID"),
          ("Service.VehicleID", "Vehicles.VehicleID"), ("Vehicles.Segment", "Segment.Segment"), ("Targets.Month", "Date.Date"),
          ("Targets.BranchID", "Branches.BranchID"), ("Targets.Segment", "Segment.Segment")],
         "C:\\PowerBI_Report\\data\\", "Folder that contains VehicleSales.xlsx (must end with a backslash)")
print(len(m.measures), "measures")
