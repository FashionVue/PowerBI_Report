"""Generate data/VehicleSales.xlsx - a deterministic, fictional Saudi automotive dealer group.

Company (invented): مجموعة مسار الأفق للسيارات - Masar Horizon Motors. Car makes are real data values; the
company, branches, people and finance partners are invented.

Usage:  python make_vehicles.py VehicleSales.xlsx

2023-01-01 .. 2025-12-31. Patterns built in on purpose:
  * Chinese makes (MG, Geely, Changan) gain share fast; hybrid and electric share rises every year
  * Dammam branch discounts heavily and earns the lowest front-end gross per vehicle
  * Financed and lease-to-own deals carry most of the back-end (F&I + add-on) profit
  * Snapchat brings the most leads but converts worst; referrals and showroom walk-ins convert best
  * Vehicles sold after 90+ days in stock need deeper discounts
  * Service visits with long turnaround (> 48 h) come back more often and score lower CSAT
  * Summer AC-service peak, Ramadan/Eid offers, December model-year clearance, Q4 new model-year launches
  * Jeddah's targets were set too high and it misses them
Every sheet holds one Excel Table with the sheet's name.
"""
import random
import sys
from datetime import date, timedelta
from itertools import accumulate
from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

random.seed(7202501)
OUT = sys.argv[1] if len(sys.argv) > 1 else "VehicleSales.xlsx"
START, END = date(2023, 1, 1), date(2025, 12, 31)
RAMADAN = {2023: (date(2023, 3, 23), date(2023, 4, 20)), 2024: (date(2024, 3, 11), date(2024, 4, 9)), 2025: (date(2025, 3, 1), date(2025, 3, 29))}
EID_FITR = {2023: date(2023, 4, 21), 2024: date(2024, 4, 10), 2025: date(2025, 3, 30)}


def days(a, b):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)


def wpick(pairs):
    return random.choices([p[0] for p in pairs], weights=[p[1] for p in pairs])[0]


# ------------------------------------------------------------------ branches
BRANCHES = [  # id, name, city, region, type, open, monthly fixed overhead allocated to after-sales (absorption proxy), sells, services
    (1, "الرياض - المعرض الرئيسي", "الرياض", "الوسطى", "معرض رئيسي", date(2014, 3, 1), 60000, True, True),
    (2, "الرياض - الشمال", "الرياض", "الوسطى", "معرض", date(2019, 9, 1), 30000, True, False),
    (3, "جدة - التحلية", "جدة", "الغربية", "معرض رئيسي", date(2016, 1, 15), 55000, True, True),
    (4, "مكة المكرمة", "مكة المكرمة", "الغربية", "معرض", date(2020, 6, 1), 25000, True, False),
    (5, "الدمام", "الدمام", "الشرقية", "معرض", date(2018, 4, 1), 40000, True, True),
    (6, "الخبر - مركز الصيانة", "الخبر", "الشرقية", "مركز صيانة", date(2019, 2, 1), 22000, False, True),
    (7, "أبها", "أبها", "الجنوبية", "معرض", date(2021, 10, 1), 25000, True, True),
    (8, "الرياض - مركز الصيانة", "الرياض", "الوسطى", "مركز صيانة", date(2017, 5, 1), 28000, False, True),
]
CITY_W = {"الرياض": 34, "جدة": 22, "مكة المكرمة": 9, "الدمام": 12, "الخبر": 8, "أبها": 9, "المدينة المنورة": 6}
CITY_REGION = {"الرياض": "الوسطى", "جدة": "الغربية", "مكة المكرمة": "الغربية", "المدينة المنورة": "الغربية",
               "الدمام": "الشرقية", "الخبر": "الشرقية", "أبها": "الجنوبية"}
SALE_BRANCH_BY_CITY = {"الرياض": [1, 1, 2], "جدة": [3], "مكة المكرمة": [4], "المدينة المنورة": [3, 4], "الدمام": [5], "الخبر": [5], "أبها": [7]}
SERVICE_BRANCH_BY_CITY = {"الرياض": [1, 8, 8], "جدة": [3], "مكة المكرمة": [3], "المدينة المنورة": [3], "الدمام": [5, 6], "الخبر": [6], "أبها": [7]}

