# Writes the complete v3 semantic model (TMDL) for the richer FashionVue dataset.
# Lineage tags and relationship ids are deterministic (uuid5 of the object path).
# Usage: python3 model_v3.py <definition dir>   (then round-trip through TmdlSerializer)
import os, re, shutil, sys, uuid, json

DEF = sys.argv[1]
T = "\t"
NS = uuid.UUID("6f1c9d2e-3b4a-4c5d-8e7f-0a1b2c3d4e5f")


def tag(*path):
    return str(uuid.uuid5(NS, "/".join(path)))


def q(name):
    return f"'{name}'" if re.search(r"[^A-Za-z0-9_]", name) else name


# ------------------------------------------------------------------ helpers
def column(table, name, dtype, fmt=None, hidden=False, key=False, summarize="none", sort_by=None, date_only=False,
           desc=None, category=None):
    L = []
    if desc:
        L.append(f"{T}/// {desc}")
    L += [f"{T}column {q(name)}", f"{T*2}dataType: {dtype}"]
    if key:
        L.append(f"{T*2}isKey")
    if hidden:
        L.append(f"{T*2}isHidden")
    if fmt:
        L.append(f"{T*2}formatString: {fmt}")
    if category:
        L.append(f"{T*2}dataCategory: {category}")
    L += [f"{T*2}lineageTag: {tag(table, 'col', name)}", f"{T*2}summarizeBy: {summarize}", f"{T*2}sourceColumn: {name}"]
    if sort_by:
        L.append(f"{T*2}sortByColumn: {q(sort_by)}")
    L += ["", f"{T*2}annotation SummarizationSetBy = {'User' if summarize == 'none' and dtype in ('int64', 'double', 'decimal') else 'Automatic'}"]
    if date_only:
        L += ["", f"{T*2}annotation UnderlyingDateTimeDataType = Date"]
    return "\n".join(L) + "\n\n"


def partition(name, m_lines):
    body = "\n".join(f"{T*4}{l}" for l in m_lines)
    return f"{T}partition {q(name)} = m\n{T*2}mode: import\n{T*2}source =\n{body}\n\n"


