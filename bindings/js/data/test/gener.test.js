// SPDX-License-Identifier: AGPL-3.0-or-later

import assert from "node:assert/strict";
import process from "node:process";
import test from "node:test";

import createGenerPreparer from "../internal/gener-preparer.mjs";

async function prepare(source) {
  const module = await createGenerPreparer({
    noInitialRun: true,
    print: () => undefined,
    printErr: () => undefined,
  });
  module.FS.writeFile("/input.txt", source);
  const previousExitCode = process.exitCode;
  let status;
  try {
    status = module.callMain(["/output.txt", "/input.txt"]);
  } finally {
    process.exitCode = previousExitCode;
  }
  let output = null;
  try {
    output = module.FS.readFile("/output.txt", { encoding: "utf8" });
  } catch {
    // Failed preparation must not leave partial output.
  }
  return { status, output };
}

test("WebAssembly generation preparer preserves continuations", async () => {
  const input = `:le:a)gakleh/s
:aj:a)ga klehs_kleous,suff_acc late
@ end:kle/a acc sg masc fem epic
@ ionic
:def:ignored metadata
@ end:kle/as acc pl masc fem epic

:le:dupe
:wd:du/pe indecl
@

:le:verb
:vs:lu_ s_aor act
@ mid epic
`;
  const expected = `:le:a)gakleh/s
:aj:a)ga klehs_kleous,suff_acc late
:aj:a)ga klehs_kleous,suff_acc end:kle/a acc sg masc fem epic
:aj:a)ga klehs_kleous,suff_acc ionic
:aj:a)ga klehs_kleous,suff_acc end:kle/as acc pl masc fem epic
:le:dupe
:wd:du/pe indecl
:wd:du/pe indecl
:le:verb
:vs:lu_ s_aor act
:vs:lu_ s_aor mid epic
`;
  const first = await prepare(input);
  const second = await prepare(input);
  assert.equal(first.status, 0);
  assert.equal(second.status, 0);
  assert.equal(first.output, expected);
  assert.equal(second.output, expected);
});

test("WebAssembly generation preparer removes failed output", async () => {
  const result = await prepare(":le:orphan\n-:vs:disabled w_stem\n@ inf act\n");
  assert.notEqual(result.status, 0);
  assert.equal(result.output, null);
});
