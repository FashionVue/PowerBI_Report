"""Generate data/SalesSample.xlsx - a deterministic, fictional Saudi fashion retailer (FashionVue).

Usage:  python make_sample.py SalesSample.xlsx

Three years of order lines (2023-01-01 .. 2025-12-31) with realistic Saudi retail seasonality
(Ramadan and Eid moving ~11 days earlier each year, Founding Day, National Day, back to school,
White Friday, summer slowdown) and deliberate, explainable patterns:
  * Northern region misses its sales target (targets assumed a new Tabuk store would ramp faster)
  * BNPL (Tabby / Tamara) grows fast; Cash shrinks
  * Brand "Sahra" has a high return rate, mostly for Size
  * App orders have a higher basket (AOV) than Website orders
  * Platinum customers are a small share of customers but a large share of sales
  * Slow deliveries (> 3 days) bring lower ratings and more returns
  * Referral customers retain best; TikTok brings many new customers who rarely come back
Every sheet holds one Excel Table with the same name as the sheet.
"""
import random
import sys
from itertools import accumulate
from datetime import date, timedelta
from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

random.seed(20250101)
OUT = sys.argv[1] if len(sys.argv) > 1 else "SalesSample.xlsx"
START, END = date(2023, 1, 1), date(2025, 12, 31)


def daterange(a, b):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)


# ----------------------------------------------------------------- calendar events
RAMADAN = {2023: (date(2023, 3, 23), date(2023, 4, 20)), 2024: (date(2024, 3, 11), date(2024, 4, 9)),
           2025: (date(2025, 3, 1), date(2025, 3, 29))}
EID_FITR = {2023: date(2023, 4, 21), 2024: date(2024, 4, 10), 2025: date(2025, 3, 30)}
EID_ADHA = {2023: date(2023, 6, 28), 2024: date(2024, 6, 16), 2025: date(2025, 6, 6)}


def season(d):
    """Retail season of a date (same rules as the Power Query Date table)."""
    y = d.year
    r0, r1 = RAMADAN[y]
    if r0 <= d <= r1:
        return "Ramadan"
    if EID_FITR[y] <= d <= EID_FITR[y] + timedelta(days=3):
        return "Eid al-Fitr"
    if EID_ADHA[y] <= d <= EID_ADHA[y] + timedelta(days=3):
        return "Eid al-Adha"
    if date(y, 2, 20) <= d <= date(y, 2, 23):
        return "Founding Day"
    if date(y, 9, 18) <= d <= date(y, 9, 24):
        return "National Day"
    if date(y, 11, 20) <= d <= date(y, 11, 30):
        return "White Friday"
    if date(y, 8, 15) <= d <= date(y, 9, 5):
        return "Back to School"
    if date(y, 6, 1) <= d <= date(y, 8, 31):
        return "Summer"
    return "Regular"


SEASON_MULT = {"Ramadan": 1.75, "Eid al-Fitr": 2.0, "Eid al-Adha": 1.45, "Founding Day": 1.4, "National Day": 1.6,
               "White Friday": 2.3, "Back to School": 1.3, "Summer": 0.72, "Regular": 1.0}
YEAR_MULT = {2023: 1.0, 2024: 1.17, 2025: 1.36}

# ----------------------------------------------------------------- geography and stores
REGIONS = {"Central": ["Riyadh"], "Western": ["Jeddah", "Makkah", "Madinah"], "Eastern": ["Dammam", "Khobar"],
           "Southern": ["Abha"], "Northern": ["Tabuk"]}
CITY_REGION = {c: r for r, cs in REGIONS.items() for c in cs}
CITY_WEIGHT = {"Riyadh": 30, "Jeddah": 20, "Makkah": 8, "Madinah": 6, "Dammam": 11, "Khobar": 9, "Abha": 8, "Tabuk": 8}
FAST_CITIES = {"Riyadh": (1, 2), "Jeddah": (1, 2), "Dammam": (1, 3), "Khobar": (1, 3), "Makkah": (2, 3),
               "Madinah": (2, 4), "Abha": (3, 6), "Tabuk": (3, 7)}