def table(name, desc, cols, m_lines, props=(), measures=""):
    s = f"/// {desc}\ntable {q(name)}\n{T}lineageTag: {tag(name)}\n" + "".join(f"{T}{p}\n" for p in props) + "\n"
    s += measures + "".join(cols) + partition(name, m_lines) + f"{T}annotation PBI_ResultType = Table\n"
    with open(os.path.join(DEF, "tables", f"{name}.tmdl"), "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def excel(item, steps, types):
    """Load an Excel table, apply extra steps (list of (name, expression using {prev})), then set types once."""
    out = ["let", f'{T}Source = Excel.Workbook(File.Contents(DataFolder & "SalesSample.xlsx"), null, true),',
           f'{T}#"{item} Table" = Source{{[Item="{item}",Kind="Table"]}}[Data],']
    prev = f'#"{item} Table"'
    for sname, expr in steps:
        out.append(f'{T}#"{sname}" = {expr.format(prev=prev)},')
        prev = f'#"{sname}"'
    tl = ", ".join(f'{{"{c}", {t}}}' for c, t in types)
    out += [f'{T}#"Set Column Types" = Table.TransformColumnTypes({prev}, {{{tl}}})', "in", f'{T}#"Set Column Types"']
    return out


I64, TXT, DT, NUM, CUR, LOG = "Int64.Type", "type text", "type date", "type number", "Currency.Type", "type logical"
os.makedirs(os.path.join(DEF, "tables"), exist_ok=True)
for f in os.listdir(os.path.join(DEF, "tables")):
    os.remove(os.path.join(DEF, "tables", f))

# ------------------------------------------------------------------ Sales
SALES_TYPES = [("OrderID", I64), ("LineNo", I64), ("OrderDate", DT), ("CustomerID", I64), ("ProductID", I64), ("StoreID", I64),
               ("EmployeeID", I64), ("CampaignID", I64), ("Channel", TXT), ("PaymentMethod", TXT), ("Quantity", I64),
               ("UnitPrice", CUR), ("Discount", NUM), ("SalesAmount", CUR), ("CostAmount", CUR), ("ShippingCost", CUR),
               ("DeliveryDays", I64), ("IsReturned", LOG), ("ReturnReason", TXT), ("CustomerRating", I64),
               ("Payment Type", TXT), ("Discount Band", TXT), ("Delivery Band", TXT), ("Delivery Band Order", I64)]
sales_steps = [
    ("Added Payment Type", 'Table.AddColumn({prev}, "Payment Type", each if List.Contains({{"Tabby", "Tamara"}}, [PaymentMethod]) then "BNPL" else if [PaymentMethod] = "Cash" then "Cash" else "Cards & wallets")'),
    ("Added Discount Band", 'Table.AddColumn({prev}, "Discount Band", each if [Discount] = 0 then "Full price" else Text.From(Number.Round([Discount] * 100)) & "% off")'),
    ("Added Delivery Band", 'Table.AddColumn({prev}, "Delivery Band", each if [DeliveryDays] = null then "In store" else if [DeliveryDays] <= 2 then "1-2 days" else if [DeliveryDays] = 3 then "3 days" else if [DeliveryDays] <= 5 then "4-5 days" else "6+ days")'),
    ("Added Delivery Band Order", 'Table.AddColumn({prev}, "Delivery Band Order", each if [DeliveryDays] = null then 0 else if [DeliveryDays] <= 2 then 1 else if [DeliveryDays] = 3 then 2 else if [DeliveryDays] <= 5 then 3 else 4)'),
]
S = "Sales"
sales_cols = [column(S, "OrderID", "int64", "0"), column(S, "LineNo", "int64", "0", hidden=True),
              column(S, "OrderDate", "dateTime", "Short Date", hidden=True, date_only=True)]
sales_cols += [column(S, k, "int64", "0", hidden=True) for k in ("CustomerID", "ProductID", "StoreID", "EmployeeID", "CampaignID")]
sales_cols += [column(S, "Channel", "string"), column(S, "PaymentMethod", "string"), column(S, "Payment Type", "string"),
               column(S, "Quantity", "int64", "#,##0", summarize="sum"), column(S, "UnitPrice", "decimal", "#,##0.00", summarize="sum"),
               column(S, "Discount", "double", "0%", summarize="none"), column(S, "Discount Band", "string", sort_by="Discount"),
               column(S, "SalesAmount", "decimal", "#,##0.00", summarize="sum"), column(S, "CostAmount", "decimal", "#,##0.00", summarize="sum"),
               column(S, "ShippingCost", "decimal", "#,##0.00", summarize="sum"), column(S, "DeliveryDays", "int64", "0", summarize="none"),
               column(S, "Delivery Band", "string", sort_by="Delivery Band Order"), column(S, "Delivery Band Order", "int64", "0", hidden=True),
               column(S, "IsReturned", "boolean"), column(S, "ReturnReason", "string"),
               column(S, "CustomerRating", "int64", "0", summarize="none")]

# ------------------------------------------------------------------ dimensions
P = "Products"
prod_cols = [column(P, "ProductID", "int64", "0", hidden=True), column(P, "ProductName", "string"), column(P, "Brand", "string"),
             column(P, "Category", "string", hidden=True), column(P, "SubCategory", "string"), column(P, "Gender", "string"),
             column(P, "Collection", "string"), column(P, "Color", "string"), column(P, "PriceTier", "string", sort_by="Price Tier Order"),
             column(P, "Price Tier Order", "int64", "0", hidden=True), column(P, "UnitCost", "decimal", "#,##0.00", summarize="none"),
             column(P, "ListPrice", "decimal", "#,##0.00", summarize="none"), column(P, "LaunchDate", "dateTime", "Short Date", date_only=True)]
prod_m = excel("Products", [("Added Price Tier Order", 'Table.AddColumn({prev}, "Price Tier Order", each if [PriceTier] = "Essential" then 1 else if [PriceTier] = "Premium" then 2 else 3)')],
               [("ProductID", I64), ("ProductName", TXT), ("Brand", TXT), ("Category", TXT), ("SubCategory", TXT), ("Gender", TXT),
                ("Collection", TXT), ("Color", TXT), ("PriceTier", TXT), ("UnitCost", CUR), ("ListPrice", CUR), ("LaunchDate", DT),
                ("Price Tier Order", I64)])

C = "Customers"
cust_cols = [column(C, "CustomerID", "int64", "0", hidden=True), column(C, "CustomerName", "string"), column(C, "Customer Label", "string"),
             column(C, "Gender", "string"), column(C, "AgeGroup", "string"), column(C, "Nationality", "string"), column(C, "City", "string"),
             column(C, "Region", "string", hidden=True), column(C, "LoyaltyTier", "string", sort_by="Tier Order"),
             column(C, "Tier Order", "int64", "0", hidden=True), column(C, "AcquisitionChannel", "string"),
             column(C, "JoinDate", "dateTime", "Short Date", date_only=True), column(C, "Join Month", "string"),
             column(C, "FirstOrderDate", "dateTime", "Short Date", date_only=True, desc="Date of the customer's first order (computed in Power Query from Sales).")]
cust_m = [
    "let",
    f'{T}Source = Excel.Workbook(File.Contents(DataFolder & "SalesSample.xlsx"), null, true),',
    f'{T}#"Customers Table" = Source{{[Item="Customers",Kind="Table"]}}[Data],',
    f'{T}#"Sales Table" = Source{{[Item="Sales",Kind="Table"]}}[Data],',
    f'{T}#"First Orders" = Table.Group(#"Sales Table", {{"CustomerID"}}, {{{{"FirstOrderDate", each List.Min([OrderDate]), type any}}}}),',
    f'{T}#"Merged First Order" = Table.NestedJoin(#"Customers Table", {{"CustomerID"}}, #"First Orders", {{"CustomerID"}}, "FirstOrder", JoinKind.LeftOuter),',
    f'{T}#"Expanded First Order" = Table.ExpandTableColumn(#"Merged First Order", "FirstOrder", {{"FirstOrderDate"}}),',
    f'{T}#"Added Customer Label" = Table.AddColumn(#"Expanded First Order", "Customer Label", each [CustomerName] & " (#" & Text.From([CustomerID]) & ")"),',
    f'{T}#"Added Join Month" = Table.AddColumn(#"Added Customer Label", "Join Month", each Date.ToText(Date.From([JoinDate]), "yyyy-MM")),',
    f'{T}#"Added Tier Order" = Table.AddColumn(#"Added Join Month", "Tier Order", each List.PositionOf({{"Bronze", "Silver", "Gold", "Platinum"}}, [LoyaltyTier]) + 1),',
    f'{T}#"Set Column Types" = Table.TransformColumnTypes(#"Added Tier Order", {{{{"CustomerID", Int64.Type}}, {{"CustomerName", type text}}, {{"Gender", type text}}, {{"AgeGroup", type text}}, {{"Nationality", type text}}, {{"City", type text}}, {{"Region", type text}}, {{"LoyaltyTier", type text}}, {{"AcquisitionChannel", type text}}, {{"JoinDate", type date}}, {{"FirstOrderDate", type date}}, {{"Customer Label", type text}}, {{"Join Month", type text}}, {{"Tier Order", Int64.Type}}}})',
    "in",
    f'{T}#"Set Column Types"',
]

ST = "Stores"
store_cols = [column(ST, "StoreID", "int64", "0", hidden=True), column(ST, "StoreName", "string"), column(ST, "City", "string"),
              column(ST, "Region", "string", desc="Store location region (Online for the web/app store). Sales by customer region use the Region table."),
              column(ST, "StoreType", "string"), column(ST, "SizeSqm", "int64", "#,##0", summarize="sum"),
              column(ST, "OpenDate", "dateTime", "Short Date", date_only=True), column(ST, "Manager", "string")]
store_m = excel("Stores", [], [("StoreID", I64), ("StoreName", TXT), ("City", TXT), ("Region", TXT), ("StoreType", TXT),
                               ("SizeSqm", I64), ("OpenDate", DT), ("Manager", TXT)])
E = "Employees"
emp_cols = [column(E, "EmployeeID", "int64", "0", hidden=True), column(E, "EmployeeName", "string"),
            column(E, "StoreID", "int64", "0", hidden=True, desc="Home store; not related to Stores to avoid a second filter path to Sales."),
            column(E, "Role", "string"), column(E, "HireDate", "dateTime", "Short Date", date_only=True)]
emp_m = excel("Employees", [], [("EmployeeID", I64), ("EmployeeName", TXT), ("StoreID", I64), ("Role", TXT), ("HireDate", DT)])
CM = "Campaigns"
camp_cols = [column(CM, "CampaignID", "int64", "0", hidden=True), column(CM, "CampaignName", "string"), column(CM, "Campaign Channel", "string"),
             column(CM, "StartDate", "dateTime", "Short Date", date_only=True), column(CM, "EndDate", "dateTime", "Short Date", date_only=True),
             column(CM, "Budget", "decimal", "#,##0", summarize="sum")]
camp_m = excel("Campaigns", [("Renamed Channel", 'Table.RenameColumns({prev}, {{{{"Channel", "Campaign Channel"}}}})')],
               [("CampaignID", I64), ("CampaignName", TXT), ("Campaign Channel", TXT), ("StartDate", DT), ("EndDate", DT), ("Budget", CUR)])
TG = "Targets"
tgt_cols = [column(TG, "Month", "dateTime", "Short Date", hidden=True, date_only=True), column(TG, "Region", "string", hidden=True),
            column(TG, "Category", "string", hidden=True), column(TG, "TargetAmount", "decimal", "#,##0", hidden=True, summarize="sum")]
tgt_m = excel("Targets", [], [("Month", DT), ("Region", TXT), ("Category", TXT), ("TargetAmount", CUR)])


def distinct_dim(item, col):
    return ["let", f'{T}Source = Excel.Workbook(File.Contents(DataFolder & "SalesSample.xlsx"), null, true),',
            f'{T}#"Targets Table" = Source{{[Item="Targets",Kind="Table"]}}[Data],',
            f'{T}#"Kept {col}" = Table.Distinct(Table.SelectColumns(#"Targets Table", {{"{col}"}})),',
            f'{T}#"Set Column Types" = Table.TransformColumnTypes(#"Kept {col}", {{{{"{col}", type text}}}})', "in", f'{T}#"Set Column Types"']


# ------------------------------------------------------------------ Date
D = "Date"
season_rules = [
    'Ramadan = {{#date(2023,3,23), #date(2023,4,20)}, {#date(2024,3,11), #date(2024,4,9)}, {#date(2025,3,1), #date(2025,3,29)}},',
    'EidFitr = {#date(2023,4,21), #date(2024,4,10), #date(2025,3,30)},',
    'EidAdha = {#date(2023,6,28), #date(2024,6,16), #date(2025,6,6)},',
]
date_m = ["let", f"{T}StartDate = #date(2023, 1, 1),", f"{T}EndDate = #date(2025, 12, 31),"] + [f"{T}{r}" for r in season_rules] + [
    f'{T}SeasonOf = (d as date) as text =>',
    f'{T*2}let',
    f'{T*3}y = Date.Year(d), md = Date.Month(d) * 100 + Date.Day(d),',
    f'{T*3}inRamadan = List.AnyTrue(List.Transform(Ramadan, each d >= _{{0}} and d <= _{{1}})),',
    f'{T*3}inFitr = List.AnyTrue(List.Transform(EidFitr, each d >= _ and d <= Date.AddDays(_, 3))),',
    f'{T*3}inAdha = List.AnyTrue(List.Transform(EidAdha, each d >= _ and d <= Date.AddDays(_, 3)))',
    f'{T*2}in',
    f'{T*3}if inRamadan then "Ramadan" else if inFitr then "Eid al-Fitr" else if inAdha then "Eid al-Adha"',
    f'{T*3}else if md >= 220 and md <= 223 then "Founding Day" else if md >= 918 and md <= 924 then "National Day"',
    f'{T*3}else if md >= 1120 and md <= 1130 then "White Friday" else if md >= 815 and md <= 905 then "Back to School"',
    f'{T*3}else if md >= 601 and md <= 831 then "Summer" else "Regular",',
    f'{T}#"Date List" = List.Dates(StartDate, Duration.Days(EndDate - StartDate) + 1, #duration(1, 0, 0, 0)),',
    f'{T}#"Date Table" = Table.FromList(#"Date List", Splitter.SplitByNothing(), {{"Date"}}),',
    f'{T}#"Added Year" = Table.AddColumn(#"Date Table", "Year", each Date.Year([Date])),',
    f'{T}#"Added Quarter" = Table.AddColumn(#"Added Year", "Quarter", each "Q" & Text.From(Date.QuarterOfYear([Date]))),',
    f'{T}#"Added Month Number" = Table.AddColumn(#"Added Quarter", "Month Number", each Date.Month([Date])),',
    f'{T}#"Added Month" = Table.AddColumn(#"Added Month Number", "Month", each Date.ToText([Date], "MMM", "en-US")),',
    f'{T}#"Added Year Month Number" = Table.AddColumn(#"Added Month", "Year Month Number", each Date.Year([Date]) * 100 + Date.Month([Date])),',
    f'{T}#"Added Month Year" = Table.AddColumn(#"Added Year Month Number", "Month Year", each Date.ToText([Date], "MMM yyyy", "en-US")),',
    f'{T}#"Added Week" = Table.AddColumn(#"Added Month Year", "Week", each Date.WeekOfYear([Date], Day.Sunday)),',
    f'{T}#"Added Day of Week Number" = Table.AddColumn(#"Added Week", "Day of Week Number", each Date.DayOfWeek([Date], Day.Sunday) + 1),',
    f'{T}#"Added Day Name" = Table.AddColumn(#"Added Day of Week Number", "Day Name", each Date.ToText([Date], "ddd", "en-US")),',
    f'{T}#"Added Is Weekend" = Table.AddColumn(#"Added Day Name", "Is Weekend", each Date.DayOfWeek([Date], Day.Sunday) >= 5),',
    f'{T}#"Added Retail Season" = Table.AddColumn(#"Added Is Weekend", "Retail Season", each SeasonOf([Date])),',
    f'{T}#"Set Column Types" = Table.TransformColumnTypes(#"Added Retail Season", {{{{"Date", type date}}, {{"Year", Int64.Type}}, {{"Quarter", type text}}, {{"Month Number", Int64.Type}}, {{"Month", type text}}, {{"Year Month Number", Int64.Type}}, {{"Month Year", type text}}, {{"Week", Int64.Type}}, {{"Day of Week Number", Int64.Type}}, {{"Day Name", type text}}, {{"Is Weekend", type logical}}, {{"Retail Season", type text}}}})',
    "in", f'{T}#"Set Column Types"']
date_cols = [column(D, "Date", "dateTime", "Short Date", key=True, date_only=True), column(D, "Year", "int64", "0"),
             column(D, "Quarter", "string"), column(D, "Month Number", "int64", "0", hidden=True), column(D, "Month", "string", sort_by="Month Number"),
             column(D, "Year Month Number", "int64", "0", hidden=True), column(D, "Month Year", "string", sort_by="Year Month Number"),
             column(D, "Week", "int64", "0"), column(D, "Day of Week Number", "int64", "0", hidden=True),
             column(D, "Day Name", "string", sort_by="Day of Week Number", desc="Short day name; the week starts on Sunday (KSA)."),
             column(D, "Is Weekend", "boolean", desc="Friday and Saturday (KSA weekend)."),
             column(D, "Retail Season", "string", desc="Ramadan, Eid al-Fitr (4 days), Eid al-Adha (4 days), Founding Day, National Day, White Friday, Back to School, Summer or Regular.")]

# ------------------------------------------------------------------ measures
M = []
POS_D, NEG_D, NEU_D, AMB_D = "#4CC38A", "#F2706C", "#8B93A7", "#E0B04C"
POS_L, NEG_L, NEU_L, AMB_L = "#1E7F4F", "#C23B33", "#6B7280", "#9A6700"


def add(name, folder, fmt, desc, *lines):
    M.append((name, folder, fmt, desc, list(lines)))


def cy(expr):
    return ["VAR _LatestYear = MAX ( 'Date'[Year] )", "RETURN", f"    CALCULATE ( {expr}, KEEPFILTERS ( 'Date'[Year] = _LatestYear ) )"]


def py(expr):
    return ["VAR _LatestYear = MAX ( 'Date'[Year] )", "RETURN", "    CALCULATE (", f"        CALCULATE ( {expr}, SAMEPERIODLASTYEAR ( 'Date'[Date] ) ),",
            "        KEEPFILTERS ( 'Date'[Year] = _LatestYear )", "    )"]


def growth(cur, prev):
    return [f"VAR _Current = {cur}", f"VAR _Previous = {prev}", "RETURN", "    DIVIDE ( _Current - _Previous, _Previous )"]


def diff(cur, prev, scale=1):
    s = f" * {scale}" if scale != 1 else ""
    return [f"VAR _Current = {cur}", f"VAR _Previous = {prev}", "RETURN", f"    IF ( NOT ISBLANK ( _Previous ) && NOT ISBLANK ( _Current ), ( _Current - _Previous ){s} )"]


MONEY, PCT, INT, DELTA, PTS, DEC1, DEC2 = "#,##0", "0.0%", "#,##0", "+0.0%;-0.0%;0.0%", "+0.0;-0.0;0.0", "#,##0.0", "#,##0.00"
F = dict(sales="Sales", orders="Orders", cust="Customers", exp="Experience", pay="Payments", store="Stores", mkt="Marketing",
         tgt="Targets", ti="Time Intelligence", cy="KPI\\Current Year", py="KPI\\Prior Year", vs="KPI\\vs PY", lbl="KPI\\Labels",
         clr="KPI\\Colors", ins="Insights", fmt="Formatting", rank="Rankings")

# base measures
add("Total Sales", F["sales"], MONEY, "Net sales: sum of Sales[SalesAmount] (after discount, before returns).", "SUM ( Sales[SalesAmount] )")
add("Total Cost", F["sales"], MONEY, "Cost of goods: sum of Sales[CostAmount].", "SUM ( Sales[CostAmount] )")
add("Gross Margin", F["sales"], MONEY, "Total Sales minus Total Cost.", "[Total Sales] - [Total Cost]")
add("Margin %", F["sales"], PCT, "Gross Margin / Total Sales.", "DIVIDE ( [Gross Margin], [Total Sales] )")
add("Gross Sales (List)", F["sales"], MONEY, "Sales at list price before discount (Quantity x UnitPrice).", "SUMX ( Sales, Sales[Quantity] * Sales[UnitPrice] )")
add("Discount Amount", F["sales"], MONEY, "List-price value minus net sales.", "[Gross Sales (List)] - [Total Sales]")
add("Discount %", F["sales"], PCT, "Discount depth weighted by list value.", "DIVIDE ( [Discount Amount], [Gross Sales (List)] )")
add("Discounted Sales %", F["sales"], PCT, "Share of net sales sold with any discount.",
    "DIVIDE ( CALCULATE ( [Total Sales], KEEPFILTERS ( Sales[Discount] > 0 ) ), [Total Sales] )")
add("Shipping Cost", F["sales"], MONEY, "Shipping cost of online orders.", "SUM ( Sales[ShippingCost] )")
add("Returned Sales", F["sales"], MONEY, "Net sales value of returned lines.", "CALCULATE ( [Total Sales], KEEPFILTERS ( Sales[IsReturned] = TRUE () ) )")
add("Returned Cost", F["sales"], MONEY, "Cost of returned lines (stock assumed resaleable).", "CALCULATE ( [Total Cost], KEEPFILTERS ( Sales[IsReturned] = TRUE () ) )")
add("Return Rate %", F["sales"], PCT, "Returned Sales / Total Sales (value based).", "DIVIDE ( [Returned Sales], [Total Sales] )")
add("Net Sales", F["sales"], MONEY, "Total Sales after returns.", "[Total Sales] - [Returned Sales]")
add("Net Margin", F["sales"], MONEY, "Margin after returns and shipping: (Sales - Returned Sales) - (Cost - Returned Cost) - Shipping Cost.",
    "( [Total Sales] - [Returned Sales] ) - ( [Total Cost] - [Returned Cost] ) - [Shipping Cost]")
add("Net Margin %", F["sales"], PCT, "Net Margin / Net Sales.", "DIVIDE ( [Net Margin], [Net Sales] )")
add("Avg Selling Price", F["sales"], MONEY, "Net sales per unit.", "DIVIDE ( [Total Sales], [Total Units] )")
add("Sales Change vs PY", F["sales"], "+#,##0;-#,##0;0", "Sales CY minus Sales PY (used by the growth bridge).", "[Sales CY] - [Sales PY]")
add("Total Orders", F["orders"], INT, "Distinct orders.", "DISTINCTCOUNT ( Sales[OrderID] )")
add("Total Units", F["orders"], INT, "Units sold.", "SUM ( Sales[Quantity] )")
add("AOV", F["orders"], MONEY, "Average order value.", "DIVIDE ( [Total Sales], [Total Orders] )")
add("UPT", F["orders"], DEC2, "Units per transaction (units / orders).", "DIVIDE ( [Total Units], [Total Orders] )")
add("Lines per Order", F["orders"], DEC2, "Basket size: order lines per order.", "DIVIDE ( COUNTROWS ( Sales ), [Total Orders] )")
add("Active Customers", F["cust"], INT, "Distinct customers with an order.", "DISTINCTCOUNT ( Sales[CustomerID] )")
add("New Customers", F["cust"], INT, "Active customers whose first-ever order falls in the dates in context (FirstOrderDate via TREATAS).",
    "VAR _Dates = VALUES ( 'Date'[Date] )", "RETURN", "    COALESCE ( CALCULATE ( [Active Customers], TREATAS ( _Dates, Customers[FirstOrderDate] ) ), 0 )")
add("Returning Customers", F["cust"], INT, "Active customers who had ordered before the period.", "[Active Customers] - [New Customers]")
add("New Customer %", F["cust"], PCT, "New Customers / Active Customers.", "DIVIDE ( [New Customers], [Active Customers] )")
add("Repeat Purchase Rate", F["cust"], PCT, "Share of active customers with two or more orders in the period.",
    "VAR _Customers =", "    ADDCOLUMNS ( VALUES ( Sales[CustomerID] ), \"@Orders\", CALCULATE ( DISTINCTCOUNT ( Sales[OrderID] ) ) )",
    "RETURN", "    DIVIDE ( COUNTROWS ( FILTER ( _Customers, [@Orders] >= 2 ) ), COUNTROWS ( _Customers ) )")
add("Customer Retention %", F["cust"], PCT, "Customers active in the prior year who bought again in the latest year in context.",
    "VAR _LatestYear = MAX ( 'Date'[Year] )",
    "VAR _CY = CALCULATETABLE ( VALUES ( Sales[CustomerID] ), KEEPFILTERS ( 'Date'[Year] = _LatestYear ) )",
    "VAR _PY = CALCULATETABLE ( VALUES ( Sales[CustomerID] ), 'Date'[Year] = _LatestYear - 1 )",
    "RETURN", "    DIVIDE ( COUNTROWS ( INTERSECT ( _CY, _PY ) ), COUNTROWS ( _PY ) )")
add("Lifetime Sales per Customer", F["cust"], MONEY, "CLV proxy: all-time net sales per customer (ignores the Date filter).",
    "DIVIDE ( CALCULATE ( [Total Sales], REMOVEFILTERS ( 'Date' ) ), CALCULATE ( [Active Customers], REMOVEFILTERS ( 'Date' ) ) )")
add("Customer Count", F["cust"], INT, "Rows in Customers (not filtered by Date).", "COUNTROWS ( Customers )")
add("Avg Rating", F["exp"], "0.00", "Average customer rating (1-5) of rated lines.", "AVERAGE ( Sales[CustomerRating] )")
add("% Detractors", F["exp"], PCT, "Share of ratings that are 1 or 2.",
    "DIVIDE ( CALCULATE ( COUNT ( Sales[CustomerRating] ), KEEPFILTERS ( Sales[CustomerRating] <= 2 ) ), COUNT ( Sales[CustomerRating] ) )")
add("Avg Delivery Days", F["exp"], DEC1, "Average delivery days of online lines.", "AVERAGE ( Sales[DeliveryDays] )")
add("% Late Deliveries", F["exp"], PCT, "Share of online lines delivered in more than 3 days.",
    "DIVIDE ( CALCULATE ( COUNT ( Sales[DeliveryDays] ), KEEPFILTERS ( Sales[DeliveryDays] > 3 ) ), COUNT ( Sales[DeliveryDays] ) )")
add("BNPL Sales", F["pay"], MONEY, "Net sales paid with Tabby or Tamara.", "CALCULATE ( [Total Sales], KEEPFILTERS ( Sales[Payment Type] = \"BNPL\" ) )")
add("BNPL Share %", F["pay"], PCT, "BNPL Sales / Total Sales.", "DIVIDE ( [BNPL Sales], [Total Sales] )")
add("Selling Area (sqm)", F["store"], INT, "Selling area of physical stores in context.", "SUM ( Stores[SizeSqm] )")
add("Sales per sqm", F["store"], MONEY, "Physical-store net sales per square metre.",
    "DIVIDE ( CALCULATE ( [Total Sales], KEEPFILTERS ( Stores[StoreType] <> \"Online\" ) ), [Selling Area (sqm)] )")
add("Sales per Employee", F["store"], MONEY, "Net sales per employee who served at least one order.", "DIVIDE ( [Total Sales], DISTINCTCOUNT ( Sales[EmployeeID] ) )")
add("Campaign Sales", F["mkt"], MONEY, "Net sales attributed to a campaign.", "CALCULATE ( [Total Sales], KEEPFILTERS ( NOT ISBLANK ( Sales[CampaignID] ) ) )")
add("Organic Sales", F["mkt"], MONEY, "Net sales without a campaign.", "[Total Sales] - [Campaign Sales]")
add("Campaign Sales %", F["mkt"], PCT, "Campaign Sales / Total Sales.", "DIVIDE ( [Campaign Sales], [Total Sales] )")
add("Campaign Budget", F["mkt"], MONEY, "Budget of campaigns running during the dates in context.",
    "VAR _First = MIN ( 'Date'[Date] )", "VAR _Last = MAX ( 'Date'[Date] )", "RETURN",
    "    SUMX ( FILTER ( Campaigns, Campaigns[StartDate] <= _Last && Campaigns[EndDate] >= _First ), Campaigns[Budget] )")
add("ROAS", F["mkt"], "0.00\"x\"", "Return on ad spend: Campaign Sales / Campaign Budget.", "DIVIDE ( [Campaign Sales], [Campaign Budget] )")
add("Target", F["tgt"], MONEY, "Monthly sales target (region x category).", "SUM ( Targets[TargetAmount] )")
add("Sales vs Target", F["tgt"], "+#,##0;-#,##0;0", "Total Sales minus Target.", "[Total Sales] - [Target]")
add("Target Attainment %", F["tgt"], PCT, "Total Sales / Target.", "DIVIDE ( [Total Sales], [Target] )")

# latest-year (CY) and prior-year (PY) variants
KPIS = [("Sales", "[Total Sales]", MONEY), ("Gross Margin", "[Gross Margin]", MONEY), ("Net Margin", "[Net Margin]", MONEY),
        ("Orders", "[Total Orders]", INT), ("Units", "[Total Units]", INT), ("Customers", "[Active Customers]", INT),
        ("New Customers", "[New Customers]", INT), ("Returned Sales", "[Returned Sales]", MONEY), ("BNPL Sales", "[BNPL Sales]", MONEY),
        ("Campaign Sales", "[Campaign Sales]", MONEY), ("Campaign Budget", "[Campaign Budget]", MONEY), ("Target", "[Target]", MONEY),
        ("Avg Rating", "[Avg Rating]", "0.00"), ("Late Deliveries %", "[% Late Deliveries]", PCT), ("Detractors %", "[% Detractors]", PCT),
        ("Avg Delivery Days", "[Avg Delivery Days]", DEC1), ("Discount %", "[Discount %]", PCT), ("Discounted Sales %", "[Discounted Sales %]", PCT),
        ("Repeat Rate", "[Repeat Purchase Rate]", PCT), ("Sales per sqm", "[Sales per sqm]", MONEY), ("Sales per Employee", "[Sales per Employee]", MONEY),
        ("UPT", "[UPT]", DEC2)]
for name, expr, fmt in KPIS:
    add(f"{name} CY", F["cy"], fmt, f"{name} for the latest year in the current filter context.", *cy(expr))
    if name not in ("Target",):
        add(f"{name} PY", F["py"] if name != "Sales" else F["ti"], fmt,
            f"{name} for the same period one year before the latest year in context." +
            (" With one year selected this equals SAMEPERIODLASTYEAR." if name == "Sales" else ""), *py(expr))
for name, num, den, fmt in [("Margin %", "Gross Margin", "Sales", PCT), ("Net Margin %", "Net Margin", "Sales", PCT), ("AOV", "Sales", "Orders", MONEY),
                            ("Return Rate", "Returned Sales", "Sales", PCT), ("BNPL Share", "BNPL Sales", "Sales", PCT),
                            ("ROAS", "Campaign Sales", "Campaign Budget", "0.00\"x\""), ("ASP", "Sales", "Units", MONEY),
                            ("Sales per Customer", "Sales", "Customers", MONEY)]:
    add(f"{name} CY", F["cy"], fmt, f"{name} for the latest year in context.", f"DIVIDE ( [{num} CY], [{den} CY] )")
    add(f"{name} PY", F["py"], fmt, f"{name} for the year before the latest year in context.", f"DIVIDE ( [{num} PY], [{den} PY] )")
add("Attainment CY", F["tgt"], PCT, "Target attainment for the latest year in context.", "DIVIDE ( [Sales CY], [Target CY] )")
add("Gap to Target CY", F["tgt"], "+#,##0;-#,##0;0", "Sales CY minus Target CY.", "[Sales CY] - [Target CY]")

# change measures
CHANGES = [("Sales YoY %", growth("[Sales CY]", "[Sales PY]"), DELTA), ("Gross Margin vs PY %", growth("[Gross Margin CY]", "[Gross Margin PY]"), DELTA),
           ("Orders vs PY %", growth("[Orders CY]", "[Orders PY]"), DELTA), ("AOV vs PY %", growth("[AOV CY]", "[AOV PY]"), DELTA),
           ("Customers vs PY %", growth("[Customers CY]", "[Customers PY]"), DELTA), ("New Customers vs PY %", growth("[New Customers CY]", "[New Customers PY]"), DELTA),
           ("ROAS vs PY %", growth("[ROAS CY]", "[ROAS PY]"), DELTA), ("Units vs PY %", growth("[Units CY]", "[Units PY]"), DELTA),
           ("Margin % vs PY (pts)", diff("[Margin % CY]", "[Margin % PY]", 100), PTS), ("Net Margin % vs PY (pts)", diff("[Net Margin % CY]", "[Net Margin % PY]", 100), PTS),
           ("Return Rate vs PY (pts)", diff("[Return Rate CY]", "[Return Rate PY]", 100), PTS), ("BNPL Share vs PY (pts)", diff("[BNPL Share CY]", "[BNPL Share PY]", 100), PTS),
           ("Late Deliveries vs PY (pts)", diff("[Late Deliveries % CY]", "[Late Deliveries % PY]", 100), PTS),
           ("Avg Rating vs PY", diff("[Avg Rating CY]", "[Avg Rating PY]"), "+0.00;-0.00;0.00")]
for name, lines, fmt in CHANGES:
    add(name, F["vs"] if name != "Sales YoY %" else F["ti"], fmt, f"Change: {name} (latest year in context vs the year before).", *lines)

# YTD and run-rate
add("Sales YTD", F["ti"], MONEY, "Year-to-date sales within the latest year in context.", *cy("CALCULATE ( [Total Sales], DATESYTD ( 'Date'[Date] ) )"))
add("Sales PY YTD", F["ti"], MONEY, "Year-to-date sales for the same dates a year earlier.",
    "VAR _LatestYear = MAX ( 'Date'[Year] )", "RETURN", "    CALCULATE (",
    "        CALCULATE ( [Total Sales], DATESYTD ( SAMEPERIODLASTYEAR ( 'Date'[Date] ) ) ),", "        KEEPFILTERS ( 'Date'[Year] = _LatestYear )", "    )")
add("YTD vs PY %", F["ti"], DELTA, "Sales YTD vs Sales PY YTD.", *growth("[Sales YTD]", "[Sales PY YTD]"))
add("Run-rate FY", F["ti"], MONEY, "Full-year projection: year-to-date sales up to the last order date, scaled to 365/366 days. Equals actual for a complete year.",
    "VAR _LatestYear = MAX ( 'Date'[Year] )", "VAR _YearStart = DATE ( _LatestYear, 1, 1 )", "VAR _YearEnd = DATE ( _LatestYear, 12, 31 )",
    "VAR _LastSale = CALCULATE ( MAX ( Sales[OrderDate] ), REMOVEFILTERS ( 'Date' ), 'Date'[Year] = _LatestYear )",
    "VAR _Ytd = CALCULATE ( [Total Sales], REMOVEFILTERS ( 'Date' ), DATESBETWEEN ( 'Date'[Date], _YearStart, _LastSale ) )",
    "VAR _Elapsed = DATEDIFF ( _YearStart, _LastSale, DAY ) + 1", "RETURN",
    "    DIVIDE ( _Ytd, _Elapsed ) * ( DATEDIFF ( _YearStart, _YearEnd, DAY ) + 1 )")
add("Target FY", F["tgt"], MONEY, "Full-year target of the latest year in context (ignores month filters).",
    "VAR _LatestYear = MAX ( 'Date'[Year] )", "RETURN", "    CALCULATE ( [Target], REMOVEFILTERS ( 'Date' ), 'Date'[Year] = _LatestYear )")
add("Run-rate vs Target %", F["tgt"], DELTA, "Run-rate FY vs Target FY.", *growth("[Run-rate FY]", "[Target FY]"))

# labels and colours (dark and light variants)
LABELS = [("Sales", "[Sales YoY %]", "pct", 1, "[Sales PY]", "money"), ("Gross Margin", "[Gross Margin vs PY %]", "pct", 1, "[Gross Margin PY]", "money"),
          ("Margin %", "[Margin % vs PY (pts)]", "pts", 1, "[Margin % PY]", "pct"), ("Net Margin %", "[Net Margin % vs PY (pts)]", "pts", 1, "[Net Margin % PY]", "pct"),
          ("Orders", "[Orders vs PY %]", "pct", 1, "[Orders PY]", "count"), ("AOV", "[AOV vs PY %]", "pct", 1, "[AOV PY]", "money"),
          ("Customers", "[Customers vs PY %]", "pct", 1, "[Customers PY]", "count"), ("New Customers", "[New Customers vs PY %]", "pct", 1, "[New Customers PY]", "count"),
          ("ROAS", "[ROAS vs PY %]", "pct", 1, "[ROAS PY]", "ratio"), ("Return Rate", "[Return Rate vs PY (pts)]", "pts", -1, "[Return Rate PY]", "pct"),
          ("BNPL Share", "[BNPL Share vs PY (pts)]", "pts", 0, "[BNPL Share PY]", "pct"), ("Late Deliveries", "[Late Deliveries vs PY (pts)]", "pts", -1, "[Late Deliveries % PY]", "pct"),
          ("Avg Rating", "[Avg Rating vs PY]", "num", 1, "[Avg Rating PY]", "rating"), ("YTD", "[YTD vs PY %]", "pct", 1, "[Sales PY YTD]", "money"),
          ("Units", "[Units vs PY %]", "pct", 1, "[Units PY]", "count")]
PYFMT = {"money": 'IF ( ABS ( _Prior ) >= 1000000, FORMAT ( _Prior / 1000000, "0.0" ) & "M", FORMAT ( _Prior / 1000, "0.0" ) & "K" )',
         "pct": 'FORMAT ( _Prior, "0.0%" )', "count": 'FORMAT ( _Prior, "#,0" )', "ratio": 'FORMAT ( _Prior, "0.00" ) & "x"', "rating": 'FORMAT ( _Prior, "0.00" )'}
for kpi, delta, kind, good, prior, pkind in LABELS:
    body = {"pct": 'FORMAT ( ABS ( _Delta ), "0.0%" )', "pts": 'FORMAT ( ABS ( _Delta ), "0.0" ) & " pts"', "num": 'FORMAT ( ABS ( _Delta ), "0.00" )'}[kind]
    add(f"{kpi} vs PY Label", F["lbl"], None, f"Tile text for {kpi}: arrow, size of the change vs prior year and the prior-year value, or a note when there is no prior-year data.",
        f"VAR _Delta = {delta}", f"VAR _Prior = {prior}", "RETURN", "    IF (", "        ISBLANK ( _Delta ),", '        "No prior-year data",',
        f'        IF ( _Delta >= 0, UNICHAR ( 9650 ), UNICHAR ( 9660 ) ) & " " & {body} & "  vs PY " & {PYFMT[pkind]}', "    )")
    for mode, (pos, neg, neu) in (("", (POS_D, NEG_D, NEU_D)), (" (Light)", (POS_L, NEG_L, NEU_L))):
        up, down = (pos, neg) if good == 1 else (neg, pos) if good == -1 else (neu, neu)
        add(f"{kpi} vs PY Color{mode}", F["clr"], None,
            f"Hex colour for the {kpi} change{' on light pages' if mode else ''}: {'higher is better' if good == 1 else 'lower is better' if good == -1 else 'neutral'}; grey without prior-year data.",
            f"VAR _Delta = {delta}", "RETURN", "    SWITCH (", "        TRUE (),", f'        ISBLANK ( _Delta ), "{neu}",',
            f'        _Delta >= 0, "{up}",', f'        "{down}"', "    )")
add("Attainment Label", F["lbl"], None, "Tile text: Target attainment and the gap in SAR.",
    "VAR _Attainment = [Attainment CY]", "VAR _Gap = [Gap to Target CY]", "RETURN", "    IF (", "        ISBLANK ( _Attainment ),", '        "No target",',
    '        IF ( _Gap >= 0, UNICHAR ( 9650 ), UNICHAR ( 9660 ) ) & " " & FORMAT ( ABS ( _Gap ) / 1000, "#,0.0" ) & "K " & IF ( _Gap >= 0, "above", "below" ) & " target " & FORMAT ( [Target CY] / 1000000, "0.00" ) & "M"', "    )")
for mode, (pos, neg, neu, amb) in (("", (POS_D, NEG_D, NEU_D, AMB_D)), (" (Light)", (POS_L, NEG_L, NEU_L, AMB_L))):
    add(f"Attainment Color{mode}", F["clr"], None, f"Hex colour by target attainment{' (light pages)' if mode else ''}: >=100% green, 90-100% amber, <90% red.",
        "VAR _Attainment = [Attainment CY]", "RETURN", "    SWITCH (", "        TRUE (),", f'        ISBLANK ( _Attainment ), "{neu}",',
        f'        _Attainment >= 1, "{pos}",', f'        _Attainment >= 0.9, "{amb}",', f'        "{neg}"', "    )")
    add(f"Return Rate Color{mode}", F["clr"], None, f"Hex colour for a return rate{' (light pages)' if mode else ''}: red above 12%, amber above 9%.",
        "VAR _Rate = [Return Rate CY]", "RETURN", "    SWITCH (", "        TRUE (),", f'        ISBLANK ( _Rate ), "{neu}",',
        f'        _Rate > 0.12, "{neg}",', f'        _Rate > 0.09, "{amb}",', f'        "{pos}"', "    )")
    add(f"ROAS Color{mode}", F["clr"], None, f"Hex colour for ROAS{' (light pages)' if mode else ''}: green from 1.2x, red below 0.9x.",
        "VAR _Roas = [ROAS CY]", "RETURN", "    SWITCH (", "        TRUE (),", f'        ISBLANK ( _Roas ), "{neu}",',
        f'        _Roas >= 1.2, "{pos}",', f'        _Roas >= 0.9, "{amb}",', f'        "{neg}"', "    )")
HEAT = {"": ["#1A2232", "#2E2F33", "#4A402D", "#6B5631", "#8E6F35"], " (Light)": ["#FFFFFF", "#F7EEDB", "#EFDDB5", "#E5C98C", "#D9B467"]}
for mode, ramp in HEAT.items():
    add(f"Heat Color{mode}", F["fmt"], None, f"Sequential background colour for the weekday x month heatmap{' (light pages)' if mode else ''}, scaled between the smallest and largest visible cell.",
        "VAR _Value = [Sales CY]",
        "VAR _Cells = ALLSELECTED ( 'Date'[Day Name], 'Date'[Day of Week Number], 'Date'[Month], 'Date'[Month Number] )",
        "VAR _Max = MAXX ( _Cells, [Sales CY] )", "VAR _Min = MINX ( _Cells, [Sales CY] )",
        "VAR _Ratio = DIVIDE ( _Value - _Min, _Max - _Min )", "RETURN", "    SWITCH (", "        TRUE (),",
        f'        ISBLANK ( _Value ), "{ramp[0]}",', f'        _Ratio < 0.2, "{ramp[0]}",', f'        _Ratio < 0.4, "{ramp[1]}",',
        f'        _Ratio < 0.6, "{ramp[2]}",', f'        _Ratio < 0.8, "{ramp[3]}",', f'        "{ramp[4]}"', "    )")

# rankings and Pareto
add("Top 10 Customer Sales", F["rank"], MONEY, "Sales CY for the top 10 customers by Sales CY among those shown; blank otherwise.",
    "VAR _Sales = [Sales CY]", "VAR _Rank =", "    IF (", "        ISINSCOPE ( Customers[Customer Label] ),",
    "        RANKX ( ALLSELECTED ( Customers[Customer Label], Customers[LoyaltyTier], Customers[City] ), [Sales CY], , DESC )", "    )",
    "RETURN", "    IF ( NOT ISBLANK ( _Sales ) && _Rank <= 10, _Sales )")
add("Top 10 Product Sales", F["rank"], MONEY, "Sales CY for the top 10 products by Sales CY among those shown; blank otherwise.",
    "VAR _Sales = [Sales CY]", "VAR _Rank =", "    IF (", "        ISINSCOPE ( Products[ProductName] ),",
    "        RANKX ( ALLSELECTED ( Products[ProductName], Products[Brand] ), [Sales CY], , DESC )", "    )",
    "RETURN", "    IF ( NOT ISBLANK ( _Sales ) && _Rank <= 10, _Sales )")
for who, col in (("Customers", "Sales[CustomerID]"), ("Products", "Sales[ProductID]")):
    add(f"Top 20% {who} Share", F["rank"], PCT, f"Pareto: share of Sales CY from the top 20% of {who.lower()} (by Sales CY).",
        f"VAR _Items = FILTER ( VALUES ( {col} ), NOT ISBLANK ( [Sales CY] ) )", "VAR _N = ROUNDUP ( COUNTROWS ( _Items ) * 0.2, 0 )",
        "VAR _Top = TOPN ( _N, _Items, [Sales CY], DESC )", "RETURN", "    DIVIDE ( SUMX ( _Top, [Sales CY] ), [Sales CY] )")
add("Margin Rank", F["rank"], INT, "Rank of the item in the visual by Margin % CY (1 = best).",
    "IF ( HASONEVALUE ( Products[Brand] ), RANKX ( ALLSELECTED ( Products[Brand] ), [Margin % CY], , DESC ) )")

add("Returning Customers CY", F["cy"], INT, "Active customers in the latest year who had ordered before it.", "[Customers CY] - [New Customers CY]")
add("Organic Sales CY", F["cy"], MONEY, "Sales CY without a campaign.", "[Sales CY] - [Campaign Sales CY]")
add("Campaign Share CY", F["cy"], PCT, "Campaign Sales CY / Sales CY.", "DIVIDE ( [Campaign Sales CY], [Sales CY] )")
add("Tier Customer Share %", F["cust"], PCT, "Share of latest-year active customers in the loyalty tier(s) in context.",
    "DIVIDE ( [Customers CY], CALCULATE ( [Customers CY], REMOVEFILTERS ( Customers[LoyaltyTier], Customers[Tier Order] ) ) )")
add("Tier Sales Share %", F["cust"], PCT, "Share of latest-year sales from the loyalty tier(s) in context.",
    "DIVIDE ( [Sales CY], CALCULATE ( [Sales CY], REMOVEFILTERS ( Customers[LoyaltyTier], Customers[Tier Order] ) ) )")

# insights (dynamic narrative)
INS = [
    ("Insight Headline", "Net sales, growth and target attainment for the latest year in context.",
     ["VAR _Year = MAX ( 'Date'[Year] )", "VAR _Sales = [Sales CY]", "VAR _Growth = [Sales YoY %]", "VAR _Attainment = [Attainment CY]", "RETURN",
      '    "Net sales reached SAR " & FORMAT ( _Sales / 1000000, "0.00" ) & "M in " & _Year',
      '        & IF ( NOT ISBLANK ( _Growth ), ", " & FORMAT ( _Growth, "+0.0%;-0.0%" ) & " vs " & ( _Year - 1 ), "" )',
      '        & IF ( NOT ISBLANK ( _Attainment ), ", " & FORMAT ( _Attainment, "0.0%" ) & " of target", "" ) & "."']),
    ("Insight Region", "The region furthest behind its target.",
     ["VAR _Regions = FILTER ( ADDCOLUMNS ( VALUES ( Region[Region] ), \"@Attainment\", [Attainment CY] ), NOT ISBLANK ( [@Attainment] ) )",
      "VAR _Worst = TOPN ( 1, _Regions, [@Attainment], ASC )", "RETURN",
      '    IF ( ISEMPTY ( _Worst ), "No target in this selection.", CONCATENATEX ( _Worst, Region[Region], \" / \" ) & " is furthest from target at " & FORMAT ( MAXX ( _Worst, [@Attainment] ), "0.0%" ) & " attainment." )']),
    ("Insight Channel AOV", "App versus Website average order value.",
     ["VAR _App = CALCULATE ( [AOV CY], Sales[Channel] = \"App\" )", "VAR _Web = CALCULATE ( [AOV CY], Sales[Channel] = \"Website\" )", "RETURN",
      '    "App orders average SAR " & FORMAT ( _App, "#,0" ) & ", " & FORMAT ( ABS ( DIVIDE ( _App - _Web, _Web ) ), "0%" ) & IF ( _App >= _Web, " above", " below" ) & " Website orders."']),
    ("Insight BNPL", "BNPL share of sales now and a year earlier.",
     ["VAR _Now = [BNPL Share CY]", "VAR _Before = [BNPL Share PY]", "RETURN",
      '    "BNPL (Tabby, Tamara) pays for " & FORMAT ( _Now, "0%" ) & " of sales" & IF ( NOT ISBLANK ( _Before ), ", up from " & FORMAT ( _Before, "0%" ) & " a year ago", "" ) & "."']),
    ("Insight Returns", "Brand with the highest return rate and how much of it is sizing.",
     ["VAR _Brands = FILTER ( ADDCOLUMNS ( VALUES ( Products[Brand] ), \"@Rate\", [Return Rate CY] ), NOT ISBLANK ( [@Rate] ) )",
      "VAR _Top = TOPN ( 1, _Brands, [@Rate], DESC )", "VAR _Brand = CONCATENATEX ( _Top, Products[Brand], \" / \" )",
      "VAR _Size = CALCULATE ( DIVIDE ( CALCULATE ( [Returned Sales CY], Sales[ReturnReason] = \"Size\" ), [Returned Sales CY] ), Products[Brand] = _Brand )", "RETURN",
      '    _Brand & " has the highest return rate (" & FORMAT ( MAXX ( _Top, [@Rate] ), "0.0%" ) & "); " & FORMAT ( _Size, "0%" ) & " of its returns are for size."']),
    ("Insight Loyalty", "Platinum share of customers and of sales.",
     ["VAR _Customers = DIVIDE ( CALCULATE ( [Customers CY], Customers[LoyaltyTier] = \"Platinum\" ), [Customers CY] )",
      "VAR _Sales = DIVIDE ( CALCULATE ( [Sales CY], Customers[LoyaltyTier] = \"Platinum\" ), [Sales CY] )", "RETURN",
      '    "Platinum members are " & FORMAT ( _Customers, "0%" ) & " of customers but " & FORMAT ( _Sales, "0%" ) & " of sales."']),
    ("Insight Delivery", "Ratings of late versus on-time deliveries.",
     ["VAR _Late = CALCULATE ( [Avg Rating CY], Sales[DeliveryDays] > 3 )", "VAR _OnTime = CALCULATE ( [Avg Rating CY], Sales[DeliveryDays] <= 3 )", "RETURN",
      '    "Orders delivered in more than 3 days rate " & FORMAT ( _Late, "0.0" ) & " on average, versus " & FORMAT ( _OnTime, "0.0" ) & " when on time."']),
    ("Insight Acquisition", "Best and worst acquisition channel by retention.",
     ["VAR _Channels = FILTER ( ADDCOLUMNS ( VALUES ( Customers[AcquisitionChannel] ), \"@Retention\", [Customer Retention %] ), NOT ISBLANK ( [@Retention] ) )",
      "VAR _Best = TOPN ( 1, _Channels, [@Retention], DESC )", "VAR _Worst = TOPN ( 1, _Channels, [@Retention], ASC )", "RETURN",
      '    CONCATENATEX ( _Best, Customers[AcquisitionChannel], \" / \" ) & " customers retain best (" & FORMAT ( MAXX ( _Best, [@Retention] ), "0%" ) & "); "',
      '        & CONCATENATEX ( _Worst, Customers[AcquisitionChannel], \" / \" ) & " customers retain worst (" & FORMAT ( MAXX ( _Worst, [@Retention] ), "0%" ) & ")."']),
    ("Insight Campaigns", "Best and worst campaign channel by ROAS.",
     ["VAR _Channels = FILTER ( ADDCOLUMNS ( VALUES ( Campaigns[Campaign Channel] ), \"@Roas\", [ROAS CY] ), NOT ISBLANK ( [@Roas] ) )",
      "VAR _Best = TOPN ( 1, _Channels, [@Roas], DESC )", "VAR _Worst = TOPN ( 1, _Channels, [@Roas], ASC )", "RETURN",
      '    CONCATENATEX ( _Best, Campaigns[Campaign Channel], \" / \" ) & " campaigns return SAR " & FORMAT ( MAXX ( _Best, [@Roas] ), "0.00" ) & " per SAR spent; "',
      '        & CONCATENATEX ( _Worst, Campaigns[Campaign Channel], \" / \" ) & " only " & FORMAT ( MAXX ( _Worst, [@Roas] ), "0.00" ) & "."']),
    ("Insight Season", "Share of the year's sales made in Ramadan and the two Eids.",
     ["VAR _LatestYear = MAX ( 'Date'[Year] )",
      "VAR _Peak = CALCULATE ( [Sales CY], KEEPFILTERS ( 'Date'[Retail Season] IN { \"Ramadan\", \"Eid al-Fitr\", \"Eid al-Adha\" } ) )",
      "VAR _PeakDays = CALCULATE ( COUNTROWS ( 'Date' ), 'Date'[Year] = _LatestYear, 'Date'[Retail Season] IN { \"Ramadan\", \"Eid al-Fitr\", \"Eid al-Adha\" } )",
      "VAR _Days = CALCULATE ( COUNTROWS ( 'Date' ), 'Date'[Year] = _LatestYear )", "RETURN",
      '    "Ramadan and Eid bring " & FORMAT ( DIVIDE ( _Peak, [Sales CY] ), "0%" ) & " of the year\'s sales in " & FORMAT ( DIVIDE ( _PeakDays, _Days ), "0%" ) & " of its days."']),
    ("Insight Pareto", "Customer concentration.",
     ['"The top 20% of customers generate " & FORMAT ( [Top 20% Customers Share], "0%" ) & " of sales."']),
    ("Period Label", "Header text naming the compared years.",
     ["VAR _LatestYear = MAX ( 'Date'[Year] )", "RETURN", '    _LatestYear & " vs " & ( _LatestYear - 1 )']),
]
for name, desc, lines in INS:
    add(name, F["ins"], None, desc, *lines)
add("Returned Sales CY", F["cy"], MONEY, "Returned Sales for the latest year in context.", *cy("[Returned Sales]")) if not any(m[0] == "Returned Sales CY" for m in M) else None

# ------------------------------------------------------------------ write measures table
ms = ""
for name, folder, fmt, desc, lines in M:
    ms += f"{T}/// {desc}\n"
    if len(lines) == 1:
        ms += f"{T}measure {q(name)} = {lines[0]}\n"
    else:
        ms += f"{T}measure {q(name)} =\n" + "".join(f"{T*3}{l}\n" for l in lines)
    if fmt:
        ms += f"{T*2}formatString: {fmt}\n"
    ms += f"{T*2}displayFolder: {folder}\n{T*2}lineageTag: {tag('_Measures', 'measure', name)}\n\n"
table("_Measures", "Holds the report measures; its only column is a hidden placeholder",
      [column("_Measures", "Column1", "string", hidden=True)], ["let", f"{T}Source = #table(type table [Column1 = text], {{}})", "in", f"{T}Source"],
      measures=ms)

table("Sales", "Order lines (one row per product per order), 2023-2025.", sales_cols, excel("Sales", sales_steps, SALES_TYPES))
table("Products", "Product dimension: brand, category, collection and price tier.", prod_cols, prod_m)
table("Customers", "Customer dimension with loyalty tier, acquisition channel and first order date.", cust_cols, cust_m)
table("Stores", "Stores, including the Online store used by app and website orders.", store_cols, store_m)
table("Employees", "Store and customer-care staff.", emp_cols, emp_m)
table("Campaigns", "Marketing campaigns with dates and budget.", camp_cols, camp_m)
table("Targets", "Monthly sales targets by region and category (first day of the month).", tgt_cols, tgt_m)
table("Region", "Customer region dimension shared by Customers and Targets.", [column("Region", "Region", "string")], distinct_dim("Targets", "Region"))
table("Category", "Product category dimension shared by Products and Targets.", [column("Category", "Category", "string")], distinct_dim("Targets", "Category"))
table("Date", "Calendar 2023-2025 with KSA weekend and retail seasons (Ramadan and Eid dates per year), marked as the date table.",
      date_cols, date_m, props=["dataCategory: Time"])

# ------------------------------------------------------------------ model, expressions, relationships
TABLES = ["Sales", "Products", "Customers", "Stores", "Employees", "Campaigns", "Targets", "Region", "Category", "Date", "_Measures"]
with open(os.path.join(DEF, "model.tmdl"), "w", newline="\n") as f:
    f.write("model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: en-US\n\tdataAccessOptions\n"
            "\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\nannotation __PBI_TimeIntelligenceEnabled = 0\n\n"
            f"annotation PBI_QueryOrder = {json.dumps(['DataFolder'] + TABLES, separators=(',', ':'))}\n\n" +
            "".join(f"ref table {q(t)}\n" for t in TABLES) + "\n")
with open(os.path.join(DEF, "expressions.tmdl"), "w", newline="\n") as f:
    f.write('/// Folder that contains SalesSample.xlsx (must end with a backslash)\n'
            'expression DataFolder = "C:\\PowerBI_Report\\data\\" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
            f"\tlineageTag: {tag('expr', 'DataFolder')}\n\n\tannotation PBI_ResultType = Text\n\n")
RELS = [("Sales.OrderDate", "Date.Date"), ("Sales.CustomerID", "Customers.CustomerID"), ("Sales.ProductID", "Products.ProductID"),
        ("Sales.StoreID", "Stores.StoreID"), ("Sales.EmployeeID", "Employees.EmployeeID"), ("Sales.CampaignID", "Campaigns.CampaignID"),
        ("Customers.Region", "Region.Region"), ("Products.Category", "Category.Category"), ("Targets.Month", "Date.Date"),
        ("Targets.Region", "Region.Region"), ("Targets.Category", "Category.Category")]
with open(os.path.join(DEF, "relationships.tmdl"), "w", newline="\n") as f:
    for a, b in RELS:
        f.write(f"relationship {tag('rel', a, b)}\n\tfromColumn: {a}\n\ttoColumn: {b}\n\n")
print(len(M), "measures")
