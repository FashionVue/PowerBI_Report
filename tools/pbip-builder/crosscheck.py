# Cross-checks report bindings and resources against the model dump and files on disk.
import json, glob, os, re, sys
dump, R = sys.argv[1], sys.argv[2]
objs = set(); t = None
for line in open(dump).read().splitlines():
    m = re.match(r"  table (\S+)", line)
    if m: t = m.group(1); continue
    m = re.match(r"    col (.+?) type=", line)
    if m: objs.add(("Column", t, m.group(1)))
    m = re.match(r"    measure \[(.+?)\]", line)
    if m: objs.add(("Measure", t, m.group(1)))
D = os.path.join(R, "definition"); bad = 0
pages = json.load(open(os.path.join(D, "pages", "pages.json")))
ids = set(pages["pageOrder"])
report = json.load(open(os.path.join(D, "report.json")))
for rp in report["resourcePackages"]:
    base = os.path.join(R, "StaticResources", rp["name"])
    for it in rp["items"]:
        if not os.path.isfile(os.path.join(base, it["path"])): print("MISSING RESOURCE", it); bad += 1
regs = {it["name"] for rp in report["resourcePackages"] if rp["name"] == "RegisteredResources" for it in rp["items"]}
assert report["themeCollection"]["customTheme"]["name"] in regs
nvis = 0
for pdir in glob.glob(os.path.join(D, "pages", "*")):
    if not os.path.isdir(pdir): continue
    pg = json.load(open(os.path.join(pdir, "page.json")))
    if pg["name"] != os.path.basename(pdir) or pg["name"] not in ids: print("PAGE NAME", pdir); bad += 1
    img = pg["objects"]["background"][0]["properties"]["image"]["image"]["url"]["expr"]["ResourcePackageItem"]["ItemName"]
    if img not in regs: print("BG NOT REGISTERED", img); bad += 1
    for vf in glob.glob(os.path.join(pdir, "visuals", "*", "visual.json")):
        v = json.load(open(vf)); nvis += 1
        if v["name"] != os.path.basename(os.path.dirname(vf)): print("VISUAL NAME", vf); bad += 1
        s = json.dumps(v)
        for k, ent, prop in re.findall(r'"(Column|Measure)": \{"Expression": \{"SourceRef": \{"Entity": "([^"]+)"\}\}, "Property": "([^"]+)"', s):
            if (k, ent, prop) not in objs: print("MISSING FIELD", k, ent, prop, vf); bad += 1
        for nav in re.findall(r'"navigationSection": \{"expr": \{"Literal": \{"Value": "\'([0-9a-f]+)\'"', s):
            if nav not in ids: print("BAD NAV TARGET", nav); bad += 1
        for role, ps in v["visual"].get("query", {}).get("queryState", {}).items():
            for p in ps["projections"]:
                k = next(iter(p["field"])); f = p["field"][k]
                if p["queryRef"] != f"{f['Expression']['SourceRef']['Entity']}.{f['Property']}": print("QUERYREF", vf); bad += 1
        for sel in re.findall(r'"metadata": "([^"]+)"', s):
            refs = [p["queryRef"] for ps in v["visual"]["query"]["queryState"].values() for p in ps["projections"]]
            if sel not in refs: print("SELECTOR NOT IN QUERY", sel, vf); bad += 1
        pos = v["position"]
        if pos["x"] + pos["width"] > 1920 or pos["y"] + pos["height"] > 1080: print("OFF CANVAS", vf); bad += 1
print(f"pages={len(ids)} visuals={nvis} problems={bad}")
sys.exit(1 if bad else 0)
