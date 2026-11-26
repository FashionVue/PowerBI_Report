#!/usr/bin/env bash
# One-time setup: downloads reference schemas, icons and validator dependencies into tools/pbip-builder/.cache (git-ignored).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; C="$HERE/.cache"; mkdir -p "$C"
# 1) Fabric PBIR/PBIP JSON schemas (mirror of developer.microsoft.com/json-schemas/fabric from github.com/microsoft/json-schemas)
python3 -I "$HERE/fetch_schemas.py" "$C/fabric" \
  pbip/pbipProperties/1.0.0/schema.json item/semanticModel/definitionProperties/1.0.0/schema.json \
  item/report/definitionProperties/2.0.0/schema.json item/report/definition/report/2.0.0/schema.json \
  item/report/definition/page/2.0.0/schema.json item/report/definition/pagesMetadata/1.0.0/schema.json \
  item/report/definition/versionMetadata/1.0.0/schema.json item/report/definition/visualContainer/2.1.0/schema.json \
  gitIntegration/platformProperties/2.0.0/schema.json
# 2) Official report theme schema (lists every formatting object/property per visual type)
curl -fsS -o "$C/reportThemeSchema-2.144.json" \
  "https://raw.githubusercontent.com/microsoft/powerbi-desktop-samples/main/Report%20Theme%20JSON%20Schema/reportThemeSchema-2.144.json"
# 3) Lucide icons (ISC licence)
mkdir -p "$C/lucide" && curl -fsS -o "$C/lucide/pkg.tgz" https://registry.npmjs.org/lucide-static/-/lucide-static-1.80.0.tgz && tar xzf "$C/lucide/pkg.tgz" -C "$C/lucide"
# 4) Microsoft Power Query parser for M syntax checks
(cd "$HERE/mparse" && npm install --silent --no-save @microsoft/powerquery-parser@6.0.0)
# 5) TMDL checker (Microsoft.AnalysisServices TmdlSerializer); needs the .NET 8 SDK
(cd "$HERE/tmdlcheck" && dotnet build -c Release -nologo -v q)
# Python: pip install jsonschema openpyxl ; Node: playwright with Chromium (npx playwright install chromium)
echo "setup done"