# ------------------------------------------------------------------ vehicles (one row per model and model year)
MODELS = [  # make, model, segment, powertrain, origin, base MSRP
    ("Toyota", "Camry", "سيدان", "بنزين", "ياباني", 118000), ("Toyota", "Camry Hybrid", "سيدان", "هجين", "ياباني", 134000),
    ("Toyota", "Land Cruiser", "دفع رباعي", "بنزين", "ياباني", 330000), ("Toyota", "Hilux", "بيك أب", "بنزين", "ياباني", 108000),
    ("Toyota", "Yaris", "هاتشباك", "بنزين", "ياباني", 69000), ("Toyota", "RAV4 Hybrid", "دفع رباعي", "هجين", "ياباني", 142000),
    ("Hyundai", "Elantra", "سيدان", "بنزين", "كوري", 86000), ("Hyundai", "Tucson", "دفع رباعي", "بنزين", "كوري", 114000),
    ("Hyundai", "Accent", "سيدان", "بنزين", "كوري", 64000), ("Hyundai", "Ioniq 5", "دفع رباعي", "كهربائي", "كوري", 186000),
    ("Kia", "K5", "سيدان", "بنزين", "كوري", 104000), ("Kia", "Sportage", "دفع رباعي", "بنزين", "كوري", 109000),
    ("Kia", "Pegas", "هاتشباك", "بنزين", "كوري", 54000), ("Kia", "EV6", "دفع رباعي", "كهربائي", "كوري", 192000),
    ("Nissan", "Patrol", "دفع رباعي", "بنزين", "ياباني", 298000), ("Nissan", "Sunny", "سيدان", "بنزين", "ياباني", 59000),
    ("Nissan", "Navara", "بيك أب", "بنزين", "ياباني", 104000), ("Ford", "Explorer", "دفع رباعي", "بنزين", "أمريكي", 212000),
    ("Ford", "F-150", "بيك أب", "بنزين", "أمريكي", 228000), ("Chevrolet", "Tahoe", "دفع رباعي", "بنزين", "أمريكي", 288000),
    ("Chevrolet", "Malibu", "سيدان", "بنزين", "أمريكي", 99000), ("MG", "MG5", "سيدان", "بنزين", "صيني", 61000),
    ("MG", "ZS", "دفع رباعي", "بنزين", "صيني", 76000), ("MG", "MG4 EV", "هاتشباك", "كهربائي", "صيني", 116000),
    ("Geely", "Coolray", "دفع رباعي", "بنزين", "صيني", 82000), ("Geely", "Monjaro", "دفع رباعي", "بنزين", "صيني", 139000),
    ("Geely", "Emgrand", "سيدان", "بنزين", "صيني", 64000), ("Changan", "CS85", "دفع رباعي", "بنزين", "صيني", 96000),
    ("Changan", "Alsvin", "سيدان", "بنزين", "صيني", 54000), ("Changan", "UNI-K iDD", "دفع رباعي", "هجين", "صيني", 128000),
    ("Lexus", "ES 300h", "فاخرة", "هجين", "ياباني", 232000), ("Lexus", "LX 600", "فاخرة", "بنزين", "ياباني", 520000),
    ("Mercedes-Benz", "E-Class", "فاخرة", "بنزين", "ألماني", 332000), ("Mercedes-Benz", "GLE", "فاخرة", "بنزين", "ألماني", 398000),
    ("BMW", "X5", "فاخرة", "بنزين", "ألماني", 378000), ("BMW", "5 Series", "فاخرة", "بنزين", "ألماني", 318000),
    ("BMW", "iX", "فاخرة", "كهربائي", "ألماني", 418000),
]
vehicles, vid = [], 0
VERSIONS = {}
for mi, (make, model, seg, pt, origin, base) in enumerate(MODELS):
    for my in (2020, 2021, 2022, 2023, 2024, 2025, 2026):
        vid += 1
        msrp = round(base * (1 + 0.035 * (my - 2023)) / 500) * 500
        margin = 0.105 if seg == "فاخرة" else 0.085 if origin == "صيني" else 0.09
        vehicles.append(dict(VehicleID=vid, Make=make, Model=model, Segment=seg, Powertrain=pt, Origin=origin, ModelYear=my,
                             MSRP=msrp, Cost=round(msrp * (1 - margin), -2)))
        VERSIONS[(mi, my)] = vehicles[-1]


