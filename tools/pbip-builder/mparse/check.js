// Parse each M expression extracted from the TMDL files with Microsoft's powerquery-parser.
const PQP = require("@microsoft/powerquery-parser");
const fs = require("fs");
const exprs = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
(async () => {
  let fail = 0;
  for (const [name, text] of Object.entries(exprs)) {
    const res = await PQP.TaskUtils.tryLexParse(PQP.DefaultSettings, text);
    if (PQP.TaskUtils.isParseStageOk(res)) console.log("M OK    ", name);
    else { fail++; console.log("M FAIL  ", name, JSON.stringify(res.error && res.error.message || res.error).slice(0, 400)); }
  }
  // negative control
  const bad = await PQP.TaskUtils.tryLexParse(PQP.DefaultSettings, "let a = 1, in a");
  console.log("negative control detected:", !PQP.TaskUtils.isParseStageOk(bad));
  process.exit(fail ? 1 : 0);
})();