STORES = [  # id, name, city, type, sqm, open date
    (1, "Riyadh Park Flagship", "Riyadh", "Mall flagship", 1200, date(2019, 5, 1)),
    (2, "Granada Mall", "Riyadh", "Mall", 600, date(2020, 9, 15)),
    (3, "Tahlia Street Riyadh", "Riyadh", "Street", 320, date(2021, 2, 1)),
    (4, "Red Sea Mall Flagship", "Jeddah", "Mall flagship", 1100, date(2019, 11, 1)),
    (5, "Tahlia Street Jeddah", "Jeddah", "Street", 350, date(2022, 3, 1)),
    (6, "Makkah Mall", "Makkah", "Mall", 480, date(2021, 6, 1)),
    (7, "Al Noor Mall", "Madinah", "Mall", 450, date(2021, 10, 1)),
    (8, "Al Othaim Mall", "Dammam", "Mall", 620, date(2020, 1, 15)),
    (9, "Al Rashid Mall", "Khobar", "Mall", 540, date(2020, 12, 1)),
    (10, "Abha Mall", "Abha", "Mall", 400, date(2022, 8, 1)),
    (11, "Tabuk Park", "Tabuk", "Mall", 380, date(2024, 6, 1)),
    (12, "Online", "Online", "Online", None, date(2019, 1, 1)),
]
MANAGERS = ["Hind Alsubaie", "Fahad Alqahtani", "Rawan Almalki", "Majed Alharbi", "Ghada Alshammari", "Yazeed Alotaibi",
            "Lulwa Aldosari", "Bandar Alghamdi", "Shahad Alzahrani", "Talal Alanazi", "Mashael Alrashidi", "Waleed Alshehri"]

FIRST_F = ["Sara", "Noura", "Reem", "Lama", "Hessa", "Dana", "Maha", "Jawaher", "Shahad", "Rawan", "Ghada", "Atheer",
           "Lujain", "Joud", "Haifa", "Mashael", "Amal", "Fatimah", "Aisha", "Layan"]
FIRST_M = ["Abdullah", "Mohammed", "Faisal", "Khalid", "Omar", "Turki", "Saad", "Nasser", "Fahad", "Majed", "Yazeed",
           "Bandar", "Sultan", "Talal", "Hamad", "Ali", "Ibrahim", "Ziyad", "Rakan", "Meshal"]
LAST_SA = ["Alotaibi", "Alqahtani", "Alghamdi", "Alharbi", "Alshehri", "Aldosari", "Almutairi", "Alzahrani", "Alanazi",
           "Alshammari", "Alsubaie", "Almalki", "Alrashidi", "Aljohani", "Alomari", "Alyami"]
LAST_EX = {"GCC": ["Alkuwari", "Almansoori", "Alhashmi", "Albalushi"], "Arab expat": ["Haddad", "Khalil", "Nasser", "Saleh", "Mansour"],
           "Asian expat": ["Khan", "Rahman", "Santos", "Nair", "Iqbal"], "Western expat": ["Smith", "Taylor", "Martin", "Brown"]}

