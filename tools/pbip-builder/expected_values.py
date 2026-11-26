# Recomputes the expected KPI values from the workbook (independent of Power BI), for README verification.
import sys, collections, json
from datetime import date
import openpyxl

wb = openpyxl.load_workbook(sys.argv[1], read_only=True)
def rows(name):
    it = wb[name].iter_rows(values_only=True)
    h = next(it)
    return [dict(zip(h, r)) for r in it]
S, P, C, ST, CM, T = (rows(n) for n in ("Sales", "Products", "Customers", "Stores", "Campaigns", "Targets"))
P = {p["ProductID"]: p for p in P}; C = {c["CustomerID"]: c for c in C}; STm = {s["StoreID"]: s for s in ST}
for r in S:
    r["Y"] = r["OrderDate"].year
first = {}
for r in S:
    first[r["CustomerID"]] = min(first.get(r["CustomerID"], r["OrderDate"]), r["OrderDate"])

def kpis(y):
    rs = [r for r in S if r["Y"] == y]
    sales = sum(r["SalesAmount"] for r in rs); cost = sum(r["CostAmount"] for r in rs)
    ret = [r for r in rs if r["IsReturned"]]
    ret_sales = sum(r["SalesAmount"] for r in ret); ret_cost = sum(r["CostAmount"] for r in ret)
    ship = sum(r["ShippingCost"] or 0 for r in rs)
    orders = len({r["OrderID"] for r in rs}); units = sum(r["Quantity"] for r in rs)
    custs = {r["CustomerID"] for r in rs}
    prev = {r["CustomerID"] for r in S if r["Y"] == y - 1}
    new = {c for c in custs if first[c].year == y}
    per_c = collections.Counter();
    for o in {(r["CustomerID"], r["OrderID"]) for r in rs}: per_c[o[0]] += 1
    rated = [r["CustomerRating"] for r in rs if r["CustomerRating"] is not None]
    online = [r for r in rs if r["DeliveryDays"] is not None]
    gross = sum(r["Quantity"] * r["UnitPrice"] for r in rs)
    tgt = sum(t["TargetAmount"] for t in T if t["Month"].year == y)
    bnpl = sum(r["SalesAmount"] for r in rs if r["PaymentMethod"] in ("Tabby", "Tamara"))
    disc_sales = sum(r["SalesAmount"] for r in rs if r["Discount"] > 0)
    def aov(ch):
        x = [r for r in rs if r["Channel"] == ch]
        return sum(r["SalesAmount"] for r in x) / len({r["OrderID"] for r in x})
    tier = collections.defaultdict(float); tier_c = collections.defaultdict(set)
    for r in rs:
        t = C[r["CustomerID"]]["LoyaltyTier"]; tier[t] += r["SalesAmount"]; tier_c[t].add(r["CustomerID"])
    reg_s = collections.defaultdict(float)
    for r in rs: reg_s[C[r["CustomerID"]]["Region"]] += r["SalesAmount"]
    reg_t = collections.defaultdict(float)
    for t in T:
        if t["Month"].year == y: reg_t[t["Region"]] += t["TargetAmount"]
    brand = collections.defaultdict(lambda: [0.0, 0.0])
    for r in rs:
        b = brand[P[r["ProductID"]]["Brand"]]; b[0] += r["SalesAmount"]; b[1] += r["SalesAmount"] if r["IsReturned"] else 0
    ps = collections.defaultdict(float); cs = collections.defaultdict(float)
    for r in rs: ps[r["ProductID"]] += r["SalesAmount"]; cs[r["CustomerID"]] += r["SalesAmount"]
    def pareto(d):
        v = sorted(d.values(), reverse=True); n = -(-len(v) * 2 // 10); return sum(v[:n]) / sum(v)
    camp = [c for c in CM if c["StartDate"].year == y]
    camp_rev = sum(r["SalesAmount"] for r in rs if r["CampaignID"]); budget = sum(c["Budget"] for c in camp)
    late = [r for r in online if r["DeliveryDays"] > 3]
    out = dict(
        Sales=sales, Target=tgt, Attainment=sales / tgt if tgt else None, GrossMargin=sales - cost, MarginPct=(sales - cost) / sales,
        ReturnedSales=ret_sales, ReturnRate=ret_sales / sales, NetMargin=(sales - ret_sales) - (cost - ret_cost) - ship,
        NetMarginPct=((sales - ret_sales) - (cost - ret_cost) - ship) / (sales - ret_sales),
        Orders=orders, AOV=sales / orders, UPT=units / orders, Units=units, ActiveCustomers=len(custs), NewCustomers=len(new),
        Retention=len(custs & prev) / len(prev) if prev else None, RepeatRate=sum(1 for v in per_c.values() if v >= 2) / len(custs),
        AvgRating=sum(rated) / len(rated), Detractors=sum(1 for x in rated if x <= 2) / len(rated),
        AvgDeliveryDays=sum(r["DeliveryDays"] for r in online) / len(online), LatePct=len(late) / len(online),
        RatingLate=sum(r["CustomerRating"] for r in late if r["CustomerRating"]) / max(1, sum(1 for r in late if r["CustomerRating"])),
        RatingOnTime=sum(r["CustomerRating"] for r in online if r["DeliveryDays"] <= 3 and r["CustomerRating"]) / max(1, sum(1 for r in online if r["DeliveryDays"] <= 3 and r["CustomerRating"])),
        DiscountPct=(gross - sales) / gross, DiscountDrivenShare=disc_sales / sales, BNPLShare=bnpl / sales,
        AOV_App=aov("App"), AOV_Website=aov("Website"), AOV_Store=aov("Store"),
        PlatinumCustShare=len(tier_c["Platinum"]) / len(custs), PlatinumSalesShare=tier["Platinum"] / sales,
        RegionAttainment={k: reg_s[k] / reg_t[k] for k in reg_t}, BrandReturnRate={k: v[1] / v[0] for k, v in brand.items()},
        Top20ProductsShare=pareto(ps), Top20CustomersShare=pareto(cs), CampaignRevenue=camp_rev, CampaignBudget=budget,
        ROAS=camp_rev / budget if budget else None, CampaignShare=camp_rev / sales,
        RamadanEidShare=None)
    return out

res = {y: kpis(y) for y in (2023, 2024, 2025)}
roas = collections.defaultdict(lambda: [0.0, 0.0])
for c in CM:
    roas[c["Channel"]][1] += c["Budget"]
cm = {c["CampaignID"]: c for c in CM}
for r in S:
    if r["CampaignID"]: roas[cm[r["CampaignID"]]["Channel"]][0] += r["SalesAmount"]
res["ROASByChannel"] = {k: v[0] / v[1] for k, v in roas.items()}
ret_reason = collections.Counter(r["ReturnReason"] for r in S if r["IsReturned"] and P[r["ProductID"]]["Brand"] == "Sahra" and r["Y"] == 2025)
res["SahraReasons2025"] = dict(ret_reason)
acq = collections.defaultdict(lambda: [set(), set()])
for r in S:
    a = C[r["CustomerID"]]["AcquisitionChannel"]
    if r["Y"] == 2024: acq[a][0].add(r["CustomerID"])
    if r["Y"] == 2025: acq[a][1].add(r["CustomerID"])
res["RetentionByAcq"] = {k: len(v[0] & v[1]) / len(v[0]) for k, v in acq.items()}
print(json.dumps(res, indent=1, default=str))