def model_weight(m, d):
    make, model, seg, pt, origin, base = m
    y = d.year + (d.timetuple().tm_yday / 366)
    w = 1.0
    if origin == "صيني":
        w *= 0.55 + 0.75 * (y - 2023)          # Chinese brands gain share fast
    if pt == "هجين":
        w *= 0.8 + 0.45 * (y - 2023)
    if pt == "كهربائي":
        w *= 0.25 + 0.55 * (y - 2023)
    if make in ("Toyota", "Hyundai", "Kia"):
        w *= 1.6
    if seg == "فاخرة":
        w *= 0.45
    if base > 250000:
        w *= 0.6
    return max(w, 0.05)


# ------------------------------------------------------------------ people
FIRST_M = ["عبدالله", "محمد", "فيصل", "خالد", "عمر", "تركي", "سعد", "ناصر", "فهد", "ماجد", "يزيد", "بندر", "سلطان", "طلال", "حمد", "علي", "إبراهيم", "زياد", "راكان", "مشعل"]
FIRST_F = ["سارة", "نورة", "ريم", "لمى", "حصة", "دانة", "مها", "جواهر", "شهد", "روان", "غادة", "أثير", "لجين", "جود", "هيفاء", "مشاعل", "أمل", "فاطمة", "عائشة", "ليان"]
LAST = ["العتيبي", "القحطاني", "الغامدي", "الحربي", "الشهري", "الدوسري", "المطيري", "الزهراني", "العنزي", "الشمري", "السبيعي", "المالكي", "الرشيدي", "الجهني", "العمري", "اليامي"]
customers = []
for cid in range(1, 4201):
    jd = date(2021, 1, 1) + timedelta(days=random.randint(0, 1825)) if cid > 500 else date(2019, 1, 1) + timedelta(days=random.randint(0, 720))
    jd = min(jd, date(2025, 12, 20))
    g = "أنثى" if random.random() < 0.27 else "ذكر"
    ctype = wpick([("أفراد", 86), ("شركات", 11), ("حكومي", 3)])
    city = random.choices(list(CITY_W), weights=list(CITY_W.values()))[0]
    customers.append(dict(CustomerID=cid, CustomerName=f"{random.choice(FIRST_F if g == 'أنثى' else FIRST_M)} {random.choice(LAST)}",
                          Gender=g, AgeGroup=wpick([("18-24", 12), ("25-34", 33), ("35-44", 28), ("45-54", 17), ("55+", 10)]),
                          Nationality=wpick([("سعودي", 74), ("مقيم عربي", 12), ("مقيم آسيوي", 10), ("مقيم غربي", 4)]),
                          City=city, Region=CITY_REGION[city], CustomerType=ctype, JoinDate=jd))
employees, eid = [], 0
STAFF = {}
for b in BRANCHES:
    roles = (["مدير فرع"] + ["مستشار مبيعات"] * (7 if b[4] == "معرض رئيسي" else 4) if b[7] else []) + (["مستشار خدمة"] * 3 if b[8] else [])
    for r in roles:
        eid += 1
        g = random.random() < 0.2
        employees.append(dict(EmployeeID=eid, EmployeeName=f"{random.choice(FIRST_F if g else FIRST_M)} {random.choice(LAST)}", BranchID=b[0],
                              Role=r, HireDate=max(b[5], date(2015, 1, 1)) + timedelta(days=random.randint(0, 1500))))
        STAFF.setdefault((b[0], r), []).append(eid)