# ----------------------------------------------------------------- products
BRANDS = {  # brand: (categories, gender, base price, return extra, size-driven)
    "Layali": (["Abayas"], "Women", 520, 0.00, False),
    "Noor Atelier": (["Abayas", "Dresses"], "Women", 880, 0.01, False),
    "Sahra": (["Dresses"], "Women", 340, 0.11, True),
    "Qamar": (["Thobes"], "Men", 260, 0.00, False),
    "Rimal Sport": (["Shoes"], "Unisex", 330, 0.03, True),
    "Dana Kids": (["Kidswear"], "Kids", 140, 0.01, True),
    "Zahra": (["Dresses", "Accessories"], "Women", 290, 0.01, False),
    "Oud & Co": (["Accessories"], "Unisex", 410, 0.00, False),
}
SUBCATS = {"Abayas": ["Classic Abaya", "Embroidered Abaya", "Open Abaya"], "Dresses": ["Evening Dress", "Day Dress", "Kaftan"],
           "Thobes": ["Cotton Thobe", "Linen Thobe", "Winter Thobe"], "Shoes": ["Sneakers", "Sandals", "Heels"],
           "Kidswear": ["School Uniform", "Kids Thobe", "Kids Dress"], "Accessories": ["Shemagh", "Handbag", "Scarf", "Perfume"]}
COLORS = ["Black", "Ivory", "Navy", "Sand", "Olive", "Burgundy", "Rose", "Grey", "White", "Emerald"]
COLLECTIONS = [("Core", date(2022, 6, 1))]
for y in (2023, 2024, 2025):
    COLLECTIONS += [(f"Ramadan {y}", RAMADAN[y][0] - timedelta(days=28)), (f"Summer {y}", date(y, 5, 15)),
                    (f"National Day {y}", date(y, 9, 1)), (f"Winter {y}", date(y, 10, 15))]

products = []
pid = 0
for brand, (cats, gender, base, _, _) in BRANDS.items():
    n = 11 if brand in ("Layali", "Qamar", "Sahra", "Zahra") else 9
    for i in range(n):
        pid += 1
        cat = cats[i % len(cats)]
        sub = random.choice(SUBCATS[cat])
        coll, launch = random.choice(COLLECTIONS[:1] * 4 + COLLECTIONS[1:])
        if cat == "Abayas" and random.random() < 0.5:
            coll, launch = random.choice([c for c in COLLECTIONS if c[0].startswith("Ramadan")])
        if cat == "Thobes" and random.random() < 0.4:
            coll, launch = random.choice([c for c in COLLECTIONS if c[0].startswith(("National", "Winter"))])
        price = round(base * random.uniform(0.6, 1.8) / 5) * 5
        tier = "Luxury" if price >= 700 else "Premium" if price >= 320 else "Essential"
        cost = round(price * random.uniform(0.34, 0.48), 2)
        g = gender if gender != "Unisex" else random.choice(["Women", "Men", "Unisex"])
        products.append(dict(ProductID=pid, ProductName=f"{brand} {sub} {random.choice(COLORS)} {i + 1:02d}", Brand=brand,
                             Category=cat, SubCategory=sub, Gender=g, Collection=coll, Color=random.choice(COLORS),
                             PriceTier=tier, UnitCost=cost, ListPrice=price, LaunchDate=launch))
CAT_SEASON = {  # category weight boosts by season
    "Ramadan": {"Abayas": 2.6, "Dresses": 1.4, "Accessories": 1.5}, "Eid al-Fitr": {"Thobes": 2.2, "Kidswear": 2.0, "Dresses": 1.6},
    "Eid al-Adha": {"Thobes": 1.8, "Kidswear": 1.5}, "National Day": {"Thobes": 2.0, "Accessories": 1.6},
    "Founding Day": {"Thobes": 1.6, "Abayas": 1.4}, "Back to School": {"Kidswear": 3.5, "Shoes": 1.8},
    "White Friday": {"Shoes": 1.6, "Accessories": 1.7, "Dresses": 1.3}, "Summer": {"Shoes": 1.3, "Dresses": 1.2}}

# ----------------------------------------------------------------- customers
TIERS = [("Bronze", 0.55, 0.7), ("Silver", 0.27, 1.1), ("Gold", 0.13, 2.0), ("Platinum", 0.05, 5.5)]
ACQ = [("Instagram", 0.25, 0.95), ("Snapchat", 0.22, 1.00), ("TikTok", 0.18, 0.55),  # (channel, share, purchase frequency)
       ("Google", 0.12, 1.00), ("Referral", 0.10, 1.65), ("Walk-in", 0.13, 1.10)]
