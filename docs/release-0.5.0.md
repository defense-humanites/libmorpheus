<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# libmorpheus 0.5.0

This native release changes experimental generation, after its first use in
a real application (issue #78): a lemma no longer fails because of one record
the engine cannot generate, and generated records report what analysis
reports. It adds one function to C ABI 2. Analysis results are unchanged. It
is the release WebAssembly binding 0.2.0 is compiled from and declares
([release-wasm-0.2.0.md](release-wasm-0.2.0.md)).

## Why a new version

Generating the forms of every lemma of the Alpheios index for an application
exposed four defects of the runtime (#78):

- **One bad record failed the whole lemma** (#79). 346 records could not be
  generated, stem classes without an ending table (`as_a`, `gc_ggos`,
  `irreg_decl3`…) or forced endings that match no cell, and each failed its
  lemma with `MORPHEUS_INTERNAL_ERROR`: 275 lemmas, among them δίδωμι,
  ἵστημι, πόλις, γράφω and βασιλεύς. Such records are now skipped and
  counted, and the lemma's other records are generated. The new function
  `morpheus_generation_result_skipped_records()` returns the count; zero
  records with a nonzero count distinguishes a lemma whose records all
  failed from an absent one.
- **Generated records lost the stem's flags** (#80). Generation read only the
  word's morphology flags, while analysis combines those of the word, the
  preverb, the stem and the ending (`checkgenwds.c`). The stem's irregular
  comparative and superlative markers were lost, so ἡδύτερος and ἥδιστος came
  out positive. The normalizer now combines the four as analysis does.
- **Surfaces kept the stem-boundary hyphen** of the stem source
  (`a)nqr-w/pwn`); it is removed.
- **Contexts printed the engine's diagnostics** (`Something wrong with
  stemkeys […]`) on standard error or output. Contexts opened through the
  public API are now silent and report failures by status only; the
  compatibility API, and so `cruncher`, keeps the messages.

A record that failed after its keys were scanned also leaked the buffer
holding its unknown keys; the whole Alpheios index now generates under
AddressSanitizer without leaks.

The version is a minor one: like 0.4.0, the release adds a public
capability, and within 0.x a behavioural change takes the minor version.
Requests that used to fail now succeed, and records change degree and
surface.

## Results and compatibility

Analysis is unchanged: the analyses of 4,177 Greek words (every eighth line
of the Alpheios `lemlist`) hash identically with the `v0.4.6` library and
with this release's.

Generation over the whole Alpheios historical index (106,422 lemmas): no
request fails (275 before); 346 records are skipped in 275 lemmas, 110 of
which keep no record; the other 106,147 lemmas return the same records apart
from the hyphen. 11,964 adjective, 28 adverb and 4 noun records change
degree, and 101,125 lemmas have records that gain flags. On 400 random
lemmas, every generated record that matches an analysis of its surface now
has the same degree (32,192 of 32,192) and 98.1 % the same flags (27.2 %
before). 1,268,920 forms of 11,823 lemmas lose their hyphen.

The C ABI stays **2** and the SONAME **1**: one function is added
(`morpheus_generation_result_skipped_records`), nothing is removed or
changed, and existing callers are unaffected. The generation index format is
unchanged. An index prepared by `@libmorpheus/data` 0.2.0
([release-data-0.2.0.md](release-data-0.2.0.md)) also works with 0.4.6, but
there the 270 lemmas holding one of its 339 unusable records fail; with 0.5.0
they generate their other records.

The native archives contain no stemlib data. The Node.js and Python bindings
keep declaring native 0.4.6 until their next releases, which declare 0.5.0
and expose the skipped count; with the older library they report a count of
zero, which is exact there, since that library fails the request instead.

## Measured effect

On the 2-vCPU Linux sandbox, against a `v0.4.6` library built with the same
compiler and options (Release), on the historical generation index,
alternated twice: maximal warm generation (`i(/hmi`, 2,918 records) takes
5.55–5.59 ms instead of 5.94–5.97 ms, small warm generation (`lo/gos`) 20.7
µs instead of 20.2–21.8 µs, and analysis 380–397 µs per benchmark word
instead of 385–403 µs: unchanged within noise.

## Release record

- Project version: **0.5.0**
- C ABI: **2**
- SONAME major: **1**
- Previous release tag: `v0.4.6`
- Benchmark evidence: pending (maintainer's schema 3 report from the
  controlled Apple Silicon host, on the candidate commit)
- Pre-release Linux CI: pending (the tagged commit's run)
- Pre-release platform qualification: pending (manual dispatch with
  `package_artifacts` on the exact candidate commit)

## Expected benchmark outcome

The release report is compared with
[`benchmark-0.4.6.json`](../bench/release-evidence/benchmark-0.4.6.json),
the accepted 0.4.6 report (`complete` scope):

```sh
sh bench/release.sh benchmark-0.5.0.json \
  bench/release-evidence/benchmark-0.4.6.json
```

All thirteen result counts must equal the baseline's: the benchmark
generates from the historical index (`--historical`), whose benchmark lemmas
have no unusable record, and hyphens or flags change no count. Analysis rows
should stay within noise. Generation rows may move a little in either
direction: each record now combines four flag sets and copies its surface
without hyphens, which the sandbox measurement above does not show as a
cost.

## Remaining authorization

Before publication, a maintainer must:

1. run `bench/release.sh` on the candidate commit on the controlled host,
   have the report reviewed against the baseline and committed with its
   sidecar as `bench/release-evidence/benchmark-0.5.0.json`;
2. dispatch the platform workflow with `package_artifacts` for the candidate
   commit and inspect the three native archives;
3. confirm the final tagged Linux CI and platform runs and record their links
   above;
4. explicitly authorize creation of `v0.5.0`, then of `wasm-v0.2.0` on the
   same commit or a descendant with an unchanged runtime, and of
   `data-v0.2.0`.
