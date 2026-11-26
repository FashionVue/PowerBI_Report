# List formatting objects/properties for a visual type from the official report theme schema.
# Usage: python3 -I themeprops.py <schema.json> <visualType> [object]
import json, sys
d = json.load(open(sys.argv[1]))
defs = d["definitions"]
def resolve(o):
    while isinstance(o, dict) and "$ref" in o:
        o = defs[o["$ref"].split("/")[-1]]
    return o
vt = sys.argv[2]
v = resolve(d["properties"]["visualStyles"]["properties"].get(vt) or defs.get("visual-" + vt))
star = resolve(v["properties"]["*"])
objs = {}
for part in star.get("allOf", [star]):
    part = resolve(part)
    for k, val in part.get("properties", {}).items():
        objs[k] = val
want = sys.argv[3:] 
for k, val in objs.items():
    if want and k not in want: continue
    item = resolve(resolve(val).get("items", {}))
    props = {}
    for p in item.get("allOf", [item]):
        p = resolve(p)
        props.update(p.get("properties", {}))
    desc = []
    for pk, pv in props.items():
        pv = resolve(pv)
        en = [x.get("const") for x in pv.get("oneOf", []) if isinstance(x, dict) and "const" in x]
        desc.append(pk + (("=" + "|".join(map(str, en))) if en else ""))
    print(f"{k}: {', '.join(desc) if want else ', '.join(list(props)[:40])}")
