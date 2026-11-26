#!/usr/bin/env bash
# Rebuilds the SalesSample model + report and runs every check. Usage: tools/pbip-builder/build.sh [--data]
#   --data  also regenerates data/SalesSample.xlsx with data/make_sample.py
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO="$(cd "$HERE/../.." && pwd)"; C="$HERE/.cache"; W="$C/build"; mkdir -p "$W"
DEF="$REPO/SalesSample.SemanticModel/definition"; RPT="$REPO/SalesSample.Report"
export NODE_PATH="${NODE_PATH:-$(npm root -g)}"
[[ "${1:-}" == "--data" ]] && python3 "$REPO/data/make_sample.py" "$REPO/data/SalesSample.xlsx"
echo "== model";  python3 "$HERE/build_model.py" "$DEF"
rm -rf "$W/tmdl" && dotnet "$HERE/tmdlcheck/bin/Release/net8.0/tmdlcheck.dll" "$DEF" "$W/tmdl" > "$W/model_dump.txt"
cp "$W/tmdl"/*.tmdl "$DEF/" && cp "$W/tmdl/tables"/*.tmdl "$DEF/tables/"     # adopt the canonical TMDL form
dotnet "$HERE/tmdlcheck/bin/Release/net8.0/tmdlcheck.dll" "$DEF" > /dev/null && echo "TMDL loads"
python3 "$HERE/extract_m.py" "$DEF" > "$W/m.json" && node "$HERE/mparse/check.js" "$W/m.json"
echo "== report"; python3 "$HERE/build_report.py" "$REPO" "$W"
python3 -I "$HERE/check_layout.py" "$W/layout.json"
node "$HERE/render_backgrounds.js" "$W/layout.json" "$C/lucide/package/icons" "$W/render" "$C/previews"
python3 "$HERE/build_report.py" "$REPO" "$W" --write
echo "== checks"
python3 -I "$HERE/validate_json.py" "$C/fabric" "$REPO" | grep -v '^VALID'
python3 -I "$HERE/check_props.py" "$C/reportThemeSchema-2.144.json" "$RPT/StaticResources/RegisteredResources/FashionVueExecutive.json" "$RPT/definition"
python3 -I -c "import json,sys;from jsonschema import Draft7Validator as V;s=json.load(open(sys.argv[1]));t=json.load(open(sys.argv[2]));e=list(V(s).iter_errors(t));print('theme schema errors',len(e));sys.exit(1 if e else 0)" \
  "$C/reportThemeSchema-2.144.json" "$RPT/StaticResources/RegisteredResources/FashionVueExecutive.json"
python3 -I "$HERE/crosscheck.py" "$W/model_dump.txt" "$RPT"
echo "previews: $C/previews"
