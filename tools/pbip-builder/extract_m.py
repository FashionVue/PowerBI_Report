# Extracts every partition M expression and the DataFolder parameter from the TMDL folder into JSON for mparse/check.js.
# Usage: python3 extract_m.py <SemanticModel/definition> > m.json
import glob, json, os, re, sys
base = sys.argv[1]; out = {}
for f in glob.glob(os.path.join(base, "tables", "*.tmdl")):
    lines = open(f, encoding="utf-8").read().split("\n")
    i = [k for k, l in enumerate(lines) if l == "\t\tsource ="][0] + 1
    body = []
    while i < len(lines) and (lines[i].startswith("\t\t\t\t") or lines[i] == ""):
        body.append(lines[i][4:]); i += 1
    out[os.path.basename(f)] = "\n".join(body).strip()
out["DataFolder"] = re.search(r"expression DataFolder = (.*)", open(os.path.join(base, "expressions.tmdl"), encoding="utf-8").read()).group(1)
print(json.dumps(out))
