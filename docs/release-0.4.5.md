<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# libmorpheus 0.4.5

This native release changes Latin results in one respect and fixes the
WebAssembly build's Latin results outright (issue #37). The stem-type tables
of the pinned datasets name two stem classes the runtime did not know: the
Perseids Latin table's fourth-principal-part class `pp_su` (the runtime knew
`pp_p4`) and `nounstem` for `pers_pron` in the Greek and Latin tables.
`GetStemClass()` reports an unknown class as all ones; stored in a `long`,
that value is positive on LP64, so `AddMorphKey()` accepted the key with a
stem type that has every bit set, while on `wasm32` it is `-1` and the key
was refused, dropping every stem of the class. The runtime now knows both
names and refuses a stem-type table that names an unknown class, with a
diagnostic and an internal error, on every platform alike.

Measured against 0.4.4 over 3,000 Greek headwords and 1,517 Latin headwords
with participles, Node.js binding and WebAssembly module alike: Greek is
unchanged on both platforms; the WebAssembly module regains the Latin
analyses it dropped (108 of 1,517 words, `amatus` had none) and now equals
the native library in lemma, stem and ending on every Latin word; native
Latin results change on 12 words, for readings whose lemma is a deponent or
semi-deponent verb of the stemlib (`cavillor`, `vador`, `audeo`, and the
deponent doublets Perseids records next to active verbs, such as `juror`,
`toleror`, `lupor`), whose perfect participles are now reported as deponent
instead of passive; readings of active lemmas are unchanged. The stemlib
production tools share the class table: the Latin tables they regenerate
carry `PP_SU|01` where the historical ones carry the all-ones value, pinned
as a reviewed semantic exception since the runtime analyzes identically
over both; the checked-in generation preparer is rebuilt.

The release also carries the data acquisition package `@libmorpheus/data`
(its own track, 0.1.0 published on 2026-11-05) and the Node.js binding's
dependency on it (Node.js 0.1.2, same day), which touch no native source.

The public C API and ABI are unchanged from 0.4.1 through 0.4.4. The native
archives contain no stemlib data. The Deno, Node.js and Python bindings keep
declaring the native releases they were qualified against; none of them
needs a release for this version, though the deponent change reaches them
once they acquire 0.4.5.

## Release record

- Project version: **0.4.5**
- C ABI: **2**
- SONAME major: **1**
- Previous release tag: `v0.4.4`
- Benchmark evidence: pending (maintainer's schema 2 report from the
  controlled Apple Silicon host, on the candidate commit)
- Pre-release Linux CI: pending (the tagged commit's run)
- Pre-release platform qualification: pending (manual dispatch with
  `package_artifacts` on the exact candidate commit)

## Expected benchmark outcome

The benchmark is Greek-only, and Greek results are unchanged: all result
counts must equal those of the accepted 0.4.4 report. The change adds two
entries to a class table scanned at key resolution and a comparison at table
load; no measurable effect is expected on warm or cold paths beyond
run-to-run variation.

Reviewer's check: the module built from the candidate and one built from
`v0.4.4` agree over 3,000 Greek headwords; the native suite passed, also
under AddressSanitizer, UBSan and ThreadSanitizer on `main`, and the
complete stemlib production qualification passed with the two reviewed
semantic exceptions.

## Remaining authorization

Before publication, a maintainer must:

1. run `bench/release.sh` on the candidate commit on the controlled host,
   have the report reviewed against the accepted 0.4.4 report and committed
   with its sidecar as `bench/release-evidence/benchmark-0.4.5.json`;
2. dispatch the platform workflow with `package_artifacts` for the candidate
   commit and inspect the three native archives;
3. confirm the final tagged Linux CI and platform runs and record their links
   above;
4. explicitly authorize creation of `v0.4.5`, then of `wasm-v0.1.3` on the
   same commit or a descendant with an unchanged runtime.