# ------------------------------------------------------------------ deals
PARTNERS = ["مصرف الأمان", "بنك الوفاق", "تمويل اليسر", "الريادة للتأجير"]
sales, deal_id = [], 900000
cust_cum = list(accumulate([3.0 if c["CustomerType"] != "أفراد" else 1.0 for c in customers]))
for d in days(START, END):
    y = d.year
    mult = {2023: 1.0, 2024: 1.1, 2025: 1.21}[y]
    r0, r1 = RAMADAN[y]
    if r0 <= d <= r1:
        mult *= 1.35
    if EID_FITR[y] <= d <= EID_FITR[y] + timedelta(days=5):
        mult *= 1.6
    if d.month == 12:
        mult *= 1.45          # year-end clearance
    if d.month in (10, 11):
        mult *= 1.15          # new model-year launches
    if d.month in (6, 7, 8):
        mult *= 0.8
    if d.weekday() == 4:
        mult *= 0.4           # Friday: showrooms open late
    if d.weekday() in (3, 5):
        mult *= 1.25
    n = max(0, int(random.gauss(5.0 * mult, 1.6)))
    weights = [model_weight(m, d) for m in MODELS]
    for _ in range(n):
        cust = customers[random.choices(range(len(customers)), cum_weights=cust_cum)[0]]
        if cust["JoinDate"] > d:
            cust = customers[random.randint(0, 499)]
        branch = random.choice(SALE_BRANCH_BY_CITY[cust["City"]])
        mi = random.choices(range(len(MODELS)), weights=weights)[0]
        used = random.random() < 0.22
        cur_my = y + 1 if d.month >= 10 else y
        my = cur_my - random.randint(2, 5) if used else (cur_my if random.random() < 0.85 else cur_my - 1)
        my = max(2020, min(2026, my))
        v = VERSIONS[(mi, my)]
        list_price = v["MSRP"] if not used else round(v["MSRP"] * (0.92 - 0.08 * (cur_my - my)) / 500) * 500
        cost = v["Cost"] if not used else round(list_price * 0.86, -2)
        days_stock = int(random.gammavariate(2.0, 24 if v["Segment"] != "فاخرة" and v["Powertrain"] != "كهربائي" else 34))
        disc = random.uniform(0.02, 0.05)
        if branch == 5:
            disc += random.uniform(0.04, 0.07)      # Dammam over-discounts
        if d.month == 12:
            disc += 0.03
        if days_stock > 90:
            disc += random.uniform(0.03, 0.05)
        if used:
            disc *= 0.6
        discount = round(list_price * disc, -2)
        price = list_price - discount
        fin_share = {2023: 0.52, 2024: 0.57, 2025: 0.62}[y] + (0.15 if cust["CustomerType"] == "شركات" else 0)
        pay = "كاش" if random.random() > fin_share else ("تأجير منتهي بالتمليك" if random.random() < 0.3 else "تمويل بنكي")
        financed = pay != "كاش"
        partner = random.choice(PARTNERS[:3] if pay == "تمويل بنكي" else PARTNERS[3:]) if financed else None
        down = round(price * random.choice([0.1, 0.15, 0.2, 0.3]), -2) if financed else None
        term = random.choice([36, 48, 60]) if financed else None
        commission = round((price - down) * random.uniform(0.018, 0.03), -1) if financed else 0.0
        addon = round(random.uniform(2500, 9000) * (1.5 if financed else 0.8) * (1.6 if v["Segment"] == "فاخرة" else 1), -1) if random.random() < (0.8 if financed else 0.45) else 0.0
        trade = random.random() < 0.24
        deal_id += 1
        sales.append(dict(DealID=deal_id, DealDate=d, BranchID=branch, EmployeeID=random.choice(STAFF[(branch, "مستشار مبيعات")]),
                          CustomerID=cust["CustomerID"], VehicleID=v["VehicleID"], Condition="مستعمل" if used else "جديد",
                          ListPrice=float(list_price), DiscountAmount=float(discount), SalePrice=float(price), VehicleCost=float(cost),
                          PaymentType=pay, FinancePartner=partner, DownPayment=down, TermMonths=term, FinanceCommission=float(commission),
                          AddOnRevenue=float(addon), AddOnCost=round(addon * 0.55, 2), TradeIn=trade,
                          TradeInValue=float(round(random.uniform(18000, 90000), -3)) if trade else None, DaysInStock=days_stock))

# ------------------------------------------------------------------ leads (funnel)
SOURCES = {"سناب شات": (0.30, 0.07, 0.30), "إنستقرام": (0.18, 0.10, 0.35), "الموقع الإلكتروني": (0.17, 0.13, 0.40),
           "زيارة المعرض": (0.16, 0.28, 0.80), "إحالة": (0.11, 0.33, 0.70), "معرض سيارات": (0.08, 0.12, 0.45)}  # volume, conversion, test drive (not converted)
