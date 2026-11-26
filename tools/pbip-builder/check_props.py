# Cross-check formatting object/property names (theme visualStyles and visual.json objects)
# against the official report theme schema, which lists every object/property per visual type.
# Usage: python3 -I check_props.py <themeSchema.json> <theme.json> <report_definition_dir>
import json, sys, glob, os
d = json.load(open(sys.argv[1])); defs = d["definitions"]
def resolve(o):
    while isinstance(o, dict) and "$ref" in o:
        o = defs[o["$ref"].split("/")[-1]]
    return o
def catalog(vt):
    v = d["properties"]["visualStyles"]["properties"].get(vt)
    if v is None: return None
    star = resolve(resolve(v)["properties"]["*"])
    objs = {}
    for part in star.get("allOf", [star]):
        for k, val in resolve(part).get("properties", {}).items():
            item = resolve(resolve(val).get("items", {}))
            props = set()
            for p in item.get("allOf", [item]):
                props |= set(resolve(p).get("properties", {}))
            objs[k] = props
    return objs
bad = 0
def check(where, vt, objects):
    global bad
    cat = catalog(vt)
    if cat is None:
        print(f"UNKNOWN VISUAL TYPE {vt} ({where})"); bad += 1; return
    for obj, entries in objects.items():
        if obj not in cat:
            print(f"BAD OBJECT {vt}.{obj} ({where})"); bad += 1; continue
        for e in entries:
            props = e.get("properties", e) if isinstance(e, dict) else {}
            for p in props:
                if p not in cat[obj] and not (obj == "general" and p == "altText"):  # altText: per-visual only, confirmed by visualContainer schema
                    print(f"BAD PROPERTY {vt}.{obj}.{p} ({where})"); bad += 1
theme = json.load(open(sys.argv[2]))
for vt, styles in theme["visualStyles"].items():
    if vt == "*":
        # '*' applies to all visuals; check against a common visual (lineChart) for shared objects
        for obj, entries in styles["*"].items():
            hits = [t for t in ("lineChart", "clusteredBarChart", "card") if obj in (catalog(t) or {})]
            if not hits: print(f"BAD OBJECT *.{obj}"); bad += 1
            else: check("theme *", hits[0], {obj: entries})
    else:
        check("theme", vt, styles["*"])
n = 0
for f in glob.glob(os.path.join(sys.argv[3], "pages", "*", "visuals", "*", "visual.json")):
    v = json.load(open(f))["visual"]; n += 1
    check(os.path.basename(os.path.dirname(f)), v["visualType"], v.get("objects", {}))
    check(os.path.basename(os.path.dirname(f)), v["visualType"], v.get("visualContainerObjects", {}))
for f in glob.glob(os.path.join(sys.argv[3], "pages", "*", "page.json")):
    check("page " + os.path.basename(os.path.dirname(f)), "page", json.load(open(f)).get("objects", {}))
print(f"checked theme + {n} visuals: {bad} problems")
sys.exit(1 if bad else 0)