NATIONALITY = [("Saudi", 0.70), ("GCC", 0.05), ("Arab expat", 0.12), ("Asian expat", 0.09), ("Western expat", 0.04)]
AGE = [("18-24", 0.18), ("25-34", 0.34), ("35-44", 0.26), ("45-54", 0.14), ("55+", 0.08)]


def wchoice(pairs):
    return random.choices([p[0] for p in pairs], weights=[p[1] for p in pairs])[0]


customers = []
N_CUST = 2400
join_days = [d for d in daterange(START, date(2025, 11, 30))]
for cid in range(1, N_CUST + 1):
    # more joiners each year (business grows)
    while True:
        jd = random.choice(join_days)
        if random.random() < {2023: 0.75, 2024: 0.9, 2025: 1.0}[jd.year]:
            break
    if cid <= 260:  # an existing base that joined before the data starts
        jd = date(2022, 1, 1) + timedelta(days=random.randint(0, 364))
    gender = "Female" if random.random() < 0.66 else "Male"
    nat = wchoice(NATIONALITY)
    first = random.choice(FIRST_F if gender == "Female" else FIRST_M)
    last = random.choice(LAST_SA) if nat == "Saudi" else random.choice(LAST_EX[nat])
    city = random.choices(list(CITY_WEIGHT), weights=list(CITY_WEIGHT.values()))[0]
    tier = random.choices([t[0] for t in TIERS], weights=[t[1] for t in TIERS])[0]
    acq = wchoice([(a[0], a[1]) for a in ACQ])
    customers.append(dict(CustomerID=cid, CustomerName=f"{first} {last}", Gender=gender, AgeGroup=wchoice(AGE),
                          Nationality=nat, City=city, Region=CITY_REGION[city], LoyaltyTier=tier,
                          AcquisitionChannel=acq, JoinDate=jd))
TIER_W = {t[0]: t[2] for t in TIERS}
ACQ_RET = {a[0]: a[2] for a in ACQ}

# ----------------------------------------------------------------- employees
ROLES = ["Store Manager", "Sales Associate", "Sales Associate", "Stylist", "Cashier"]
employees = []
eid = 0
for s in STORES:
    staff = (["Customer Care"] * 6) if s[3] == "Online" else ROLES + (["Sales Associate", "Stylist"] if s[3] == "Mall flagship" else [])
    for role in staff:
        eid += 1
        g = random.random() < 0.5
        employees.append(dict(EmployeeID=eid, EmployeeName=f"{random.choice(FIRST_F if g else FIRST_M)} {random.choice(LAST_SA)}",
                              StoreID=s[0], Role=role, HireDate=max(s[5], date(2019, 1, 1)) + timedelta(days=random.randint(0, 700))))
STAFF = {s[0]: [e["EmployeeID"] for e in employees if e["StoreID"] == s[0] and e["Role"] != "Store Manager"] for s in STORES}

# ----------------------------------------------------------------- campaigns
campaigns = []
cmp_id = 0
for y in (2023, 2024, 2025):
    plan = [("Ramadan Kareem", "Snapchat", RAMADAN[y][0] - timedelta(days=7), RAMADAN[y][1], 260000, 1.25),
            ("Eid Collection", "Instagram", EID_FITR[y] - timedelta(days=10), EID_FITR[y] + timedelta(days=3), 140000, 1.1),
            ("Founding Day", "SMS", date(y, 2, 18), date(y, 2, 23), 40000, 1.0),
            ("Back to School", "TikTok", date(y, 8, 10), date(y, 9, 5), 120000, 0.6),
            ("National Day", "Influencer", date(y, 9, 15), date(y, 9, 24), 110000, 1.05),
            ("White Friday", "Google", date(y, 11, 18), date(y, 11, 30), 210000, 1.2),
            ("Summer Sale", "Instagram", date(y, 7, 1), date(y, 7, 31), 70000, 0.85)]
    for name, ch, s0, s1, budget, strength in plan:
        cmp_id += 1
        campaigns.append(dict(CampaignID=cmp_id, CampaignName=f"{name} {y}", Channel=ch, StartDate=s0, EndDate=s1,
                              Budget=round(budget * YEAR_MULT[y] * random.uniform(0.9, 1.1), -3), _strength=strength))

