# Builds the Arabic, right-to-left VehicleSales report: 7 pages x (Dark, Light) twin pages + layout.json for render.js.
# Usage: python3 build_report.py <repo_root> <work_dir> [--write]
import hashlib, json, os, shutil, sys

ROOT, W = sys.argv[1], sys.argv[2]
WRITE = "--write" in sys.argv
NAME, THEME_NAME = "VehicleSales", "MasarHorizon.json"
RP = os.path.join(ROOT, f"{NAME}.Report")
D = os.path.join(RP, "definition")
FAB = "https://developer.microsoft.com/json-schemas/fabric"
VC = f"{FAB}/item/report/definition/visualContainer/2.1.0/schema.json"
FONT = "Tajawal"

PAL = {
    "dark": dict(canvas="#0D0F12", rail="#111418", panel="#16191E", panel2="#1D2127", border="#2A2F37", grid="#262B33", text="#EEF1F4",
                 text2="#9AA3AE", accentText="#3FD9C2", s1="#12A594", s2="#E8793A", s3="#8A93F2", pos="#4CC38A", neg="#F2706C", band="#191C21",
                 tooltip="#1D2127", blueprint="#FFFFFF", bpOpacity=0.035),
    "light": dict(canvas="#EEF0F2", rail="#F7F8F9", panel="#FFFFFF", panel2="#F4F6F8", border="#D9DDE2", grid="#E6E9ED", text="#15181C",
                  text2="#5A626C", accentText="#0E6F64", s1="#00897A", s2="#C2560F", s3="#4A5FA8", pos="#1E7F4F", neg="#C23B33", band="#F8F9FA",
                  tooltip="#FFFFFF", blueprint="#0D0F12", bpOpacity=0.04),
}
MODES, SUFFIX = ["dark", "light"], {"dark": "", "light": " (Light)"}
X0, X1, CW, G, COL = 40, 1792, 1752, 24, 124
TILE_H, ROW2 = 200, 360


def span(n):
    return n * COL + (n - 1) * G


def rx(c, n):
    """x of a block that starts c columns from the right edge and spans n columns (RTL grid)."""
    return X1 - c * (COL + G) - span(n)


def hid(*p):
    return hashlib.sha1("|".join(p).encode()).hexdigest()[:20]


PAGES = [dict(key="cover", name="المقدمة", icon="book-open", nav="المقدمة"),
         dict(key="exec", name="الملخص التنفيذي", icon="layout-dashboard", nav="الملخص"),
         dict(key="sales", name="المبيعات والأهداف", icon="target", nav="المبيعات"),
         dict(key="stock", name="المخزون والطرازات", icon="car", nav="المخزون"),
         dict(key="customers", name="العملاء والتمويل", icon="users", nav="العملاء"),
         dict(key="service", name="خدمات ما بعد البيع", icon="wrench", nav="الصيانة"),
         dict(key="conclusion", name="الخاتمة والتوصيات", icon="flag", nav="الخاتمة")]
NAV_Y = [120 + i * 80 for i in range(len(PAGES))]
LEAD = {"Insight Headline": "الأداء", "Insight Chinese": "العلامات الصينية", "Insight Electrified": "التحول الكهربائي", "Insight Finance": "التمويل",
        "Insight Leads": "مصادر العملاء", "Insight Service": "جودة الصيانة", "Insight Absorption": "الاستيعاب", "Insight Branch Target": "الأهداف",
        "Insight Discount": "الخصومات", "Insight Aged": "المخزون المتقادم"}
NO_SPARK = {"Target FY", "Run-rate FY", "Trade-in Rate CY"}


def pid(key, mode):
    return hid("veh-page", key, mode)


def col(e, p):
    return {"Column": {"Expression": {"SourceRef": {"Entity": e}}, "Property": p}}


def mea(p):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": p}}


def qref(f):
    k = next(iter(f)); return f"{f[k]['Expression']['SourceRef']['Entity']}.{f[k]['Property']}"


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


def solid_m(n):
    return {"solid": {"color": {"expr": mea(n)}}}


