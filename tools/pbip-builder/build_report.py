# Builds the FashionVue report: 6 pages x (Dark, Light) twin pages from one spec, + layout.json for the renderer.
# Usage: python3 build_report.py <repo_root> <work_dir> [--write]
#   1) run without --write -> <work_dir>/layout.json + theme.json
#   2) node render_backgrounds.js ... -> <work_dir>/render/*.jpg
#   3) run with --write -> PBIR files + resources in the repo
import hashlib, json, os, shutil, sys

ROOT, SCRATCH = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
TILE_H, ROW2 = 200, 360
NO_SPARK = {"Target FY", "Run-rate FY", "Lifetime Sales per Customer", "Top 20% Products Share", "Customer Retention %"}
WRITE = "--write" in sys.argv
RP = os.path.join(ROOT, "SalesSample.Report")
D = os.path.join(RP, "definition")
FAB = "https://developer.microsoft.com/json-schemas/fabric"
VC = f"{FAB}/item/report/definition/visualContainer/2.1.0/schema.json"
THEME_NAME = "FashionVueExecutive.json"
BG_EXT = "jpg"

PAL = {
    "dark": dict(canvas="#0A0E17", rail="#0E1421", panel="#131A28", panel2="#1A2335", border="#212B3E", grid="#222C3F",
                 text="#F3EFE7", text2="#9AA3B5", accentText="#D9B97A", s1="#BF9640", s2="#6A86C9", s3="#1FA38C",
                 pos="#4CC38A", neg="#F2706C", neutral="#8B93A7", band="#161E2E", tooltip="#1C2538", glow=0.10),
    "light": dict(canvas="#F3EFE8", rail="#FBF9F5", panel="#FFFFFF", panel2="#F7F4EF", border="#E4DDD2", grid="#ECE6DC",
                  text="#1E2230", text2="#5B6273", accentText="#8A6A2A", s1="#97701F", s2="#4466AD", s3="#00876A",
                  pos="#1E7F4F", neg="#C23B33", neutral="#6B7280", band="#FAF8F4", tooltip="#FFFFFF", glow=0.07),
}
MODES = ["dark", "light"]
SUFFIX = {"dark": "", "light": " (Light)"}

X0, CW, G, COL = 128, 1752, 24, 124


def cx(c):
    return X0 + c * (COL + G)


def span(n):
    return n * COL + (n - 1) * G


def hid(*parts):
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:20]


PAGES = [dict(key="exec", name="Executive Summary", icon="layout-dashboard", nav="Summary"),
         dict(key="targets", name="Sales & Targets", icon="target", nav="Targets"),
         dict(key="products", name="Products & Brands", icon="shirt", nav="Products"),
         dict(key="customers", name="Customers", icon="users", nav="Customers"),
         dict(key="ops", name="Operations & Experience", icon="truck", nav="Operations"),
         dict(key="marketing", name="Marketing", icon="megaphone", nav="Marketing")]
NAV_Y = [128 + i * 84 for i in range(len(PAGES))]
LEAD = {"Insight Headline": "Performance", "Insight Region": "Targets", "Insight Channel AOV": "Channels", "Insight BNPL": "Payments",
        "Insight Loyalty": "Loyalty", "Insight Acquisition": "Acquisition", "Insight Pareto": "Concentration", "Insight Delivery": "Delivery",
        "Insight Returns": "Returns", "Insight Campaigns": "Campaigns"}


def pid(key, mode):
    return hid("page3", key, mode)


# ------------------------------------------------------------------ field / literal helpers
def col(e, p):
    return {"Column": {"Expression": {"SourceRef": {"Entity": e}}, "Property": p}}


def mea(p):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": p}}


def qref(f):
    k = next(iter(f))
    return f"{f[k]['Expression']['SourceRef']['Entity']}.{f[k]['Property']}"


def proj(f, display=None, active=None):
    p = {"field": f, "queryRef": qref(f), "nativeQueryRef": f[next(iter(f))]["Property"]}
    if display:
        p["displayName"] = display
    if active is not None:
        p["active"] = active
    return p


def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def solid(h):
    return {"solid": {"color": lit(f"'{h}'")}}


def solid_m(name):
    return {"solid": {"color": {"expr": mea(name)}}}


