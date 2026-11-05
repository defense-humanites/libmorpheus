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
- Benchmark evidence: **accepted**
- Pre-release Linux CI: pending (the tagged commit's run)
- Pre-release platform qualification: pending (manual dispatch with
  `package_artifacts` on the exact candidate commit)

## Benchmark evidence

The schema 2 report from native source revision
`5ba9dc037510f51dc8c13440a8d61a76f6d04739` (the merge of the release
preparation) uses the pinned Alpheios stemlib revision
`4632415fe93c85e9fdca47a0c5a13f31385f0023` on the same Apple Silicon host as
the 0.4.4 report, with the same toolchain (Apple Clang 21 build 2100.4.1.1,
Deno 2.9.8), corpus, generation index and workload parameters. Its SHA-256
is `f10dbc854337e440cd3b07e274e81ae7fbafe7386a95b5a8e99739ff566ca590`. The
complete benchmark validator passes with the recorded source revision and
compiler. All thirteen result counts equal those of the accepted 0.4.4
report, as the Greek-only benchmark requires of a change that alters Latin
readings only.

Relative to 0.4.4, analysis FFI mean latency changes by −0.6 %, −5.2 % and
−1.0 % at one, two and four contexts; persistent `cruncher` by −1.4 % and
cold `cruncher` by +1.4 %. Maximal generation changes by +0.2 %, +1.5 % and
−1.6 % warm and −0.2 % cold; small generation by −7.0 %, −6.1 % and −3.8 %
warm and +0.0 % cold. The two-context FFI figure returns to 421 µs after
the 444 µs of the 0.4.4 report, within the oscillation recorded for that
measurement since 0.4.0 (−1.7 %, +2.5 %, −3.3 %, +5.5 %); the small warm
generation aggregates (2 to 3.5 ms in total) are too short to carry
meaning. Neither direction nor magnitude points at the change: the two
entries added to the stem-class table are scanned when a stem-type table is
loaded, before any timed operation, and the comparison added at that point
runs once per class name.

Peak RSS is lower by 1 to 3 % in the first ten measurements and by 11.5 %
in the last three, because the four-context maximal generation grew the
process by 9.4 MiB during its measurement against 39 MiB in the 0.4.4
report. The 0.4.4 decision attributed that growth to the Deno runtime
version; the present report, taken under the same Deno 2.9.8, shows the
figure to be bimodal from one run to the next rather than tied to a
version (the accepted reports hold 8–9 MiB or 39–47 MiB, both under 2.9.6
and now both under 2.9.8). The measurement decodes 233,440 results per
iteration into JavaScript objects, and whether V8 collects them within the
measurement window varies between runs; the native library allocates
nothing in that path that this release changes. The first-context FFI
start-up, 2.7 s against 1.6 s, is the one-time module load and symbol
binding, which the accepted reports place anywhere between 1.1 s and 6.0 s.

Reviewer's check: the module built from the candidate and one built from
`v0.4.4` agree over 3,000 Greek headwords; the native suite passed, also
under AddressSanitizer, UBSan and ThreadSanitizer on `main`, and the
complete stemlib production qualification passed with the two reviewed
semantic exceptions.

## Remaining authorization

Before publication, a maintainer must:

1. dispatch the platform workflow with `package_artifacts` for the candidate
   commit and inspect the three native archives;
2. confirm the final tagged Linux CI and platform runs and record their links
   above;
3. explicitly authorize creation of `v0.4.5`, then of `wasm-v0.1.3` on the
   same commit or a descendant with an unchanged runtime.