def wild(f):
    return {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": qref(f)}


def merge(a, b):
    out = {k: list(v) for k, v in (a or {}).items()}
    for k, v in (b or {}).items():
        out.setdefault(k, []).extend(v)
    return out


AXES = {"lineChart", "clusteredBarChart", "clusteredColumnChart", "columnChart", "hundredPercentStackedColumnChart", "scatterChart"}


def mode_objects(vt, m):
    o = {}
    if vt in AXES:
        o["categoryAxis"] = [{"properties": {"labelColor": solid(m["text2"])}}]
        o["valueAxis"] = [{"properties": {"labelColor": solid(m["text2"]), "gridlineColor": solid(m["grid"])}}]
        o["legend"] = [{"properties": {"labelColor": solid(m["text2"])}}]
        if vt != "scatterChart":
            o["labels"] = [{"properties": {"color": solid(m["text2"])}}]
    if vt == "scatterChart":
        o["categoryLabels"] = [{"properties": {"color": solid(m["text2"])}}]
    if vt == "donutChart":
        o["labels"] = [{"properties": {"color": solid(m["text"])}}]
        o["legend"] = [{"properties": {"labelColor": solid(m["text2"])}}]
        o["dataPoint"] = [{"properties": {"borderColor": solid(m["panel"])}}]
    if vt == "slicer":
        o["items"] = [{"properties": {"fontColor": solid(m["text"]), "background": solid(m["panel2"])}}]
    if vt in ("pivotTable", "tableEx"):
        o["grid"] = [{"properties": {"gridHorizontalColor": solid(m["border"]), "outlineColor": solid(m["border"])}}]
        o["columnHeaders"] = [{"properties": {"fontColor": solid(m["text2"]), "backColor": solid(m["panel"]), "outlineColor": solid(m["border"]),
                                              "alignment": lit("'Right'")}}]
        o["values"] = [{"properties": {"fontColorPrimary": solid(m["text"]), "backColorPrimary": solid(m["panel"]), "fontColorSecondary": solid(m["text"]),
                                       "backColorSecondary": solid(m["band"]), "outlineColor": solid(m["border"])}}]
        o["total"] = [{"properties": {"fontColor": solid(m["accentText"]), "backColor": solid(m["panel2"])}}]
        if vt == "pivotTable":
            o["rowHeaders"] = [{"properties": {"fontColor": solid(m["text"]), "backColor": solid(m["panel"]), "outlineColor": solid(m["border"])}}]
    return o


def mode_vco(m):
    return {"visualTooltip": [{"properties": {"background": solid(m["tooltip"]), "titleFontColor": solid(m["text2"]), "valueFontColor": solid(m["text"])}}],
            "visualHeader": [{"properties": {"background": solid(m["panel2"]), "foreground": solid(m["text2"]), "border": solid(m["border"])}}]}


CLEAR = {"background": [{"properties": {"show": lit("false")}}], "border": [{"properties": {"show": lit("false")}}],
         "dropShadow": [{"properties": {"show": lit("false")}}], "title": [{"properties": {"show": lit("false")}}],
         "padding": [{"properties": {"top": lit("0D"), "bottom": lit("0D"), "left": lit("0D"), "right": lit("0D")}}]}
MONTH = col("Date", "Month")


class Page:
    def __init__(self, spec, mode):
        self.spec, self.mode, self.m, self.key, self.id = spec, mode, PAL[mode], spec["key"], pid(spec["key"], mode)
        self.visuals, self.panels, self.tiles, self.bullets, self.controls, self.extra = [], [], [], [], [], {}

    def add(self, key, x, y, w, h, vt, query=None, sort=None, objects=None, vco=None, sync=None, label=None, alt=None, style=True):
        v = {"visualType": vt}
        if query is not None:
            v["query"] = {"queryState": query}
            if sort:
                v["query"]["sortDefinition"] = {"sort": [{"field": f, "direction": d} for f, d in sort]}
        objs = merge(mode_objects(vt, self.m) if style else {}, objects)
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
        self.visuals.append({"$schema": VC, "name": hid("veh-visual", self.key, self.mode, key),
                             "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z}, "visual": v, "_label": label or key})

    def card(self, key, x, y, w, h, measure, size=None, color=None, units=None, label=None, wrap=False, bold=False):
        props = {"color": solid_m(color + SUFFIX[self.mode]) if color else solid(self.m["text"]), "fontFamily": lit(f"'{FONT}'")}
        if size:
            props["fontSize"] = lit(f"{size}D")
        if units is not None:
            props["labelDisplayUnits"] = lit(f"{units}D")
        if bold:
            props["bold"] = lit("true")
        objs = {"labels": [{"properties": props}], "categoryLabels": [{"properties": {"show": lit("false")}}]}
        if wrap:
            objs["wordWrap"] = [{"properties": {"show": lit("true")}}]
        self.add(key, x, y, w, h, "card", {"Values": {"projections": [proj(mea(measure))]}}, objects=objs, vco=dict(CLEAR),
                 label=label or measure, alt=label or measure)

    def sparkline(self, key, x, y, w, h, measure):
        f = mea(measure)
        self.add(key, x, y, w, h, "lineChart", {"Category": {"projections": [proj(MONTH, active=True)]}, "Y": {"projections": [proj(f, "الاتجاه")]}},
                 sort=[(MONTH, "Ascending")], style=False, label=f"Sparkline {measure}", alt=f"اتجاه شهري - {measure}",
                 objects={"categoryAxis": [{"properties": {"show": lit("false")}}], "valueAxis": [{"properties": {"show": lit("false"), "gridlineShow": lit("false")}}],
                          "legend": [{"properties": {"show": lit("false")}}], "lineStyles": [{"properties": {"strokeWidth": lit("2L"), "showMarker": lit("false")}}],
                          "dataPoint": [{"properties": {"fill": solid(self.m["s1"])}, "selector": {"metadata": qref(f)}}]},
                 vco=merge(dict(CLEAR), {"visualHeader": [{"properties": {"show": lit("false")}}], "visualTooltip": mode_vco(self.m)["visualTooltip"]}))

    def tile(self, i, x, w, label, icon, measure, delta=None, color=None, caption=None, units=None):
        y = 136
        self.tiles.append(dict(x=x, y=y, w=w, h=TILE_H, label=label, icon=icon, caption=caption))
        self.card(f"kpi{i}-v", x + 12, y + 58, w - 24, 60, measure, size=26, units=units, bold=True, label=f"{label} القيمة")
        if delta:
            lbl = delta if delta.endswith("Label") else f"{delta} vs PY Label"
            self.card(f"kpi{i}-d", x + 12, y + 118, w - 24, 30, lbl, size=11, color=color or f"{delta} vs PY Color", label=f"{label} التغير")
        if measure not in NO_SPARK:
            self.sparkline(f"kpi{i}-s", x + 16, y + 152, w - 32, 38, measure)

    def tiles_row(self, items):
        w = (CW - (len(items) - 1) * G) // len(items)
        for i, it in enumerate(items):
            self.tile(i, X1 - (i + 1) * w - i * G, w, *it[:3], **(it[3] if len(it) > 3 else {}))

    def panel(self, x, y, w, h, title, subtitle):
        self.panels.append(dict(x=x, y=y, w=w, h=h, title=title, subtitle=subtitle))
        return x + 16, y + 80, w - 32, h - 96

    def insights(self, x, y, w, h, title, measures, numbered=False, subtitle="مكتوبة آلياً من البيانات للفترة المختارة"):
        self.panel(x, y, w, h, title, subtitle)
        step = (h - 96) // len(measures)
        for i, msr in enumerate(measures):
            yy = y + 80 + i * step
            self.bullets.append(dict(x=x + w - 44, y=yy, text=LEAD.get(msr, ""), num=(i + 1) if numbered else None))
            self.card(f"ins-{msr}", x + 24, yy + (26 if LEAD.get(msr) else 0), w - 72, step - (32 if LEAD.get(msr) else 8), msr, size=12, wrap=True, label=msr)

    def series(self, pairs, dashed=()):
        o = {"dataPoint": [{"properties": {"fill": solid(c)}, "selector": {"metadata": qref(f)}} for f, c in pairs]}
        if dashed:
            o["lineStyles"] = [{"properties": {"lineStyle": lit("'dashed'")}, "selector": {"metadata": qref(f)}} for f in dashed]
        return o

    def button(self, key, x, y, w, h, target, tip, label):
        self.add(key, x, y, w, h, "actionButton", style=False, label=label, alt=tip, objects={
            "icon": [{"properties": {"shapeType": lit("'blank'")}, "selector": {"id": "default"}}], "fill": [{"properties": {"show": lit("false")}}],
            "outline": [{"properties": {"show": lit("false")}}], "text": [{"properties": {"show": lit("false")}}]},
            vco={"background": [{"properties": {"show": lit("false")}}], "border": [{"properties": {"show": lit("false")}}],
                 "dropShadow": [{"properties": {"show": lit("false")}}], "title": [{"properties": {"show": lit("false")}}],
                 "visualHeader": [{"properties": {"show": lit("false")}}],
                 "visualLink": [{"properties": {"show": lit("true"), "type": lit("'PageNavigation'"), "navigationSection": lit(f"'{target}'"), "tooltip": lit(f"'{tip}'")}}]})

    def chrome(self, slicers=True):
        other = "light" if self.mode == "dark" else "dark"
        self.controls = [dict(x=40, y=28, w=112, h=76, label="الوضع", kind="mode")]
        self.button("mode-toggle", 40, 28, 112, 76, pid(self.key, other), "التبديل إلى الوضع " + ("الفاتح" if other == "light" else "الداكن"), "Mode toggle")
        if slicers:
            self.controls += [dict(x=176, y=28, w=160, h=76, label="السنة", kind="text"), dict(x=360, y=28, w=200, h=76, label="الفرع", kind="text"),
                              dict(x=584, y=28, w=272, h=76, label="المقارنة", kind="text")]
            for k, x, w, f, grp in (("year", 176, 160, col("Date", "Year"), "Year"), ("branch", 360, 200, col("Branches", "BranchName"), "Branch")):
                self.add("slicer-" + k, x + 8, 56, w - 16, 40, "slicer", {"Values": {"projections": [proj(f, active=True)]}},
                         objects={"data": [{"properties": {"mode": lit("'Dropdown'")}}]}, sync={"groupName": grp, "fieldChanges": True, "filterChanges": True},
                         label=f"{grp} slicer", alt="تصفية حسب " + ("السنة" if grp == "Year" else "الفرع"))
            self.card("period", 596, 52, 248, 48, "Period Label", size=16, bold=True, label="سنوات المقارنة")
        for i, p in enumerate(PAGES):
            self.button("nav-" + p["key"], 1836, NAV_Y[i], 72, 72, pid(p["key"], self.mode), "الانتقال إلى " + p["name"], f"Nav: {p['key']}")


def bar(pg, key, x, y, w, h, cat, measures, vt="clusteredBarChart", sort=None, units=0, precision=1, colors=None, series=None, label=None, alt=None):
    q = {"Category": {"projections": [proj(cat, active=True)]}, "Y": {"projections": [proj(f, d) for f, d in measures]}}
    if series is not None:
        q["Series"] = {"projections": [proj(series, active=True)]}
    objs = {"labels": [{"properties": {"show": lit("true"), "labelDisplayUnits": lit(f"{units}D"), "labelPrecision": lit(f"{precision}L")}}]} if units is not None else {}
    if vt == "clusteredBarChart":   # right-to-left bars: categories on the right, bars grow to the left
        objs = merge(objs, {"valueAxis": [{"properties": {"invertAxis": lit("true")}}], "categoryAxis": [{"properties": {"switchAxisPosition": lit("true")}}]})
    if colors:
        objs = merge(objs, pg.series(list(zip([f for f, _ in measures], colors))))
    pg.add(key, x, y, w, h, vt, q, sort=sort, objects=objs, label=label, alt=alt)


def table(pg, key, x, y, w, h, cols, sort, bars=None, colour=None, label=None, alt=None):
    """cols are given right-to-left (first = rightmost); PBI tables lay out left-to-right, so they are reversed."""
    m = pg.m
    objs = {"columnFormatting": [{"properties": {"alignment": lit("'Right'")}, "selector": {"metadata": qref(cols[0][0])}}]}
    if bars is not None:
        objs["columnFormatting"].append({"properties": {"dataBars": {"positiveColor": solid(m["s1"]), "negativeColor": solid(m["neg"]), "axisColor": solid(m["border"]),
                                         "reverseDirection": lit("true"), "hideText": lit("false")}}, "selector": {"metadata": qref(bars)}})
    if colour:
        objs["values"] = [{"properties": {"fontColor": solid_m(colour[1] + SUFFIX[pg.mode])}, "selector": wild(colour[0])}]
    pg.add(key, x, y, w, h, "tableEx", {"Values": {"projections": [proj(f, d) for f, d in reversed(cols)]}}, sort=sort, objects=objs, label=label, alt=alt)


RCY, RPY, RT = mea("Revenue CY"), mea("Revenue PY"), mea("Revenue Target CY")
UCY, UPY = mea("Units CY"), mea("Units PY")
BRN, SEG = col("Branches", "BranchName"), col("Segment", "Segment")


def build(spec, mode):
    pg = Page(spec, mode); m = pg.m; k = spec["key"]
    if k == "cover":
        pg.chrome(slicers=False)
        hx, hw = rx(0, 7), span(7)
        pg.extra["hero"] = dict(x=hx, y=40, w=hw, h=1008)
        for i, (lbl, msr, units) in enumerate([("إيرادات المبيعات 2023-2025", "Cover Revenue Label", None), ("سيارة مُباعة", "Units All Years", 1),
                                               ("إجمالي الربح", "Cover Gross Label", None), ("زيارة صيانة", "Visits All Years", 1)]):
            tw = (hw - 64 - 3 * 16) // 4
            tx = hx + hw - 32 - (i + 1) * tw - i * 16
            pg.tiles.append(dict(x=tx, y=800, w=tw, h=168, label=lbl, icon=None, caption=None, hero=True))
            pg.card(f"cover{i}", tx + 8, 828, tw - 16, 56, msr, size=24, units=units, bold=True, label=lbl)
        tx, tw = rx(7, 5), span(5)
        pg.extra["toc"] = dict(x=tx, y=136, w=tw, h=912)
        for i, p in enumerate(PAGES[1:]):
            pg.button(f"toc-{p['key']}", tx + 24, 236 + i * 128, tw - 48, 112, pid(p["key"], mode), "الانتقال إلى " + p["name"], f"TOC: {p['key']}")
        return pg
    pg.chrome()
    if k == "exec":
        pg.tiles_row([("الإيرادات", "banknote", "Revenue CY", dict(delta="Revenue")), ("الوحدات المباعة", "car", "Units CY", dict(delta="Units", units=1)),
                      ("إجمالي الربح للسيارة", "coins", "Total GPU CY", dict(delta="Total GPU", units=1)),
                      ("تحقيق الهدف", "target", "Attainment CY", dict(delta="Attainment Label", color="Attainment Color")),
                      ("نسبة التمويل", "landmark", "Finance Penetration CY", dict(delta="Finance Penetration")),
                      ("إيرادات الصيانة", "wrench", "Service Revenue CY", dict(delta="Service Revenue"))])
        x, y, w, h = pg.panel(rx(0, 8), ROW2, span(8), 368, "الإيرادات الشهرية مقابل الهدف", "آخر سنة مقارنةً بالهدف والعام السابق (ريال)")
        pg.add("trend", x, y, w, h, "lineChart", {"Category": {"projections": [proj(MONTH, active=True)]},
               "Y": {"projections": [proj(RCY, "هذا العام"), proj(RT, "الهدف"), proj(RPY, "العام السابق")]}}, sort=[(MONTH, "Ascending")],
               objects=pg.series([(RCY, m["s1"]), (RT, m["s3"]), (RPY, m["s2"])], dashed=[RT, RPY]), label="Revenue vs target (line)", alt="الإيرادات الشهرية مقابل الهدف")
        pg.insights(rx(8, 4), ROW2, span(4), 368, "أبرز المؤشرات", ["Insight Headline", "Insight Chinese", "Insight Electrified"])
        x, y, w, h = pg.panel(rx(0, 5), 752, span(5), 296, "الإيرادات مقابل الهدف حسب الفرع", "آخر سنة")
        bar(pg, "branch", x, y, w, h, BRN, [(RCY, "الإيرادات"), (RT, "الهدف")], sort=[(RCY, "Descending")], colors=[m["s1"], m["s3"]], label="Branch vs target (bar)", alt="الإيرادات والهدف حسب الفرع")
        x, y, w, h = pg.panel(rx(5, 4), 752, span(4), 296, "الوحدات حسب منشأ العلامة", "آخر سنة")
        bar(pg, "origin", x, y, w, h, col("Vehicles", "Origin"), [(UCY, "الوحدات")], sort=[(UCY, "Descending")], units=1, precision=0, label="Origin (bar)", alt="الوحدات حسب المنشأ")
        x, y, w, h = pg.panel(rx(9, 3), 752, span(3), 296, "نوع المحرك", "حصة الوحدات، آخر سنة")
        pg.add("powertrain", x, y, w, h, "donutChart", {"Category": {"projections": [proj(col("Vehicles", "Powertrain"), active=True)]},
               "Y": {"projections": [proj(UCY, "الوحدات")]}}, label="Powertrain (donut)", alt="حصة أنواع المحركات")
    elif k == "sales":
        pg.tiles_row([("الربح الأمامي للسيارة", "coins", "Front GPU CY", dict(delta="Front GPU", units=1)), ("نسبة الخصم", "percent", "Discount % CY", dict(delta="Discount")),
                      ("التوقع السنوي", "gauge", "Run-rate FY", dict(caption="بحسب وتيرة البيع منذ بداية العام")),
                      ("هدف العام", "flag", "Target FY", dict(caption="مجموع الأهداف الشهرية للفروع والفئات"))])
        x, y, w, h = pg.panel(rx(0, 7), ROW2, span(7), 336, "تحقيق الهدف حسب الفرع والفئة", "الإيرادات ÷ الهدف؛ أخضر ≥ 100%، كهرماني 90-100%، أحمر < 90%")
        att = mea("Attainment CY")
        pg.add("attmatrix", x, y, w, h, "pivotTable", {"Rows": {"projections": [proj(BRN, "الفرع", active=True)]}, "Columns": {"projections": [proj(SEG, "الفئة", active=True)]},
               "Values": {"projections": [proj(att, "التحقيق")]}}, objects={"values": [{"properties": {"fontColor": solid_m("Attainment Color" + SUFFIX[mode])}, "selector": wild(att)}]},
               label="Attainment matrix", alt="مصفوفة تحقيق الهدف")
        x, y, w, h = pg.panel(rx(7, 5), ROW2, span(5), 336, "الوحدات حسب العلامة", "آخر سنة")
        bar(pg, "make", x, y, w, h, col("Vehicles", "Make"), [(UCY, "الوحدات")], sort=[(UCY, "Descending")], units=1, precision=0, label="Make (bar)", alt="الوحدات حسب العلامة")
        x, y, w, h = pg.panel(rx(0, 6), 720, span(6), 328, "الخصم مقابل الربح الأمامي", "كل نقطة فرع؛ الحجم = الوحدات")
        pg.add("scatter", x, y, w, h, "scatterChart", {"Category": {"projections": [proj(BRN, active=True)]}, "X": {"projections": [proj(mea("Discount % CY"), "نسبة الخصم")]},
               "Y": {"projections": [proj(mea("Front GPU CY"), "الربح الأمامي للسيارة")]}, "Size": {"projections": [proj(UCY, "الوحدات")]}},
               objects={"colorByCategory": [{"properties": {"show": lit("false")}}], "dataPoint": [{"properties": {"defaultColor": solid(m["s2"])}}],
                        "categoryLabels": [{"properties": {"show": lit("true")}}]}, label="Discount vs gross (scatter)", alt="الخصم مقابل الربح حسب الفرع")
        x, y, w, h = pg.panel(rx(6, 6), 720, span(6), 328, "الموسمية الشهرية", "الوحدات المباعة: هذا العام مقابل العام السابق")
        bar(pg, "season", x, y, w, h, MONTH, [(UCY, "هذا العام"), (UPY, "العام السابق")], vt="clusteredColumnChart", sort=[(MONTH, "Ascending")], units=None,
            colors=[m["s1"], m["s2"]], label="Units by month (column)", alt="الوحدات الشهرية")
    elif k == "stock":
        pg.tiles_row([("متوسط أيام المخزون", "timer", "Avg Days in Stock CY", dict(delta="Days in Stock")), ("المخزون المتقادم", "hourglass", "Aged Stock % CY", dict(delta="Aged")),
                      ("الهجين والكهربائي", "zap", "Electrified Share CY", dict(delta="Electrified")), ("العلامات الصينية", "globe", "Chinese Share CY", dict(delta="Chinese"))])
        x, y, w, h = pg.panel(rx(0, 7), ROW2, span(7), 352, "أداء الطرازات", "آخر سنة؛ الأشرطة = الوحدات")
        table(pg, "models", x, y, w, h, [(col("Vehicles", "Vehicle"), "الطراز"), (SEG, "الفئة"), (UCY, "الوحدات"), (mea("Front GPU CY"), "الربح للسيارة"),
              (mea("Avg Days in Stock CY"), "أيام المخزون")], sort=[(UCY, "Descending")], bars=UCY, label="Models table", alt="جدول أداء الطرازات")
        x, y, w, h = pg.panel(rx(7, 5), ROW2, span(5), 352, "التحول في نوع المحرك", "حصة الوحدات لكل سنة")
        yr = col("Date", "Year")
        bar(pg, "ptshift", x, y, w, h, yr, [(mea("Units"), "الوحدات")], vt="hundredPercentStackedColumnChart", sort=[(yr, "Ascending")], units=None,
            series=col("Vehicles", "Powertrain"), label="Powertrain shift (100% column)", alt="حصة أنواع المحركات حسب السنة")
        x, y, w, h = pg.panel(rx(0, 4), 736, span(4), 312, "الخصم حسب عمر المخزون", "نسبة الخصم، آخر سنة")
        age = col("Sales", "Stock Age Band")
        bar(pg, "agedisc", x, y, w, h, age, [(mea("Discount % CY"), "نسبة الخصم")], vt="clusteredColumnChart", sort=[(age, "Ascending")], units=1, precision=1,
            label="Discount by stock age (column)", alt="الخصم حسب عمر المخزون")
        x, y, w, h = pg.panel(rx(4, 4), 736, span(4), 312, "الفئات السعرية", "الوحدات، آخر سنة")
        pb = col("Sales", "Price Band")
        bar(pg, "price", x, y, w, h, pb, [(UCY, "الوحدات")], sort=[(pb, "Ascending")], units=1, precision=0, label="Price band (bar)", alt="الوحدات حسب الفئة السعرية")
        x, y, w, h = pg.panel(rx(8, 4), 736, span(4), 312, "مزيج الفئات", "حصة الوحدات، آخر سنة")
        pg.add("segmix", x, y, w, h, "donutChart", {"Category": {"projections": [proj(SEG, active=True)]}, "Y": {"projections": [proj(UCY, "الوحدات")]}},
               label="Segment (donut)", alt="مزيج الفئات")
    elif k == "customers":
        pg.tiles_row([("العملاء المحتملون", "user-plus", "Leads CY", dict(delta="Leads", units=1)), ("نسبة التحويل", "funnel", "Lead Conversion CY", dict(delta="Lead Conversion")),
                      ("نسبة التمويل", "landmark", "Finance Penetration CY", dict(delta="Finance Penetration")),
                      ("صفقات الاستبدال", "repeat", "Trade-in Rate CY", dict(caption="صفقات تضمنت سيارة مستبدلة"))])
        x, y, w, h = pg.panel(rx(0, 7), ROW2, span(7), 352, "مسار البيع حسب المصدر", "عملاء محتملون ← تجارب قيادة ← صفقات، آخر سنة")
        conv = mea("Lead Conversion CY")
        table(pg, "funnel", x, y, w, h, [(col("Leads", "Source"), "المصدر"), (mea("Leads CY"), "عملاء محتملون"), (mea("Test Drives CY"), "تجارب قيادة"),
              (mea("Converted Leads CY"), "صفقات"), (conv, "نسبة التحويل")], sort=[(conv, "Descending")], bars=conv, label="Funnel table", alt="مسار البيع حسب المصدر")
        x, y, w, h = pg.panel(rx(7, 5), ROW2, span(5), 352, "طريقة الدفع", "حصة الوحدات، آخر سنة")
        pg.add("payment", x, y, w, h, "donutChart", {"Category": {"projections": [proj(col("Sales", "PaymentType"), active=True)]}, "Y": {"projections": [proj(UCY, "الوحدات")]}},
               label="Payment (donut)", alt="طرق الدفع")
        x, y, w, h = pg.panel(rx(0, 4), 736, span(4), 312, "شركاء التمويل", "الصفقات الممولة، آخر سنة")
        fu = mea("Financed Units CY")
        bar(pg, "partners", x, y, w, h, col("Sales", "FinancePartner"), [(fu, "صفقات ممولة")], sort=[(fu, "Descending")], units=1, precision=0, label="Finance partners (bar)", alt="شركاء التمويل")
        x, y, w, h = pg.panel(rx(4, 4), 736, span(4), 312, "نوع العميل", "الإيرادات، آخر سنة")
        bar(pg, "ctype", x, y, w, h, col("Customers", "CustomerType"), [(RCY, "الإيرادات")], sort=[(RCY, "Descending")], label="Customer type (bar)", alt="الإيرادات حسب نوع العميل")
        pg.insights(rx(8, 4), 736, span(4), 312, "مؤشرات العملاء", ["Insight Finance", "Insight Leads"])
    elif k == "service":
        pg.tiles_row([("إيرادات الصيانة", "wrench", "Service Revenue CY", dict(delta="Service Revenue")), ("رضا العملاء", "smile", "Avg CSAT CY", dict(delta="CSAT")),
                      ("نسبة العودة للإصلاح", "rotate-ccw", "Comeback Rate CY", dict(delta="Comeback")), ("نسبة الاستيعاب", "shield-check", "Absorption CY", dict(delta="Absorption"))])
        x, y, w, h = pg.panel(rx(0, 5), ROW2, span(5), 336, "الإيرادات حسب نوع الخدمة", "العمالة وقطع الغيار، آخر سنة")
        bar(pg, "stype", x, y, w, h, col("Service", "ServiceType"), [(mea("Labor Revenue CY"), "العمالة"), (mea("Parts Revenue CY"), "قطع الغيار")],
            sort=[(mea("Parts Revenue CY"), "Descending")], colors=[m["s1"], m["s3"]], label="Service type (bar)", alt="إيرادات الصيانة حسب النوع")
        band = col("Service", "Turnaround Band")
        x, y, w, h = pg.panel(rx(5, 4), ROW2, span(4), 336, "الرضا حسب زمن الإنجاز", "متوسط التقييم (1-5)")
        bar(pg, "csat", x, y, w, h, band, [(mea("Avg CSAT CY"), "الرضا")], vt="clusteredColumnChart", sort=[(band, "Ascending")], units=1, precision=2,
            label="CSAT by turnaround (column)", alt="الرضا حسب زمن الإنجاز")
        x, y, w, h = pg.panel(rx(9, 3), ROW2, span(3), 336, "العودة حسب زمن الإنجاز", "نسبة الزيارات المتكررة")
        bar(pg, "comeback", x, y, w, h, band, [(mea("Comeback Rate CY"), "العودة")], vt="clusteredColumnChart", sort=[(band, "Ascending")], units=1, precision=1,
            colors=[m["s2"]], label="Comebacks by turnaround (column)", alt="العودة للإصلاح حسب زمن الإنجاز")
        x, y, w, h = pg.panel(rx(0, 8), 720, span(8), 328, "ترتيب مراكز الصيانة", "آخر سنة؛ الأشرطة = الإيرادات، العودة ملونة حسب الحد")
        cb = mea("Comeback Rate CY")
        table(pg, "league", x, y, w, h, [(BRN, "الفرع"), (mea("Visits CY"), "الزيارات"), (mea("Service Revenue CY"), "الإيرادات"), (mea("Avg CSAT CY"), "الرضا"),
              (cb, "العودة"), (mea("Avg Turnaround CY"), "زمن الإنجاز (ساعة)")], sort=[(mea("Service Revenue CY"), "Descending")], bars=mea("Service Revenue CY"),
              colour=(cb, "Comeback Color"), label="Service league table", alt="ترتيب مراكز الصيانة")
        pg.insights(rx(8, 4), 720, span(4), 328, "مؤشرات الصيانة", ["Insight Service", "Insight Absorption"])
    elif k == "conclusion":
        pg.insights(rx(0, 6), 136, span(6), 520, "النتائج الرئيسية", ["Insight Headline", "Insight Branch Target", "Insight Discount", "Insight Service"])
        pg.insights(rx(6, 6), 136, span(6), 520, "التوصيات", ["Recommendation Discount", "Recommendation Leads", "Recommendation Stock", "Recommendation Service"],
                    numbered=True, subtitle="مبنية على أرقام الفترة المختارة")
        pg.extra["next"] = dict(x=X0, y=680, w=CW, h=368)
        pg.button("back-to-cover", X0 + 24, 680 + 368 - 72, 240, 48, pid("cover", mode), "العودة إلى المقدمة", "Back to cover")
    return pg


pages = [build(s, md) for md in MODES for s in PAGES]
layout = {"palettes": PAL, "nav": [dict(y=NAV_Y[i], icon=p["icon"], label=p["nav"]) for i, p in enumerate(PAGES)],
          "toc": [dict(title=p["name"], icon=p["icon"]) for p in PAGES[1:]], "pages": []}
for pg in pages:
    layout["pages"].append(dict(key=pg.key, mode=pg.mode, title=pg.spec["name"], bg=f"bg-{pg.key}-{pg.mode}.jpg", active=[p["key"] for p in PAGES].index(pg.key),
                                panels=pg.panels, tiles=pg.tiles, bullets=pg.bullets, controls=pg.controls, extra=pg.extra,
                                visuals=[dict(x=v["position"]["x"], y=v["position"]["y"], w=v["position"]["width"], h=v["position"]["height"], label=v["_label"]) for v in pg.visuals]))
os.makedirs(W, exist_ok=True)
json.dump(layout, open(os.path.join(W, "layout.json"), "w"), ensure_ascii=False, indent=1)
print("visuals per page:", {f"{p.key}-{p.mode}": len(p.visuals) for p in pages})

# ------------------------------------------------------------------ theme (dark default, Tajawal everywhere)
c = PAL["dark"]
sol = lambda h: {"solid": {"color": h}}
ax = {"labelColor": sol(c["text2"]), "fontSize": 11, "fontFamily": FONT, "showAxisTitle": False}
theme = {
    "name": "Masar Horizon", "dataColors": [c["s1"], c["s2"], c["s3"], "#D4A72C", "#5FB0D9", "#C9667A", "#8FA35B", "#A57BD1"],
    "foreground": c["text"], "foregroundNeutralSecondary": c["text2"], "foregroundNeutralTertiary": "#6B737E", "background": c["panel"],
    "backgroundLight": c["panel2"], "backgroundNeutral": c["border"], "tableAccent": c["s1"], "good": c["pos"], "neutral": "#8B95A1", "bad": c["neg"],
    "maximum": c["s1"], "center": "#6B737E", "minimum": c["panel2"], "null": "#8B95A1", "hyperlink": c["accentText"], "visitedHyperlink": c["accentText"],
    "textClasses": {"callout": {"fontFace": FONT, "fontSize": 26, "color": c["text"]}, "title": {"fontFace": FONT, "fontSize": 14, "color": c["text"]},
                    "header": {"fontFace": FONT, "fontSize": 12, "color": c["text2"]}, "label": {"fontFace": FONT, "fontSize": 11, "color": c["text2"]}},
    "visualStyles": {
        "*": {"*": {"background": [{"show": False, "transparency": 100}], "border": [{"show": False}], "dropShadow": [{"show": False}], "title": [{"show": False}],
                    "padding": [{"top": 0, "bottom": 0, "left": 0, "right": 0}],
                    "visualHeader": [{"background": sol(c["panel2"]), "foreground": sol(c["text2"]), "border": sol(c["border"]), "transparency": 0}],
                    "visualTooltip": [{"background": sol(c["tooltip"]), "titleFontColor": sol(c["text2"]), "valueFontColor": sol(c["text"]), "fontSize": 11, "fontFamily": FONT}],
                    "categoryAxis": [dict(ax, gridlineShow=False)], "valueAxis": [dict(ax, gridlineShow=True, gridlineColor=sol(c["grid"]), gridlineStyle="dotted")],
                    "legend": [{"show": True, "position": "TopRight", "labelColor": sol(c["text2"]), "fontSize": 11, "fontFamily": FONT}],
                    "labels": [{"color": sol(c["text2"]), "fontSize": 11, "fontFamily": FONT}]}},
        "page": {"*": {"outspace": [{"color": sol(c["canvas"]), "transparency": 0}], "background": [{"color": sol(c["canvas"]), "transparency": 0}]}},
        "card": {"*": {"labels": [{"fontFamily": FONT, "fontSize": 26, "color": sol(c["text"])}], "categoryLabels": [{"show": False}], "wordWrap": [{"show": True}]}},
        "slicer": {"*": {"header": [{"show": False}], "items": [{"fontColor": sol(c["text"]), "background": sol(c["panel2"]), "textSize": 12, "fontFamily": FONT}],
                         "data": [{"mode": "Dropdown"}]}},
        "lineChart": {"*": {"lineStyles": [{"strokeWidth": 3, "showMarker": False}]}},
        "clusteredBarChart": {"*": {"valueAxis": [{"show": False, "gridlineShow": False}], "labels": [{"show": True, "fontSize": 11}], "layout": [{"clusteredGapSize": 6}]}},
        "donutChart": {"*": {"slices": [{"innerRadiusRatio": 68}], "legend": [{"show": False}], "dataPoint": [{"borderShow": True, "borderColor": sol(c["panel"]), "borderSize": 2}],
                             "labels": [{"show": True, "labelStyle": "Category, percent of total", "color": sol(c["text"]), "fontSize": 12, "fontFamily": FONT, "position": "outside"}]}},
        "pivotTable": {"*": {"grid": [{"gridHorizontal": True, "gridVertical": False, "rowPadding": 7, "textSize": 12}],
                             "columnHeaders": [{"fontFamily": FONT, "fontSize": 11, "bold": True}], "rowHeaders": [{"fontFamily": FONT, "fontSize": 12}],
                             "values": [{"fontFamily": FONT, "fontSize": 12}], "total": [{"bold": True}]}},
        "tableEx": {"*": {"grid": [{"gridHorizontal": True, "gridVertical": False, "rowPadding": 7, "textSize": 12}],
                          "columnHeaders": [{"fontFamily": FONT, "fontSize": 11, "bold": True}], "values": [{"fontFamily": FONT, "fontSize": 12}], "total": [{"bold": True}]}},
        "scatterChart": {"*": {"categoryLabels": [{"fontSize": 10, "fontFamily": FONT}]}},
    },
}
json.dump(theme, open(os.path.join(W, "theme.json"), "w"), ensure_ascii=False, indent=2)
if not WRITE:
    sys.exit(0)


def wj(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


# project shell (created once)
if not os.path.exists(os.path.join(ROOT, f"{NAME}.pbip")):
    wj(os.path.join(ROOT, f"{NAME}.pbip"), {"$schema": f"{FAB}/pbip/pbipProperties/1.0.0/schema.json", "version": "1.0",
                                            "artifacts": [{"report": {"path": f"{NAME}.Report"}}], "settings": {"enableAutoRecovery": True}})
    sm = os.path.join(ROOT, f"{NAME}.SemanticModel")
    wj(os.path.join(sm, "definition.pbism"), {"$schema": f"{FAB}/item/semanticModel/definitionProperties/1.0.0/schema.json", "version": "4.0", "settings": {}})
    wj(os.path.join(sm, ".platform"), {"$schema": f"{FAB}/gitIntegration/platformProperties/2.0.0/schema.json", "metadata": {"type": "SemanticModel", "displayName": NAME},
                                       "config": {"version": "2.0", "logicalId": "8b0f6c1e-4d2a-4f7b-9c3e-1a5d7e9b2c40"}})
    wj(os.path.join(RP, "definition.pbir"), {"$schema": f"{FAB}/item/report/definitionProperties/2.0.0/schema.json", "version": "4.0",
                                             "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
    wj(os.path.join(RP, ".platform"), {"$schema": f"{FAB}/gitIntegration/platformProperties/2.0.0/schema.json", "metadata": {"type": "Report", "displayName": NAME},
                                       "config": {"version": "2.0", "logicalId": "3e7a9d2b-6c1f-4e8a-b5d0-7f2c4a6e8b91"}})
    wj(os.path.join(D, "version.json"), {"$schema": f"{FAB}/item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    src = os.path.join(ROOT, "SalesSample.Report", "StaticResources", "SharedResources", "BaseThemes", "CY24SU10.json")
    dst = os.path.join(RP, "StaticResources", "SharedResources", "BaseThemes", "CY24SU10.json")
    os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copyfile(src, dst)
reg = os.path.join(RP, "StaticResources", "RegisteredResources")
shutil.rmtree(reg, ignore_errors=True); os.makedirs(reg)
for lp in layout["pages"]:
    shutil.copyfile(os.path.join(W, "render", lp["bg"]), os.path.join(reg, lp["bg"]))
shutil.copyfile(os.path.join(W, "theme.json"), os.path.join(reg, THEME_NAME))
wj(os.path.join(D, "report.json"), {
    "$schema": f"{FAB}/item/report/definition/report/2.0.0/schema.json",
    "themeCollection": {"baseTheme": {"name": "CY24SU10", "reportVersionAtImport": "5.61", "type": "SharedResources"},
                        "customTheme": {"name": THEME_NAME, "reportVersionAtImport": "5.65", "type": "RegisteredResources"}},
    "objects": {"outspacePane": [{"properties": {"expanded": lit("false"), "visible": lit("false")}}]},
    "resourcePackages": [{"name": "SharedResources", "type": "SharedResources", "items": [{"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": "BaseTheme"}]},
                         {"name": "RegisteredResources", "type": "RegisteredResources", "items": [{"name": THEME_NAME, "path": THEME_NAME, "type": "CustomTheme"}] +
                          [{"name": lp["bg"], "path": lp["bg"], "type": "Image"} for lp in layout["pages"]]}],
    "settings": {"useStylableVisualContainerHeader": True, "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True}})
pd_root = os.path.join(D, "pages")
shutil.rmtree(pd_root, ignore_errors=True)
wj(os.path.join(pd_root, "pages.json"), {"$schema": f"{FAB}/item/report/definition/pagesMetadata/1.0.0/schema.json",
                                         "pageOrder": [p.id for p in pages], "activePageName": pages[0].id})
for pg, lp in zip(pages, layout["pages"]):
    page = {"$schema": f"{FAB}/item/report/definition/page/2.0.0/schema.json", "name": pg.id,
            "displayName": pg.spec["name"] + (" (فاتح)" if pg.mode == "light" else ""), "displayOption": "FitToPage", "height": 1080, "width": 1920,
            "objects": {"background": [{"properties": {"image": {"image": {"name": lit(f"'{lp['bg']}'"),
                        "url": {"expr": {"ResourcePackageItem": {"PackageName": "RegisteredResources", "PackageType": 1, "ItemName": lp["bg"]}}},
                        "scaling": lit("'Fit'")}}, "transparency": lit("0D")}}],
                        "outspace": [{"properties": {"color": solid(pg.m["canvas"]), "transparency": lit("0D")}}]}}
    if pg.mode == "light":
        page["visibility"] = "HiddenInViewMode"
    wj(os.path.join(pd_root, pg.id, "page.json"), page)
    for v in pg.visuals:
        wj(os.path.join(pd_root, pg.id, "visuals", v["name"], "visual.json"), {k2: val for k2, val in v.items() if k2 != "_label"})
print("report written")
