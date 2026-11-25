import random, sys
from datetime import date, timedelta
from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

random.seed(42)
out = sys.argv[1]

products = [
    (1, "Classic Abaya", "Abayas", 180, 420),
    (2, "Embroidered Abaya", "Abayas", 260, 650),
    (3, "Linen Thobe", "Thobes", 120, 290),
    (4, "Cotton Thobe", "Thobes", 90, 220),
    (5, "Silk Shemagh", "Accessories", 60, 160),
    (6, "Leather Bag", "Accessories", 150, 380),
    (7, "Summer Dress", "Dresses", 110, 310),
    (8, "Evening Dress", "Dresses", 240, 720),
    (9, "Sneakers", "Shoes", 140, 350),
    (10, "Sandals", "Shoes", 50, 140),
]
cities = [("Riyadh", "Central"), ("Jeddah", "Western"), ("Makkah", "Western"),
          ("Dammam", "Eastern"), ("Khobar", "Eastern"), ("Madinah", "Western"),
          ("Abha", "Southern"), ("Tabuk", "Northern")]
first = ["Abdullah", "Sara", "Mohammed", "Noura", "Faisal", "Reem", "Khalid", "Lama",
         "Omar", "Hessa", "Turki", "Dana", "Saad", "Maha", "Nasser", "Jawaher"]
last = ["Alotaibi", "Alqahtani", "Alghamdi", "Alharbi", "Alshehri", "Aldosari",
        "Almutairi", "Alzahrani"]

customers = []
for cid in range(1, 121):
    city, region = random.choice(cities)
    customers.append((cid, f"{random.choice(first)} {random.choice(last)}", city, region,
                      random.choice(["Online", "Store"]),
                      date(2023, 1, 1) + timedelta(days=random.randint(0, 600))))

channels = ["Website", "App", "Store"]
sales = []
start, end = date(2024, 1, 1), date(2025, 12, 31)
oid = 100000
d = start
while d <= end:
    # more orders in Ramadan/Eid season months and November (White Friday)
    base = 3 + (3 if d.month in (3, 4, 11) else 0) + (1 if d.year == 2025 else 0)
    for _ in range(random.randint(base - 2, base + 2)):
        oid += 1
        pid, pname, cat, cost, price = random.choice(products)
        cust = random.choice(customers)
        qty = random.choices([1, 2, 3, 4], weights=[60, 25, 10, 5])[0]
        disc = random.choices([0, 0.1, 0.2], weights=[70, 20, 10])[0]
        sales.append((oid, d, cust[0], pid, random.choice(channels), qty, price, disc,
                      round(qty * price * (1 - disc), 2), round(qty * cost, 2)))
    d += timedelta(days=1)

wb = Workbook()

def add_sheet(ws, name, headers, rows, formats):
    ws.title = name
    ws.append(headers)
    for r in rows:
        ws.append(list(r))
    for col, fmt in formats.items():
        for cell in ws[col][1:]:
            cell.number_format = fmt
    ref = f"A1:{ws.cell(row=1, column=len(headers)).column_letter}{len(rows) + 1}"
    t = Table(displayName=name, ref=ref)
    t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(t)
    for i, h in enumerate(headers, 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = max(12, len(h) + 4)
    ws.freeze_panes = "A2"

add_sheet(wb.active, "Sales",
          ["OrderID", "OrderDate", "CustomerID", "ProductID", "Channel", "Quantity",
           "UnitPrice", "Discount", "SalesAmount", "CostAmount"],
          sales, {"B": "yyyy-mm-dd", "G": "#,##0.00", "H": "0%", "I": "#,##0.00", "J": "#,##0.00"})
add_sheet(wb.create_sheet(), "Products",
          ["ProductID", "ProductName", "Category", "UnitCost", "ListPrice"],
          products, {"D": "#,##0.00", "E": "#,##0.00"})
add_sheet(wb.create_sheet(), "Customers",
          ["CustomerID", "CustomerName", "City", "Region", "Segment", "JoinDate"],
          customers, {"F": "yyyy-mm-dd"})
wb.save(out)
print(len(sales), "sales rows,", len(customers), "customers,", len(products), "products")