# ----------------------------------------------------------------- order lines
pay_methods = ["Mada", "Apple Pay", "Credit Card", "Tabby", "Tamara", "Cash"]


def payment(year, channel):
    bnpl = {2023: 0.08, 2024: 0.15, 2025: 0.24}[year]
    apple = {2023: 0.16, 2024: 0.21, 2025: 0.25}[year]
    cash = {2023: 0.20, 2024: 0.14, 2025: 0.09}[year] if channel == "Store" else 0.0
    card = 0.18
    mada = max(0.05, 1 - bnpl - apple - cash - card)
    return random.choices(pay_methods, weights=[mada, apple, card, bnpl * 0.55, bnpl * 0.45, cash])[0]


cust_by_city = {}
for c in customers:
    cust_by_city.setdefault(c["City"], []).append(c)
stores_by_city = {}
for s in STORES[:-1]:
    stores_by_city.setdefault(s[2], []).append(s)
all_cust = customers
cust_weight = []
for c in all_cust:
    w = TIER_W[c["LoyaltyTier"]] * ACQ_RET[c["AcquisitionChannel"]]
    cust_weight.append(w)

sales = []
oid = 500000
BASE_ORDERS = 12.4
for d in daterange(START, END):
    s = season(d)
    mult = SEASON_MULT[s] * YEAR_MULT[d.year]
    r0, r1 = RAMADAN[d.year]
    if s == "Ramadan" and (r1 - d).days < 10:
        mult *= 1.25  # last ten nights
    wd = d.weekday()  # Mon=0 .. Sun=6 ; KSA weekend Fri(4)/Sat(5)
    mult *= 1.25 if wd in (4, 5) else 1.1 if wd == 3 else 1.0
    n_orders = max(0, int(random.gauss(BASE_ORDERS * mult, 3)))
    active_camps = [c for c in campaigns if c["StartDate"] <= d <= c["EndDate"]]
    eligible = [i for i, c in enumerate(all_cust) if c["JoinDate"] <= d]
    weights = [cust_weight[i] * (1.6 if (d - all_cust[i]["JoinDate"]).days < 60 else 1.0) *
               (0.35 if all_cust[i]["AcquisitionChannel"] == "TikTok" and (d - all_cust[i]["JoinDate"]).days > 120 else 1.0)
               for i in eligible]
    cum = list(accumulate(weights))
    boosts = CAT_SEASON.get(s, {})
    avail = [p for p in products if p["LaunchDate"] <= d]
    pw_base = [boosts.get(p["Category"], 1.0) * (1.4 if p["Collection"].endswith(str(d.year)) else 1.0) for p in avail]
    pw_bronze = [w * (0.6 if p["PriceTier"] == "Luxury" else 1.0) for w, p in zip(pw_base, avail)]
    for _ in range(n_orders):
        cust = all_cust[random.choices(eligible, cum_weights=cum)[0]]
        app_share = {2023: 0.24, 2024: 0.32, 2025: 0.40}[d.year]
        web_share = {2023: 0.34, 2024: 0.31, 2025: 0.28}[d.year]
        ch = random.choices(["App", "Website", "Store"], weights=[app_share, web_share, 1 - app_share - web_share])[0]
        if ch == "Store":
            local = [st for st in stores_by_city.get(cust["City"], []) if st[5] <= d]
            if not local:
                local = [st for st in STORES[:-1] if CITY_REGION[st[2]] == cust["Region"] and st[5] <= d] or \
                        [st for st in STORES[:-1] if st[2] == "Riyadh"]
            store = random.choice(local)
        else:
            store = STORES[-1]
        emp = random.choice(STAFF[store[0]])
        camp = None
        if active_camps:
            pick = random.choices(active_camps, weights=[c["_strength"] for c in active_camps])[0]
            if random.random() < (0.45 if ch != "Store" else 0.25) * pick["_strength"]:
                camp = pick
        pay = payment(d.year, ch)
        oid += 1
        n_lines = random.choices([1, 2, 3, 4], weights=[52, 28, 13, 7] if ch != "App" else [40, 31, 18, 11])[0]
        n_lines += 1 if cust["LoyaltyTier"] == "Platinum" and random.random() < 0.5 else 0
        delivery = None
        if ch != "Store":
            lo, hi = FAST_CITIES[cust["City"]]
            delivery = random.randint(lo, hi) + (random.randint(0, 3) if s in ("White Friday", "Ramadan", "Eid al-Fitr") else 0)
        ship = 0.0 if ch == "Store" else round(random.choice([15, 19, 25, 29, 35]) * (1.4 if cust["City"] in ("Abha", "Tabuk") else 1), 2)
        pw = pw_bronze if cust["LoyaltyTier"] == "Bronze" else pw_base
        for ln in range(1, n_lines + 1):
            p = random.choices(avail, weights=pw)[0]
            qty = random.choices([1, 2, 3], weights=[74, 20, 6])[0]
            disc = 0.0
            if camp or s == "White Friday":
                disc = random.choice([0.1, 0.15, 0.2, 0.3] if s == "White Friday" else [0.0, 0.1, 0.15])
            elif s == "Summer" and random.random() < 0.35:
                disc = random.choice([0.2, 0.3, 0.4])
            elif random.random() < 0.08:
                disc = 0.1
            price = p["ListPrice"]
            amount = round(qty * price * (1 - disc), 2)
            cost = round(qty * p["UnitCost"], 2)
            b = BRANDS[p["Brand"]]
            ret_p = 0.035 + (0.045 if ch != "Store" else 0) + b[3] + (0.07 if delivery and delivery > 3 else 0)
            returned = random.random() < ret_p
            reason = None
            if returned:
                opts = [("Size", 30 + (120 if b[4] and p["Brand"] == "Sahra" else 25 if b[4] else 0)), ("Quality", 18),
                        ("Changed mind", 25), ("Damaged", 8), ("Late delivery", 45 if delivery and delivery > 3 else 2)]
                reason = wchoice(opts)
            rating = None
            if random.random() < 0.58:
                base = 4.45 - (1.3 if delivery and delivery > 3 else 0) - (1.6 if returned else 0) - (0.2 if p["Brand"] == "Sahra" else 0)
                rating = int(min(5, max(1, round(random.gauss(base, 0.8)))))
            sales.append(dict(OrderID=oid, LineNo=ln, OrderDate=d, CustomerID=cust["CustomerID"], ProductID=p["ProductID"],
                              StoreID=store[0], EmployeeID=emp, CampaignID=camp["CampaignID"] if camp else None, Channel=ch,
                              PaymentMethod=pay, Quantity=qty, UnitPrice=float(price), Discount=disc, SalesAmount=amount,
                              CostAmount=cost, ShippingCost=ship if ln == 1 else 0.0, DeliveryDays=delivery,
                              IsReturned=returned, ReturnReason=reason, CustomerRating=rating))