leads, lead_id = [], 0
conv_w = [(s, v[0] * v[1]) for s, v in SOURCES.items()]
by_source = {s: 0 for s in SOURCES}
for s_ in sales:
    if random.random() < 0.55:
        src = wpick(conv_w)
        by_source[src] += 1
        lead_id += 1
        leads.append(dict(LeadID=lead_id, LeadDate=s_["DealDate"] - timedelta(days=random.randint(2, 30)), Source=src, BranchID=s_["BranchID"],
                          VehicleID=s_["VehicleID"], TestDrive=random.random() < 0.86, Converted=True, DealID=s_["DealID"]))
showrooms = [b[0] for b in BRANCHES if b[7]]
for src, (_, conv, td) in SOURCES.items():
    for _ in range(int(by_source[src] * (1 / conv - 1))):
        lead_id += 1
        d = START + timedelta(days=random.randint(0, (END - START).days))
        leads.append(dict(LeadID=lead_id, LeadDate=d, Source=src, BranchID=random.choice(showrooms),
                          VehicleID=random.choice(vehicles)["VehicleID"], TestDrive=random.random() < td * 0.45, Converted=False, DealID=None))
leads = [l for l in leads if START <= l["LeadDate"] <= END]
leads.sort(key=lambda r: (r["LeadDate"], r["LeadID"]))

# ------------------------------------------------------------------ service visits
STYPES = {"صيانة دورية": (0.45, 450, 520), "إصلاح": (0.2, 1400, 2600), "ضمان": (0.12, 0, 0), "تكييف": (0.13, 650, 900), "إطارات": (0.10, 150, 2200)}
service, sid = [], 0
owned = [(s_["CustomerID"], s_["VehicleID"]) for s_ in sales]
for d in days(START, END):
    mult = {2023: 1.0, 2024: 1.08, 2025: 1.17}[d.year] * (0.35 if d.weekday() == 4 else 1)
    n = max(0, int(random.gauss(6.2 * mult, 2)))
    for _ in range(n):
        if random.random() < 0.7 and owned:
            cid, vid_ = random.choice(owned)
        else:
            cid, vid_ = random.randint(1, len(customers)), random.choice(vehicles)["VehicleID"]
        city = customers[cid - 1]["City"]
        branch = random.choice(SERVICE_BRANCH_BY_CITY[city])
        tw = {k: v[0] * (3.2 if k == "تكييف" and d.month in (6, 7, 8) else 1) for k, v in STYPES.items()}
        st = random.choices(list(tw), weights=list(tw.values()))[0]
        _, lab, parts = STYPES[st]
        labor = round(lab * random.uniform(0.7, 1.4), -1)
        parts_rev = round(parts * random.uniform(0.6, 1.5), -1)
        if st == "ضمان":
            labor, parts_rev = 0.0, 0.0
        cost = round(labor * 0.35 + parts_rev * 0.68 + (180 if st == "ضمان" else 0), 2)
        hours = round(random.gammavariate(2.2, 7 if st in ("صيانة دورية", "إطارات", "تكييف") else 16) + (10 if branch == 8 else 0), 1)
        comeback = random.random() < (0.035 + (0.09 if hours > 48 else 0) + (0.04 if st == "إصلاح" else 0))
        csat_base = 4.5 - (1.2 if hours > 48 else 0) - (1.3 if comeback else 0)
        sid += 1
        service.append(dict(VisitID=sid, VisitDate=d, BranchID=branch, EmployeeID=random.choice(STAFF[(branch, "مستشار خدمة")]),
                            CustomerID=cid, VehicleID=vid_, ServiceType=st, LaborRevenue=float(labor), PartsRevenue=float(parts_rev),
                            ServiceCost=cost, TurnaroundHours=hours, CSAT=int(min(5, max(1, round(random.gauss(csat_base, 0.7))))) if random.random() < 0.7 else None,
                            IsComeback=comeback))