def wild(f, default_id=False):
    s = {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": qref(f)}
    if default_id:
        s["id"] = "default"
    return s


def merge(a, b):
    out = {k: list(v) for k, v in (a or {}).items()}
    for k, v in (b or {}).items():
        out.setdefault(k, []).extend(v)
    return out


AXES = {"lineChart", "clusteredBarChart", "clusteredColumnChart", "columnChart", "barChart", "hundredPercentStackedBarChart",
        "hundredPercentStackedColumnChart", "waterfallChart", "scatterChart"}


def mode_objects(vtype, m):
    """Visual-level colours for the page mode (theme defaults are dark; both modes set them explicitly)."""
    o = {}
    if vtype in AXES:
        o["categoryAxis"] = [{"properties": {"labelColor": solid(m["text2"])}}]
        o["valueAxis"] = [{"properties": {"labelColor": solid(m["text2"]), "gridlineColor": solid(m["grid"])}}]
        o["legend"] = [{"properties": {"labelColor": solid(m["text2"])}}]
        if vtype != "scatterChart":
            o["labels"] = [{"properties": {"color": solid(m["text2"] if vtype != "lineChart" else m["text"])}}]
    if vtype == "scatterChart":
        o["categoryLabels"] = [{"properties": {"color": solid(m["text2"])}}]
        o["categoryAxis"][0]["properties"]["titleColor"] = solid(m["text2"])
        o["valueAxis"][0]["properties"]["titleColor"] = solid(m["text2"])
    if vtype == "waterfallChart":
        o["sentimentColors"] = [{"properties": {"increaseFill": solid(m["pos"]), "decreaseFill": solid(m["neg"]), "totalFill": solid(m["s1"])}}]
    if vtype == "donutChart":
        o["labels"] = [{"properties": {"color": solid(m["text"])}}]
        o["legend"] = [{"properties": {"labelColor": solid(m["text2"])}}]
        o["dataPoint"] = [{"properties": {"borderColor": solid(m["panel"])}}]
    if vtype == "slicer":
        o["items"] = [{"properties": {"fontColor": solid(m["text"]), "background": solid(m["panel2"])}}]
    if vtype in ("pivotTable", "tableEx"):
        o["grid"] = [{"properties": {"gridHorizontalColor": solid(m["border"]), "outlineColor": solid(m["border"])}}]
        o["columnHeaders"] = [{"properties": {"fontColor": solid(m["text2"]), "backColor": solid(m["panel"]), "outlineColor": solid(m["border"])}}]
        o["values"] = [{"properties": {"fontColorPrimary": solid(m["text"]), "backColorPrimary": solid(m["panel"]),
                                       "fontColorSecondary": solid(m["text"]), "backColorSecondary": solid(m["band"]), "outlineColor": solid(m["border"])}}]
        o["total"] = [{"properties": {"fontColor": solid(m["accentText"]), "backColor": solid(m["panel2"])}}]
        if vtype == "pivotTable":
            o["rowHeaders"] = [{"properties": {"fontColor": solid(m["text"]), "backColor": solid(m["panel"]), "outlineColor": solid(m["border"])}}]
    return o


def mode_vco(m):
    return {"visualTooltip": [{"properties": {"background": solid(m["tooltip"]), "titleFontColor": solid(m["text2"]), "valueFontColor": solid(m["text"])}}],
            "visualHeader": [{"properties": {"background": solid(m["panel2"]), "foreground": solid(m["text2"]), "border": solid(m["border"])}}]}


# ------------------------------------------------------------------ page builder (one spec, two modes)
class Page:
    def __init__(self, spec, mode):
        self.spec, self.mode, self.m = spec, mode, PAL[mode]
        self.key, self.id = spec["key"], pid(spec["key"], mode)
        self.visuals, self.panels, self.tiles, self.bullets = [], [], [], []
        self.controls = []

    def add(self, key, x, y, w, h, vtype, query=None, sort=None, objects=None, vco=None, sync=None, label=None, alt=None, style=True):
        v = {"visualType": vtype}
        if query is not None:
            v["query"] = {"queryState": query}
            if sort:
                v["query"]["sortDefinition"] = {"sort": [{"field": f, "direction": d} for f, d in sort]}
        objs = merge(mode_objects(vtype, self.m) if style else {}, objects)
        if objs:
            v["objects"] = objs
        vc = merge(mode_vco(self.m) if style else {}, vco)
        if alt:
            vc["general"] = [{"properties": {"altText": lit("'" + alt.replace("'", "''") + "'")}}]
        if vc:
            v["visualContainerObjects"] = vc
        if sync:
            v["syncGroup"] = sync
        v["drillFilterOtherVisuals"] = True
        z = (len(self.visuals) + 1) * 1000
        self.visuals.append({"$schema": VC, "name": hid("visual3", self.key, self.mode, key),
                             "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z},
                             "visual": v, "_label": label or key})

    # ---- building blocks
    def card(self, key, x, y, w, h, measure, size=None, color=None, units=None, precision=None, label=None, wrap=False, font=None):
        """Classic card: category label off, transparent container, value colour per mode (or a colour measure)."""
        f = mea(measure)
        props = {"color": solid_m(color + SUFFIX[self.mode]) if color else solid(self.m["text"])}
        if size:
            props["fontSize"] = lit(f"{size}D")
        if units is not None:
            props["labelDisplayUnits"] = lit(f"{units}D")
        if precision is not None:
            props["labelPrecision"] = lit(f"{precision}L")
        if font:
            props["fontFamily"] = lit(f"'{font}'")
        objs = {"labels": [{"properties": props}], "categoryLabels": [{"properties": {"show": lit("false")}}]}
        if wrap:
            objs["wordWrap"] = [{"properties": {"show": lit("true")}}]
        self.add(key, x, y, w, h, "card", {"Values": {"projections": [proj(f)]}}, objects=objs, label=label or measure, alt=label or measure,
                 vco={"background": [{"properties": {"show": lit("false")}}], "border": [{"properties": {"show": lit("false")}}],
                      "dropShadow": [{"properties": {"show": lit("false")}}], "title": [{"properties": {"show": lit("false")}}],
                      "padding": [{"properties": {"top": lit("0D"), "bottom": lit("0D"), "left": lit("0D"), "right": lit("0D")}}]})

    def sparkline(self, key, x, y, w, h, measure):
        f = mea(measure)
        self.add(key, x, y, w, h, "lineChart", {"Category": {"projections": [proj(MONTH, active=True)]}, "Y": {"projections": [proj(f, "Trend")]}},
                 sort=[(MONTH, "Ascending")], style=False, label=f"Sparkline {measure}", alt=f"Monthly trend of {measure}",
                 objects={"categoryAxis": [{"properties": {"show": lit("false")}}],
                          "valueAxis": [{"properties": {"show": lit("false"), "gridlineShow": lit("false")}}],
                          "legend": [{"properties": {"show": lit("false")}}],
                          "lineStyles": [{"properties": {"strokeWidth": lit("2L"), "showMarker": lit("false")}}],
                          "dataPoint": [{"properties": {"fill": solid(self.m["s1"])}, "selector": {"metadata": qref(f)}}]},
                 vco={"background": [{"properties": {"show": lit("false")}}], "border": [{"properties": {"show": lit("false")}}],
                      "dropShadow": [{"properties": {"show": lit("false")}}], "title": [{"properties": {"show": lit("false")}}],
                      "visualHeader": [{"properties": {"show": lit("false")}}],
                      "visualTooltip": mode_vco(self.m)["visualTooltip"],
                      "padding": [{"properties": {"top": lit("0D"), "bottom": lit("0D"), "left": lit("0D"), "right": lit("0D")}}]})

    def tile(self, key, x, w, label, icon, measure, delta=None, caption=None, units=None, color=None, spark=None, precision=None):
        y = 136
        self.tiles.append(dict(x=x, y=y, w=w, h=TILE_H, label=label, icon=icon, caption=caption))
        self.card(key + "-v", x + 12, y + 58, w - 24, 60, measure, units=units, precision=precision, label=f"{label} value")
        if delta:
            lbl = delta if delta.endswith("Label") else f"{delta} vs PY Label"
            clr = color or f"{delta} vs PY Color"
            self.card(key + "-d", x + 12, y + 118, w - 24, 30, lbl, size=11, color=clr, font="Segoe UI Semibold", label=f"{label} change")
        spark = measure if spark is None and measure not in NO_SPARK else spark
        if spark:
            self.sparkline(key + "-s", x + 16, y + 152, w - 32, 38, spark)

    def tiles_row(self, items):
        w = (CW - (len(items) - 1) * G) // len(items)
        for i, it in enumerate(items):
            self.tile(f"kpi{i}", X0 + i * (w + G), w, *it[:3], **(it[3] if len(it) > 3 else {}))

    def panel(self, x, y, w, h, title, subtitle):
        self.panels.append(dict(x=x, y=y, w=w, h=h, title=title, subtitle=subtitle))
        return x + 16, y + 80, w - 32, h - 96

    def insights(self, x, y, w, h, title, measures):
        self.panel(x, y, w, h, title, "Written from the data for the selected period")
        step = (h - 96) // len(measures)
        for i, msr in enumerate(measures):
            yy = y + 80 + i * step
            self.bullets.append(dict(x=x + 24, y=yy, text=LEAD.get(msr, "Insight")))
            self.card(f"ins{i}", x + 24, yy + 26, w - 48, step - 32, msr, size=11, wrap=True, font="Segoe UI", label=msr)

    def series(self, pairs, dashed=()):
        o = {"dataPoint": [{"properties": {"fill": solid(c)}, "selector": {"metadata": qref(f)}} for f, c in pairs]}
        if dashed:
            o["lineStyles"] = [{"properties": {"lineStyle": lit("'dashed'")}, "selector": {"metadata": qref(f)}} for f in dashed]
        return o

    def header(self):
        m = self.m
        self.controls = [dict(x=1104, y=28, w=272, h=76, label="COMPARING", kind="text"), dict(x=1400, y=28, w=160, h=76, label="YEAR", kind="text"),
                         dict(x=1584, y=28, w=160, h=76, label="CHANNEL", kind="text"), dict(x=1768, y=28, w=112, h=76, label="MODE", kind="mode")]
        self.card("period", 1104 + 12, 52, 248, 48, "Period Label", size=16, font="Segoe UI Semibold", label="Compared years")
        for k, x, f, grp in (("year", 1400, col("Date", "Year"), "Year"), ("channel", 1584, col("Sales", "Channel"), "Channel")):
            self.add("slicer-" + k, x + 8, 56, 144, 40, "slicer", {"Values": {"projections": [proj(f, active=True)]}},
                     objects={"data": [{"properties": {"mode": lit("'Dropdown'")}}]},
                     sync={"groupName": grp, "fieldChanges": True, "filterChanges": True}, label=f"{grp} slicer", alt=f"{grp} slicer")
        other = "light" if self.mode == "dark" else "dark"
        self.button("mode-toggle", 1768, 28, 112, 76, pid(self.key, other), f"Switch to {other.title()} mode", label="Mode toggle")
        for i, p in enumerate(PAGES):
            self.button("nav-" + p["key"], 12, NAV_Y[i], 72, 72, pid(p["key"], self.mode), f"Go to {p['name']}", label=f"Nav: {p['nav']}")

    def button(self, key, x, y, w, h, target, tip, label):
        self.add(key, x, y, w, h, "actionButton", style=False, label=label, alt=tip, objects={
            "icon": [{"properties": {"shapeType": lit("'blank'")}, "selector": {"id": "default"}}],
            "fill": [{"properties": {"show": lit("false")}}], "outline": [{"properties": {"show": lit("false")}}],
            "text": [{"properties": {"show": lit("false")}}]},
            vco={"background": [{"properties": {"show": lit("false")}}], "border": [{"properties": {"show": lit("false")}}],
                 "dropShadow": [{"properties": {"show": lit("false")}}], "title": [{"properties": {"show": lit("false")}}],
                 "visualHeader": [{"properties": {"show": lit("false")}}],
                 "visualLink": [{"properties": {"show": lit("true"), "type": lit("'PageNavigation'"), "navigationSection": lit(f"'{target}'"),
                                                "tooltip": lit(f"'{tip}'")}}]})


def labels_units(u, precision=1):
    return {"labels": [{"properties": {"show": lit("true"), "labelDisplayUnits": lit(f"{u}D"), "labelPrecision": lit(f"{precision}L")}}]}


SCY, SPY, TCY = mea("Sales CY"), mea("Sales PY"), mea("Target CY")
MONTH = col("Date", "Month")
REGION, CATEGORY = col("Region", "Region"), col("Category", "Category")


def bar(pg, key, x, y, w, h, cat, measures, vtype="clusteredBarChart", sort=None, units=0, colors=None, alt=None, label=None, series=None, precision=1):
    q = {"Category": {"projections": [proj(cat, active=True)]}, "Y": {"projections": [proj(f, d) for f, d in measures]}}
    if series is not None:
        q["Series"] = {"projections": [proj(series, active=True)]}
    objs = labels_units(units, precision) if units is not None else {}
    if colors:
        objs = merge(objs, pg.series(list(zip([f for f, _ in measures], colors))))
    pg.add(key, x, y, w, h, vtype, q, sort=sort, objects=objs, label=label, alt=alt)


def build(spec, mode):
    pg = Page(spec, mode)
    m = pg.m
    pg.header()
    k = spec["key"]
    if k == "exec":
        pg.tiles_row([("NET SALES", "banknote", "Sales CY", dict(delta="Sales")),
                      ("TARGET ATTAINMENT", "target", "Attainment CY", dict(delta="Attainment Label", color="Attainment Color")),
                      ("GROSS MARGIN %", "percent", "Margin % CY", dict(delta="Margin %")),
                      ("ORDERS", "shopping-bag", "Orders CY", dict(delta="Orders", units=1)),
                      ("AVG ORDER VALUE", "receipt", "AOV CY", dict(delta="AOV", units=1)),
                      ("ACTIVE CUSTOMERS", "user-check", "Customers CY", dict(delta="Customers", units=1))])
        x, y, w, h = pg.panel(cx(0), 360, span(8), 368, "Monthly sales vs target", "Net sales by month: latest year, target and prior year (SAR)")
        pg.add("trend", x, y, w, h, "lineChart", {"Category": {"projections": [proj(MONTH, active=True)]},
               "Y": {"projections": [proj(SCY, "This year"), proj(TCY, "Target"), proj(SPY, "Prior year")]}},
               sort=[(MONTH, "Ascending")], objects=pg.series([(SCY, m["s1"]), (TCY, m["s3"]), (SPY, m["s2"])], dashed=[TCY, SPY]),
               label="Sales vs target (line)", alt="Line chart of monthly sales, target and prior year")
        pg.insights(cx(8), 360, span(4), 368, "Key insights", ["Insight Headline", "Insight Region", "Insight Channel AOV"])
        x, y, w, h = pg.panel(cx(0), 752, span(4), 296, "Region vs target", "Net sales and target, latest year")
        bar(pg, "region", x, y, w, h, REGION, [(SCY, "Actual"), (TCY, "Target")], sort=[(SCY, "Descending")], colors=[m["s1"], m["s3"]],
            label="Region vs target (bar)", alt="Bar chart of sales and target by region")
        x, y, w, h = pg.panel(cx(4), 752, span(5), 296, "Growth bridge", "Change in net sales vs prior year by category")
        pg.add("bridge", x, y, w, h, "waterfallChart", {"Category": {"projections": [proj(CATEGORY, active=True)]},
               "Y": {"projections": [proj(mea("Sales Change vs PY"), "Change vs PY")]}}, objects=labels_units(1000),
               label="Growth bridge (waterfall)", alt="Waterfall of sales change vs prior year by category")
        x, y, w, h = pg.panel(cx(9), 752, span(3), 296, "Sales by channel", "Share of net sales, latest year")
        pg.add("channel", x, y, w, h, "donutChart", {"Category": {"projections": [proj(col("Sales", "Channel"), active=True)]},
               "Y": {"projections": [proj(SCY, "Sales")]}}, label="Channel (donut)", alt="Donut of sales share by channel")
    elif k == "targets":
        pg.tiles_row([("SALES YTD", "trending-up", "Sales YTD", dict(delta="YTD")),
                      ("FULL-YEAR TARGET", "flag", "Target FY", dict(caption="Sum of monthly region x category targets")),
                      ("RUN-RATE PROJECTION", "gauge", "Run-rate FY", dict(caption="Projected from the year-to-date pace")),
                      ("GAP TO TARGET", "scale", "Gap to Target CY", dict(delta="Attainment Label", color="Attainment Color"))])
        x, y, w, h = pg.panel(cx(0), 360, span(7), 336, "Attainment by region and category", "Sales CY / Target CY; green >= 100%, amber 90-100%, red < 90%")
        att = mea("Attainment CY")
        pg.add("attmatrix", x, y, w, h, "pivotTable", {"Rows": {"projections": [proj(REGION, active=True)]},
               "Columns": {"projections": [proj(CATEGORY, active=True)]}, "Values": {"projections": [proj(att, "Attainment")]}},
               objects={"values": [{"properties": {"fontColor": solid_m("Attainment Color" + SUFFIX[mode])}, "selector": wild(att)}]},
               label="Attainment matrix", alt="Matrix of target attainment by region and category")
        x, y, w, h = pg.panel(cx(7), 360, span(5), 336, "Actual vs target by month", "Net sales and target, latest year")
        bar(pg, "monthtarget", x, y, w, h, MONTH, [(SCY, "Actual"), (TCY, "Target")], vtype="clusteredColumnChart", sort=[(MONTH, "Ascending")],
            units=None, colors=[m["s1"], m["s3"]], label="Actual vs target (column)", alt="Column chart of monthly sales and target")
        x, y, w, h = pg.panel(cx(0), 720, span(7), 328, "Seasonality heatmap", "Net sales by weekday and month, latest year; stronger gold = higher")
        pg.add("heatmap", x, y, w, h, "pivotTable", {"Rows": {"projections": [proj(col("Date", "Day Name"), active=True)]},
               "Columns": {"projections": [proj(MONTH, active=True)]}, "Values": {"projections": [proj(SCY, "Sales")]}},
               objects={"values": [{"properties": {"backColor": solid_m("Heat Color" + SUFFIX[mode])}, "selector": wild(SCY)}]},
               label="Weekday x month heatmap", alt="Heatmap matrix of sales by weekday and month")
        x, y, w, h = pg.panel(cx(7), 720, span(5), 328, "Sales by retail season", "Net sales, latest year")
        bar(pg, "season", x, y, w, h, col("Date", "Retail Season"), [(SCY, "Sales")], sort=[(SCY, "Descending")],
            label="Retail season (bar)", alt="Bar chart of sales by retail season")
    elif k == "products":
        pg.tiles_row([("UNITS SOLD", "package", "Units CY", dict(delta="Units", units=1)),
                      ("AVG SELLING PRICE", "tag", "ASP CY", dict(caption="Net sales per unit (SAR)", units=1)),
                      ("RETURN RATE", "undo-2", "Return Rate CY", dict(delta="Return Rate")),
                      ("TOP 20% PRODUCTS", "crown", "Top 20% Products Share", dict(caption="Share of sales from the top 20% of products"))])
        x, y, w, h = pg.panel(cx(0), 360, span(7), 352, "Brand performance", "Latest year; bars = net sales, return rate coloured by threshold")
        rr = mea("Return Rate CY")
        pg.add("brands", x, y, w, h, "tableEx", {"Values": {"projections": [
            proj(col("Products", "Brand")), proj(SCY, "Sales"), proj(mea("Sales YoY %"), "YoY"), proj(mea("Margin % CY"), "Margin"),
            proj(rr, "Return rate"), proj(mea("Avg Rating CY"), "Rating")]}}, sort=[(SCY, "Descending")],
            objects={"columnFormatting": [{"properties": {"dataBars": {"positiveColor": solid(m["s1"]), "negativeColor": solid(m["neg"]),
                     "axisColor": solid(m["border"]), "reverseDirection": lit("false"), "hideText": lit("false")}}, "selector": {"metadata": qref(SCY)}}],
                     "values": [{"properties": {"fontColor": solid_m("Return Rate Color" + SUFFIX[mode])}, "selector": wild(rr)}]},
            label="Brand table", alt="Table of brands with sales, growth, margin, return rate and rating")
        x, y, w, h = pg.panel(cx(7), 360, span(5), 352, "Margin vs return rate", "Each bubble is a brand; size = net sales")
        pg.add("scatter", x, y, w, h, "scatterChart", {"Category": {"projections": [proj(col("Products", "Brand"), active=True)]},
               "X": {"projections": [proj(rr, "Return rate")]}, "Y": {"projections": [proj(mea("Margin % CY"), "Margin")]},
               "Size": {"projections": [proj(SCY, "Sales")]}},
               objects={"colorByCategory": [{"properties": {"show": lit("false")}}], "dataPoint": [{"properties": {"defaultColor": solid(m["s1"])}}],
                        "categoryLabels": [{"properties": {"show": lit("true")}}]}, label="Margin vs returns (scatter)",
               alt="Scatter of margin against return rate by brand")
        x, y, w, h = pg.panel(cx(0), 736, span(4), 312, "Price tier mix", "Share of net sales by price tier and category")
        bar(pg, "tiers", x, y, w, h, CATEGORY, [(SCY, "Sales")], vtype="hundredPercentStackedBarChart", units=None,
            series=col("Products", "PriceTier"), label="Price tier mix (100% bar)", alt="100% stacked bar of price tier mix by category")
        x, y, w, h = pg.panel(cx(4), 736, span(4), 312, "Collections", "Net sales by collection, latest year")
        bar(pg, "collections", x, y, w, h, col("Products", "Collection"), [(SCY, "Sales")], sort=[(SCY, "Descending")],
            label="Collections (bar)", alt="Bar chart of sales by collection")
        top = mea("Top 10 Product Sales")
        x, y, w, h = pg.panel(cx(8), 736, span(4), 312, "Top 10 products", "Ranked by net sales, latest year")
        pg.add("top10p", x, y, w, h, "tableEx", {"Values": {"projections": [proj(col("Products", "ProductName"), "Product"),
               proj(col("Products", "Brand")), proj(top, "Sales")]}}, sort=[(top, "Descending")],
               objects={"total": [{"properties": {"totals": lit("false")}}]}, label="Top 10 products", alt="Table of the ten best-selling products")
    elif k == "customers":
        pg.tiles_row([("ACTIVE CUSTOMERS", "user-check", "Customers CY", dict(delta="Customers", units=1)),
                      ("NEW CUSTOMERS", "user-plus", "New Customers CY", dict(delta="New Customers", units=1)),
                      ("RETENTION", "repeat", "Customer Retention %", dict(caption="Prior-year customers who bought again")),
                      ("LIFETIME VALUE", "gem", "Lifetime Sales per Customer", dict(caption="All-time sales per customer (CLV proxy)", units=1))])
        x, y, w, h = pg.panel(cx(0), 360, span(5), 336, "New vs returning customers", "Active customers by month, latest year")
        nc, rc = mea("New Customers CY"), mea("Returning Customers CY")
        bar(pg, "newret", x, y, w, h, MONTH, [(nc, "New"), (rc, "Returning")], vtype="columnChart", sort=[(MONTH, "Ascending")], units=None,
            colors=[m["s1"], m["s2"]], label="New vs returning (stacked column)", alt="Stacked columns of new and returning customers by month")
        x, y, w, h = pg.panel(cx(5), 360, span(4), 336, "Loyalty tiers", "Share of customers vs share of sales, latest year")
        bar(pg, "tiers", x, y, w, h, col("Customers", "LoyaltyTier"), [(mea("Tier Customer Share %"), "Customers"), (mea("Tier Sales Share %"), "Sales")],
            units=None, colors=[m["s2"], m["s1"]], label="Loyalty tiers (bar)", alt="Bar chart of customer and sales share by loyalty tier")
        pg.insights(cx(9), 360, span(3), 336, "Customer insights", ["Insight Loyalty", "Insight Acquisition", "Insight Pareto"])
        x, y, w, h = pg.panel(cx(0), 720, span(5), 328, "Acquisition channel quality", "Latest year; retention vs prior-year customers")
        ret = mea("Customer Retention %")
        pg.add("acq", x, y, w, h, "tableEx", {"Values": {"projections": [proj(col("Customers", "AcquisitionChannel"), "Channel"),
               proj(mea("Customers CY"), "Customers"), proj(nc, "New"), proj(mea("AOV CY"), "AOV"), proj(ret, "Retention"),
               proj(mea("Sales per Customer CY"), "Sales / customer")]}}, sort=[(ret, "Descending")],
               objects={"columnFormatting": [{"properties": {"dataBars": {"positiveColor": solid(m["s2"]), "negativeColor": solid(m["neg"]),
                        "axisColor": solid(m["border"]), "reverseDirection": lit("false"), "hideText": lit("false")}}, "selector": {"metadata": qref(ret)}}]},
               label="Acquisition table", alt="Table of acquisition channels with customers, AOV and retention")
        x, y, w, h = pg.panel(cx(5), 720, span(3), 328, "Age groups", "Net sales, latest year")
        bar(pg, "age", x, y, w, h, col("Customers", "AgeGroup"), [(SCY, "Sales")], label="Age groups (bar)", alt="Bar chart of sales by age group")
        top = mea("Top 10 Customer Sales")
        x, y, w, h = pg.panel(cx(8), 720, span(4), 328, "Top 10 customers", "Ranked by net sales, latest year")
        pg.add("top10c", x, y, w, h, "tableEx", {"Values": {"projections": [proj(col("Customers", "Customer Label"), "Customer"),
               proj(col("Customers", "LoyaltyTier"), "Tier"), proj(col("Customers", "City")), proj(top, "Sales")]}}, sort=[(top, "Descending")],
               objects={"total": [{"properties": {"totals": lit("false")}}]}, label="Top 10 customers", alt="Table of the ten customers with the highest sales")
    elif k == "ops":
        pg.tiles_row([("RETURN RATE", "undo-2", "Return Rate CY", dict(delta="Return Rate")),
                      ("AVG RATING", "star", "Avg Rating CY", dict(delta="Avg Rating")),
                      ("LATE DELIVERIES", "clock", "Late Deliveries % CY", dict(delta="Late Deliveries")),
                      ("BNPL SHARE", "credit-card", "BNPL Share CY", dict(delta="BNPL Share"))])
        x, y, w, h = pg.panel(cx(0), 360, span(4), 336, "Returns by reason", "Returned sales value, latest year")
        bar(pg, "reasons", x, y, w, h, col("Sales", "ReturnReason"), [(mea("Returned Sales CY"), "Returned")], sort=[(mea("Returned Sales CY"), "Descending")],
            label="Return reasons (bar)", alt="Bar chart of returned sales by reason")
        x, y, w, h = pg.panel(cx(4), 360, span(4), 336, "Delivery time vs rating", "Average rating by delivery band, latest year")
        band = col("Sales", "Delivery Band")
        bar(pg, "delivery", x, y, w, h, band, [(mea("Avg Rating CY"), "Rating")], vtype="clusteredColumnChart", sort=[(band, "Ascending")], units=1, precision=2,
            label="Delivery vs rating (column)", alt="Column chart of average rating by delivery band")
        x, y, w, h = pg.panel(cx(8), 360, span(4), 336, "Payment mix", "Share of net sales by payment type and month")
        bar(pg, "payments", x, y, w, h, MONTH, [(SCY, "Sales")], vtype="hundredPercentStackedColumnChart", sort=[(MONTH, "Ascending")], units=None,
            series=col("Sales", "Payment Type"), label="Payment mix (100% column)", alt="100% stacked columns of payment type share by month")
        x, y, w, h = pg.panel(cx(0), 720, span(8), 328, "Store league table", "Latest year; bars = net sales")
        rr = mea("Return Rate CY")
        pg.add("stores", x, y, w, h, "tableEx", {"Values": {"projections": [proj(col("Stores", "StoreName"), "Store"), proj(col("Stores", "StoreType"), "Type"),
               proj(SCY, "Sales"), proj(mea("Sales per sqm CY"), "Sales / sqm"), proj(mea("Sales per Employee CY"), "Sales / employee"),
               proj(mea("Avg Rating CY"), "Rating"), proj(rr, "Return rate")]}}, sort=[(SCY, "Descending")],
               objects={"columnFormatting": [{"properties": {"dataBars": {"positiveColor": solid(m["s1"]), "negativeColor": solid(m["neg"]),
                        "axisColor": solid(m["border"]), "reverseDirection": lit("false"), "hideText": lit("false")}}, "selector": {"metadata": qref(SCY)}}],
                        "values": [{"properties": {"fontColor": solid_m("Return Rate Color" + SUFFIX[mode])}, "selector": wild(rr)}]},
               label="Store league table", alt="Table of stores with sales, sales per sqm, sales per employee, rating and returns")
        pg.insights(cx(8), 720, span(4), 328, "Experience insights", ["Insight Delivery", "Insight Returns", "Insight BNPL"])
    elif k == "marketing":
        pg.tiles_row([("CAMPAIGN SALES", "sparkles", "Campaign Sales CY", dict(caption="Net sales attributed to campaigns")),
                      ("CAMPAIGN BUDGET", "wallet", "Campaign Budget CY", dict(caption="Budget of campaigns running in the period")),
                      ("ROAS", "trending-up", "ROAS CY", dict(delta="ROAS")),
                      ("CAMPAIGN SHARE", "pie-chart", "Campaign Share CY", dict(caption="Share of net sales from campaigns"))])
        x, y, w, h = pg.panel(cx(0), 360, span(7), 352, "Campaign performance", "Latest year; ROAS coloured: green >= 1.2x, red < 0.9x")
        roas = mea("ROAS CY")
        pg.add("campaigns", x, y, w, h, "tableEx", {"Values": {"projections": [proj(col("Campaigns", "CampaignName"), "Campaign"),
               proj(col("Campaigns", "Campaign Channel"), "Channel"), proj(mea("Campaign Budget CY"), "Budget"),
               proj(mea("Campaign Sales CY"), "Sales"), proj(roas, "ROAS")]}}, sort=[(roas, "Descending")],
               objects={"values": [{"properties": {"fontColor": solid_m("ROAS Color" + SUFFIX[mode])}, "selector": wild(roas)}]},
               label="Campaign table", alt="Table of campaigns with budget, sales and ROAS")
        x, y, w, h = pg.panel(cx(7), 360, span(5), 352, "ROAS by channel", "Campaign sales per SAR of budget, latest year")
        bar(pg, "roas", x, y, w, h - 84, col("Campaigns", "Campaign Channel"), [(roas, "ROAS")], sort=[(roas, "Descending")], units=1, precision=2,
            label="ROAS by channel (bar)", alt="Bar chart of ROAS by campaign channel")
        pg.bullets.append(dict(x=x + 8, y=y + h - 76, text="Campaigns"))
        pg.card("ins-campaign", x + 8, y + h - 50, w - 16, 50, "Insight Campaigns", size=11, wrap=True, font="Segoe UI", label="Insight Campaigns")
        x, y, w, h = pg.panel(cx(0), 736, span(7), 312, "Campaign vs organic sales", "Net sales by month, latest year")
        cs, os_ = mea("Campaign Sales CY"), mea("Organic Sales CY")
        bar(pg, "mix", x, y, w, h, MONTH, [(cs, "Campaign"), (os_, "Organic")], vtype="columnChart", sort=[(MONTH, "Ascending")], units=None,
            colors=[m["s1"], m["s2"]], label="Campaign vs organic (stacked column)", alt="Stacked columns of campaign and organic sales by month")
        x, y, w, h = pg.panel(cx(7), 736, span(5), 312, "New customers by acquisition channel", "First-time buyers, latest year")
        bar(pg, "acqnew", x, y, w, h, col("Customers", "AcquisitionChannel"), [(mea("New Customers CY"), "New customers")], sort=[(mea("New Customers CY"), "Descending")],
            units=1, label="New customers by channel (bar)", alt="Bar chart of new customers by acquisition channel")
    return pg


pages = [build(s, md) for md in MODES for s in PAGES]

# ------------------------------------------------------------------ layout.json for the renderer
layout = {"palettes": PAL, "nav": [dict(y=NAV_Y[i], icon=p["icon"], label=p["nav"]) for i, p in enumerate(PAGES)], "pages": []}
for pg in pages:
    layout["pages"].append(dict(key=pg.key, mode=pg.mode, title=pg.spec["name"], bg=f"bg-{pg.key}-{pg.mode}.{BG_EXT}",
                                active=[p["key"] for p in PAGES].index(pg.key), panels=pg.panels, tiles=pg.tiles, bullets=pg.bullets,
                                controls=pg.controls,
                                visuals=[dict(x=v["position"]["x"], y=v["position"]["y"], w=v["position"]["width"], h=v["position"]["height"],
                                              label=v["_label"]) for v in pg.visuals]))
with open(os.path.join(SCRATCH, "layout.json"), "w") as f:
    json.dump(layout, f, indent=1)
print("visuals per page:", {f"{p.key}-{p.mode}": len(p.visuals) for p in pages})

# ------------------------------------------------------------------ theme (dark default)
c = PAL["dark"]
theme = json.load(open(os.path.join(HERE, "theme_template.json")))
theme["name"] = "FashionVue Executive"
theme["dataColors"] = [c["s1"], c["s2"], c["s3"], "#D98E5F", "#A57BD1", "#5FB0D9", "#C9667A", "#8FA35B"]
vs = theme["visualStyles"]
vs.pop("cardVisual", None)
star = vs["*"]["*"]
for ax in ("categoryAxis", "valueAxis"):
    star[ax][0]["fontSize"] = 11
star["legend"][0].update({"position": "Top", "fontSize": 10})
star["labels"][0].update({"fontSize": 10})
vs["card"] = {"*": {"labels": [{"fontFamily": "DIN", "fontSize": 28, "color": {"solid": {"color": c["text"]}}}],
                    "categoryLabels": [{"show": False}], "wordWrap": [{"show": True}]}}
vs["waterfallChart"] = {"*": {"sentimentColors": [{"increaseFill": {"solid": {"color": c["pos"]}}, "decreaseFill": {"solid": {"color": c["neg"]}},
                                                   "totalFill": {"solid": {"color": c["s1"]}}}],
                              "valueAxis": [{"gridlineColor": {"solid": {"color": c["grid"]}}, "gridlineStyle": "dotted", "showAxisTitle": False}],
                              "labels": [{"show": True, "fontSize": 10}]}}
for vt in ("hundredPercentStackedBarChart", "hundredPercentStackedColumnChart", "columnChart"):
    vs[vt] = {"*": {"valueAxis": [{"gridlineColor": {"solid": {"color": c["grid"]}}, "gridlineStyle": "dotted", "showAxisTitle": False}]}}
with open(os.path.join(SCRATCH, "theme.json"), "w") as f:
    json.dump(theme, f, indent=2)

if not WRITE:
    sys.exit(0)


# ------------------------------------------------------------------ write PBIR
def wj(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


reg = os.path.join(RP, "StaticResources", "RegisteredResources")
shutil.rmtree(reg, ignore_errors=True)
os.makedirs(reg)
for lp in layout["pages"]:
    shutil.copyfile(os.path.join(SCRATCH, "render", lp["bg"]), os.path.join(reg, lp["bg"]))
shutil.copyfile(os.path.join(SCRATCH, "theme.json"), os.path.join(reg, THEME_NAME))
report = json.load(open(os.path.join(D, "report.json")))
report["themeCollection"]["customTheme"] = {"name": THEME_NAME, "reportVersionAtImport": "5.65", "type": "RegisteredResources"}
report["objects"] = {"outspacePane": [{"properties": {"expanded": lit("false"), "visible": lit("false")}}]}
report["resourcePackages"] = [r for r in report["resourcePackages"] if r["name"] != "RegisteredResources"] + [{
    "name": "RegisteredResources", "type": "RegisteredResources",
    "items": [{"name": THEME_NAME, "path": THEME_NAME, "type": "CustomTheme"}] +
             [{"name": lp["bg"], "path": lp["bg"], "type": "Image"} for lp in layout["pages"]]}]
wj(os.path.join(D, "report.json"), report)
pd_root = os.path.join(D, "pages")
shutil.rmtree(pd_root)
wj(os.path.join(pd_root, "pages.json"), {"$schema": f"{FAB}/item/report/definition/pagesMetadata/1.0.0/schema.json",
                                         "pageOrder": [p.id for p in pages], "activePageName": pages[0].id})
for pg, lp in zip(pages, layout["pages"]):
    page = {"$schema": f"{FAB}/item/report/definition/page/2.0.0/schema.json", "name": pg.id,
            "displayName": pg.spec["name"] + (" (Light)" if pg.mode == "light" else ""), "displayOption": "FitToPage",
            "height": 1080, "width": 1920,
            "objects": {"background": [{"properties": {"image": {"image": {
                "name": lit(f"'{lp['bg']}'"),
                "url": {"expr": {"ResourcePackageItem": {"PackageName": "RegisteredResources", "PackageType": 1, "ItemName": lp["bg"]}}},
                "scaling": lit("'Fit'")}}, "transparency": lit("0D")}}],
                "outspace": [{"properties": {"color": solid(pg.m["canvas"]), "transparency": lit("0D")}}]}}
    if pg.mode == "light":
        page["visibility"] = "HiddenInViewMode"
    wj(os.path.join(pd_root, pg.id, "page.json"), page)
    for v in pg.visuals:
        wj(os.path.join(pd_root, pg.id, "visuals", v["name"], "visual.json"), {k: val for k, val in v.items() if k != "_label"})
print("report written")