# ----------------------------------------------------------------- targets (monthly, region x category)
actual = {}
for r in sales:
    k = (r["OrderDate"].year, r["OrderDate"].month, customers[r["CustomerID"] - 1]["Region"],
         products[r["ProductID"] - 1]["Category"])
    actual[k] = actual.get(k, 0) + r["SalesAmount"]
targets = []
for y in (2023, 2024, 2025):
    for m in range(1, 13):
        for reg in REGIONS:
            for cat in SUBCATS:
                if y == 2023:
                    base = actual.get((y, m, reg, cat), 0) * random.uniform(0.94, 1.08)
                else:
                    base = actual.get((y - 1, m, reg, cat), 0) * random.uniform(1.10, 1.18)
                    if reg == "Northern":
                        base *= 1.32 if y == 2024 else 1.55  # plan assumed the new Tabuk store would ramp quickly
                targets.append(dict(Month=date(y, m, 1), Region=reg, Category=cat, TargetAmount=round(base, -2)))

# ----------------------------------------------------------------- workbook
wb = Workbook()


def add_sheet(ws, name, rows, columns, formats):
    ws.title = name
    ws.append(columns)
    for r in rows:
        ws.append([r[c] for c in columns])
    for col_letter, fmt in formats.items():
        for cell in ws[col_letter][1:]:
            cell.number_format = fmt
    last = ws.cell(row=1, column=len(columns)).column_letter
    t = Table(displayName=name, ref=f"A1:{last}{len(rows) + 1}")
    t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(t)
    for i, c in enumerate(columns, 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = max(12, len(c) + 4)
    ws.freeze_panes = "A2"


add_sheet(wb.active, "Sales", sales,
          ["OrderID", "LineNo", "OrderDate", "CustomerID", "ProductID", "StoreID", "EmployeeID", "CampaignID", "Channel",
           "PaymentMethod", "Quantity", "UnitPrice", "Discount", "SalesAmount", "CostAmount", "ShippingCost", "DeliveryDays",
           "IsReturned", "ReturnReason", "CustomerRating"],
          {"C": "yyyy-mm-dd", "L": "#,##0.00", "M": "0%", "N": "#,##0.00", "O": "#,##0.00", "P": "#,##0.00"})
add_sheet(wb.create_sheet(), "Products", products,
          ["ProductID", "ProductName", "Brand", "Category", "SubCategory", "Gender", "Collection", "Color", "PriceTier",
           "UnitCost", "ListPrice", "LaunchDate"], {"J": "#,##0.00", "K": "#,##0.00", "L": "yyyy-mm-dd"})
add_sheet(wb.create_sheet(), "Customers", customers,
          ["CustomerID", "CustomerName", "Gender", "AgeGroup", "Nationality", "City", "Region", "LoyaltyTier",
           "AcquisitionChannel", "JoinDate"], {"J": "yyyy-mm-dd"})
store_rows = [dict(StoreID=s[0], StoreName=s[1], City=s[2], Region=CITY_REGION.get(s[2], "Online"), StoreType=s[3],
                   SizeSqm=s[4], OpenDate=s[5], Manager=MANAGERS[i]) for i, s in enumerate(STORES)]
add_sheet(wb.create_sheet(), "Stores", store_rows,
          ["StoreID", "StoreName", "City", "Region", "StoreType", "SizeSqm", "OpenDate", "Manager"], {"G": "yyyy-mm-dd"})
add_sheet(wb.create_sheet(), "Employees", employees, ["EmployeeID", "EmployeeName", "StoreID", "Role", "HireDate"],
          {"E": "yyyy-mm-dd"})
add_sheet(wb.create_sheet(), "Campaigns", campaigns,
          ["CampaignID", "CampaignName", "Channel", "StartDate", "EndDate", "Budget"],
          {"D": "yyyy-mm-dd", "E": "yyyy-mm-dd", "F": "#,##0"})
add_sheet(wb.create_sheet(), "Targets", targets, ["Month", "Region", "Category", "TargetAmount"],
          {"A": "yyyy-mm-dd", "D": "#,##0"})
wb.save(OUT)
print(f"{len(sales)} sales lines, {oid - 500000} orders, {len(products)} products, {len(customers)} customers, "
      f"{len(STORES)} stores, {len(employees)} employees, {len(campaigns)} campaigns, {len(targets)} targets")
