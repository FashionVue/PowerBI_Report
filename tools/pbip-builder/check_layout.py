# Checks layout.json: no two visuals overlap, every visual (except nav buttons) sits inside a drawn panel, tile or header control.
# Usage: python3 check_layout.py <layout.json>
import json, sys
L = json.load(open(sys.argv[1])); bad = 0
for p in L["pages"]:
    vs = p["visuals"]; boxes = p["panels"] + p["tiles"] + p.get("controls", []) + [b for b in (p.get("extra") or {}).values() if isinstance(b, dict) and "w" in b]
    for i, a in enumerate(vs):
        for b in vs[i + 1:]:
            if a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"] and a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"]:
                print("OVERLAP", p["key"], p.get("mode"), a["label"], "|", b["label"]); bad += 1
        if a["label"].startswith("Nav"):
            continue
        if not any(a["x"] >= q["x"] and a["y"] >= q["y"] and a["x"] + a["w"] <= q["x"] + q["w"] and a["y"] + a["h"] <= q["y"] + q["h"] for q in boxes):
            print("OUTSIDE PANEL", p["key"], p.get("mode"), a["label"]); bad += 1
print("layout problems", bad); sys.exit(1 if bad else 0)
