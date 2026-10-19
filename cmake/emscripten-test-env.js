// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Pre-JS for the Emscripten builds of the native test programs. Emscripten
// does not expose the host environment to getenv() by default; the historical
// runtime and several tests locate the stemlib through MORPHLIB, so copy the
// process environment into the module before main() runs.
if (typeof process !== "undefined" && process.env) {
  Module["preRun"] = Module["preRun"] || [];
  Module["preRun"].push(function () {
    // ENV is only linked into programs that call getenv().
    if (typeof ENV === "undefined") return;
    for (var name in process.env) {
      if (Object.prototype.hasOwnProperty.call(process.env, name)) {
        ENV[name] = process.env[name];
      }
    }
  });
}
