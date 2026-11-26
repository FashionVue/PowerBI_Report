# Recomputes the VehicleSales KPIs from the workbook (independent of Power BI) for README verification.
# Usage: python3 expected_values.py data/VehicleSales.xlsx
import collections, json, sys
import openpyxl

wb = openpyxl.load_workbook(sys.argv[1], read_only=True)
def rows(n):
    it = wb[n].iter_rows(values_only=True); h = next(it); return [dict(zip(h, r)) for r in it]
S, L, SV, V, B, T = (rows(n) for n in ("Sales", "Leads", "Service", "Vehicles", "Branches", "Targets"))
V = {v["VehicleID"]: v for v in V}; B = {b["BranchID"]: b for b in B}

def year(y):
    s = [r for r in S if r["DealDate"].year == y]; l = [r for r in L if r["LeadDate"].year == y]; sv = [r for r in SV if r["VisitDate"].year == y]
    units = len(s); rev = sum(r["SalePrice"] for r in s); front = sum(r["SalePrice"] - r["VehicleCost"] for r in s)
    back = sum(r["FinanceCommission"] + r["AddOnRevenue"] - r["AddOnCost"] for r in s)
    fin = [r for r in s if r["PaymentType"] != "كاش"]
    svc_rev = sum(r["LaborRevenue"] + r["PartsRevenue"] for r in sv); svc_gross = svc_rev - sum(r["ServiceCost"] for r in sv)
    csat = [r["CSAT"] for r in sv if r["CSAT"] is not None]
    fixed = sum(b["MonthlyFixedCost"] for b in B.values()) * 12
    tgt = sum(t["RevenueTarget"] for t in T if t["Month"].year == y)
    by_branch = collections.defaultdict(lambda: [0, 0.0, 0.0, 0.0])
    for r in s:
        a = by_branch[B[r["BranchID"]]["BranchName"]]; a[0] += 1; a[1] += r["SalePrice"] - r["VehicleCost"]; a[2] += r["DiscountAmount"]; a[3] += r["ListPrice"]
    tb = collections.defaultdict(float); ab = collections.defaultdict(float)
    for t in T:
        if t["Month"].year == y: tb[B[t["BranchID"]]["BranchName"]] += t["RevenueTarget"]
    for r in s: ab[B[r["BranchID"]]["BranchName"]] += r["SalePrice"]
    src = collections.defaultdict(lambda: [0, 0])
    for r in l: src[r["Source"]][0] += 1; src[r["Source"]][1] += 1 if r["Converted"] else 0
    aged = [r for r in s if r["DaysInStock"] > 90]
    long_ = [r for r in sv if r["TurnaroundHours"] > 48]; short = [r for r in sv if r["TurnaroundHours"] <= 48]
    return dict(Units=units, Revenue=rev, FrontGross=front, FrontGrossPerUnit=front / units, BackEndGross=back, TotalGross=front + back,
                TotalGrossPerUnit=(front + back) / units, DiscountPct=sum(r["DiscountAmount"] for r in s) / sum(r["ListPrice"] for r in s),
                FinancePenetration=len(fin) / units, BackEndShareFromFinanced=sum(r["FinanceCommission"] + r["AddOnRevenue"] - r["AddOnCost"] for r in fin) / back,
                ChineseShare=sum(1 for r in s if V[r["VehicleID"]]["Origin"] == "صيني") / units,
                ElectrifiedShare=sum(1 for r in s if V[r["VehicleID"]]["Powertrain"] != "بنزين") / units,
                NewShare=sum(1 for r in s if r["Condition"] == "جديد") / units, AvgDaysInStock=sum(r["DaysInStock"] for r in s) / units,
                AgedPct=len(aged) / units, DiscountAged=sum(r["DiscountAmount"] for r in aged) / sum(r["ListPrice"] for r in aged),
                DiscountFresh=sum(r["DiscountAmount"] for r in s if r["DaysInStock"] <= 90) / sum(r["ListPrice"] for r in s if r["DaysInStock"] <= 90),
                Leads=len(l), TestDrives=sum(1 for r in l if r["TestDrive"]), LeadConversion=sum(1 for r in l if r["Converted"]) / len(l),
                SourceConversion={k: v[1] / v[0] for k, v in src.items()}, SourceLeads={k: v[0] for k, v in src.items()},
                Visits=len(sv), ServiceRevenue=svc_rev, ServiceGross=svc_gross, LaborMix=sum(r["LaborRevenue"] for r in sv) / svc_rev,
                CSAT=sum(csat) / len(csat), ComebackRate=sum(1 for r in sv if r["IsComeback"]) / len(sv),
                ComebackLong=sum(1 for r in long_ if r["IsComeback"]) / len(long_), ComebackShort=sum(1 for r in short if r["IsComeback"]) / len(short),
                AvgTurnaround=sum(r["TurnaroundHours"] for r in sv) / len(sv), Absorption=svc_gross / fixed, FixedCosts=fixed,
                RevenueTarget=tgt, Attainment=rev / tgt,
                BranchFrontPerUnit={k: v[1] / v[0] for k, v in by_branch.items()}, BranchDiscount={k: v[2] / v[3] for k, v in by_branch.items()},
                BranchAttainment={k: ab[k] / tb[k] for k in tb if tb[k]})

print(json.dumps({y: year(y) for y in (2023, 2024, 2025)}, ensure_ascii=False, indent=1, default=str))
