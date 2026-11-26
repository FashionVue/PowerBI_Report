# Recursively mirror Fabric JSON schemas from microsoft/json-schemas (raw GitHub) into a local tree.
import json, os, re, sys, urllib.request, posixpath
RAW = "https://raw.githubusercontent.com/microsoft/json-schemas/main/fabric/"
out = sys.argv[1]
todo = list(sys.argv[2:])
seen = set()
while todo:
    rel = posixpath.normpath(todo.pop())
    if rel in seen: continue
    seen.add(rel)
    dest = os.path.join(out, rel)
    if not os.path.exists(dest):
        try:
            data = urllib.request.urlopen(RAW + rel, timeout=30).read()
        except Exception as e:
            print("FAIL", rel, e); continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(data)
        print("got", rel)
    doc = json.load(open(dest, encoding="utf-8"))
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "$ref" and isinstance(v, str) and not v.startswith("#"):
                    p = v.split("#")[0]
                    if p.startswith("http"):
                        p = p.replace("https://developer.microsoft.com/json-schemas/fabric/", "")
                    else:
                        p = posixpath.join(posixpath.dirname(rel), p)
                    todo.append(p)
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(doc)
