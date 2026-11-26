# Validate every JSON file of the PBIP project against its $schema, resolved from a local mirror
# of https://developer.microsoft.com/json-schemas/fabric/ (downloaded from microsoft/json-schemas).
# Usage: python3 -I validate_json.py <schema_mirror_root> <repo_root>
import json, os, sys, glob
from jsonschema import validators
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

MIRROR, ROOT = sys.argv[1], sys.argv[2]
PREFIX = "https://developer.microsoft.com/json-schemas/fabric/"


def retrieve(uri):
    if not uri.startswith(PREFIX):
        raise LookupError(uri)
    path = os.path.join(MIRROR, uri[len(PREFIX):])
    with open(path, encoding="utf-8") as f:
        return Resource.from_contents(json.load(f), default_specification=DRAFT7)


registry = Registry(retrieve=retrieve)
PREFIX_NAME = sys.argv[3] if len(sys.argv) > 3 else "SalesSample"
files = [p for p in glob.glob(os.path.join(ROOT, PREFIX_NAME + "*"), recursive=False)]
targets = []
for base in files:
    if os.path.isfile(base):
        targets.append(base)
    else:
        for dp, dn, fn in os.walk(base):
            for n in fn:
                if n.endswith((".json", ".pbir", ".pbism", ".pbip")) or n == ".platform":
                    targets.append(os.path.join(dp, n))
fails = 0
for t in sorted(targets):
    raw = open(t, "rb").read()
    assert not raw.startswith(b"\xef\xbb\xbf"), f"BOM in {t}"
    doc = json.loads(raw.decode("utf-8"))
    rel = os.path.relpath(t, ROOT)
    sch = doc.get("$schema") if isinstance(doc, dict) else None
    if not sch:
        print(f"NO-SCHEMA  {rel} (parsed OK)")
        continue
    schema = retrieve(sch).contents
    cls = validators.validator_for(schema)
    v = cls(schema, registry=registry)
    errs = sorted(v.iter_errors(doc), key=lambda e: list(e.absolute_path))
    if errs:
        fails += 1
        print(f"FAIL       {rel}")
        for e in errs[:10]:
            print("    ", list(e.absolute_path), e.message[:300])
    else:
        print(f"VALID      {rel}  <- {sch[len(PREFIX):]}")
print("failures:", fails)
sys.exit(1 if fails else 0)