# ------------------------------------------------------------------ targets (monthly revenue and units by branch x segment)
SEGMENTS = ["سيدان", "دفع رباعي", "بيك أب", "هاتشباك", "فاخرة"]
seg_of = {v["VehicleID"]: v["Segment"] for v in vehicles}
act = {}
for s_ in sales:
    k = (s_["DealDate"].year, s_["DealDate"].month, s_["BranchID"], seg_of[s_["VehicleID"]])
    a = act.setdefault(k, [0.0, 0])
    a[0] += s_["SalePrice"]; a[1] += 1
targets = []
for y in (2023, 2024, 2025):
    for m in range(1, 13):
        for b in showrooms:
            for seg in SEGMENTS:
                ref = act.get((y - 1, m, b, seg) if y > 2023 else (y, m, b, seg), [0.0, 0])
                f = random.uniform(0.95, 1.06) if y == 2023 else random.uniform(1.08, 1.15) * (1.28 if b == 3 else 1)
                targets.append(dict(Month=date(y, m, 1), BranchID=b, Segment=seg, RevenueTarget=round(ref[0] * f, -3), UnitsTarget=round(ref[1] * f)))

# ------------------------------------------------------------------ workbook
wb = Workbook()


def sheet(ws, name, rows, cols, fmts):
    ws.title = name
    ws.append(cols)
    for r in rows:
        ws.append([r[c] for c in cols])
    for col, f in fmts.items():
        for cell in ws[col][1:]:
            cell.number_format = f
    t = Table(displayName=name, ref=f"A1:{ws.cell(row=1, column=len(cols)).column_letter}{len(rows) + 1}")
    t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium9", showRowStripes=True)
    ws.add_table(t)
    ws.sheet_view.rightToLeft = True
    ws.freeze_panes = "A2"
    for i, c in enumerate(cols, 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = max(12, len(c) + 4)


sheet(wb.active, "Sales", sales, ["DealID", "DealDate", "BranchID", "EmployeeID", "CustomerID", "VehicleID", "Condition", "ListPrice",
      "DiscountAmount", "SalePrice", "VehicleCost", "PaymentType", "FinancePartner", "DownPayment", "TermMonths", "FinanceCommission",
      "AddOnRevenue", "AddOnCost", "TradeIn", "TradeInValue", "DaysInStock"], {"B": "yyyy-mm-dd"})
sheet(wb.create_sheet(), "Leads", leads, ["LeadID", "LeadDate", "Source", "BranchID", "VehicleID", "TestDrive", "Converted", "DealID"], {"B": "yyyy-mm-dd"})
sheet(wb.create_sheet(), "Service", service, ["VisitID", "VisitDate", "BranchID", "EmployeeID", "CustomerID", "VehicleID", "ServiceType",
      "LaborRevenue", "PartsRevenue", "ServiceCost", "TurnaroundHours", "CSAT", "IsComeback"], {"B": "yyyy-mm-dd"})
sheet(wb.create_sheet(), "Vehicles", vehicles, ["VehicleID", "Make", "Model", "Segment", "Powertrain", "Origin", "ModelYear", "MSRP", "Cost"], {})
sheet(wb.create_sheet(), "Branches", [dict(BranchID=b[0], BranchName=b[1], City=b[2], Region=b[3], BranchType=b[4], OpenDate=b[5],
      MonthlyFixedCost=b[6]) for b in BRANCHES], ["BranchID", "BranchName", "City", "Region", "BranchType", "OpenDate", "MonthlyFixedCost"], {"F": "yyyy-mm-dd"})
sheet(wb.create_sheet(), "Employees", employees, ["EmployeeID", "EmployeeName", "BranchID", "Role", "HireDate"], {"E": "yyyy-mm-dd"})
sheet(wb.create_sheet(), "Customers", customers, ["CustomerID", "CustomerName", "Gender", "AgeGroup", "Nationality", "City", "Region",
      "CustomerType", "JoinDate"], {"I": "yyyy-mm-dd"})
sheet(wb.create_sheet(), "Targets", targets, ["Month", "BranchID", "Segment", "RevenueTarget", "UnitsTarget"], {"A": "yyyy-mm-dd"})
wb.save(OUT)
print(f"{len(sales)} deals, {len(leads)} leads, {len(service)} service visits, {len(vehicles)} vehicles, {len(customers)} customers, "
      f"{len(employees)} employees, {len(targets)} targets")
