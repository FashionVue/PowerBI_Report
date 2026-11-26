#!/usr/bin/env bash
# Rebuilds one project's model + report and runs every check.
# Usage: tools/pbip-builder/build.sh <project> [--data]      project = salessample | vehicles (folder under projects/)
#   --data  also regenerates the workbook with the project's data/ generator
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO="$(cd "$HERE/../.." && pwd)"; C="$HERE/.cache"
PROJ="${1:?usage: build.sh <project> [--data]}"; P="$HERE/projects/$PROJ"; source "$P/project.conf"
W="$C/build-$PROJ"; mkdir -p "$W"
DEF="$REPO/$NAME.SemanticModel/definition"; RPT="$REPO/$NAME.Report"; mkdir -p "$DEF"
export NODE_PATH="${NODE_PATH:-$(npm root -g)}"
[[ "${2:-}" == "--data" ]] && python3 "$REPO/data/$DATA_SCRIPT" "$REPO/data/$XLSX"
echo "== model ($NAME)"; python3 "$P/build_model.py" "$DEF"
TM="$HERE/tmdlcheck/bin/Release/net8.0/tmdlcheck.dll"
rm -rf "$W/tmdl" && dotnet "$TM" "$DEF" "$W/tmdl" > "$W/model_dump.txt"
cp "$W/tmdl"/*.tmdl "$DEF/" && cp "$W/tmdl/tables"/*.tmdl "$DEF/tables/"     # adopt the canonical TMDL form
rm -rf "$W/tmdl2" && dotnet "$TM" "$DEF" "$W/tmdl2" > /dev/null && diff -r "$DEF" "$W/tmdl2" && echo "TMDL round-trip identical"
python3 "$HERE/extract_m.py" "$DEF" > "$W/m.json" && node "$HERE/mparse/check.js" "$W/m.json"
echo "== report"; python3 "$P/build_report.py" "$REPO" "$W"
python3 -I "$HERE/check_layout.py" "$W/layout.json"
node "$P/render.js" "$W/layout.json" "$C/lucide/package/icons" "$W/render" "$C/previews"
python3 "$P/build_report.py" "$REPO" "$W" --write
echo "== checks"
python3 -I "$HERE/validate_json.py" "$C/fabric" "$REPO" "$NAME" | grep -v '^VALID'
python3 -I "$HERE/check_props.py" "$C/reportThemeSchema-2.144.json" "$RPT/StaticResources/RegisteredResources/$THEME" "$RPT/definition"
python3 -I -c "import json,sys;from jsonschema import Draft7Validator as V;s=json.load(open(sys.argv[1]));t=json.load(open(sys.argv[2]));e=list(V(s).iter_errors(t));print('theme schema errors',len(e));sys.exit(1 if e else 0)" \
  "$C/reportThemeSchema-2.144.json" "$RPT/StaticResources/RegisteredResources/$THEME"
python3 -I "$HERE/crosscheck.py" "$W/model_dump.txt" "$RPT"
echo "previews: $C/previews"
