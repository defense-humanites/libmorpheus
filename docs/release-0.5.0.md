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
- Benchmark evidence: **accepted**
- Pre-release Linux CI: [passed on `667ca57`](https://github.com/defense-humanites/libmorpheus/actions/runs/43068651909)
- Pre-release platform qualification: [passed on `667ca57`](https://github.com/defense-humanites/libmorpheus/actions/runs/43068760334)
  (manual dispatch with `package_artifacts`, first attempt)
- Tagged platform run and release publication: [passed on `667ca57`](https://github.com/defense-humanites/libmorpheus/actions/runs/43070003936)
  (second attempt)
- Release: [`v0.5.0`](https://github.com/defense-humanites/libmorpheus/releases/tag/v0.5.0),
  created on 2026-11-11 on `667ca578fb514fe099fcc522a0f47167bf3805a9`

## Benchmark evidence

The schema 3 report from source revision
`fa7f0a6ad7adae09e17cefa46df0119d1d080399` (the merge of the release
preparation) uses the pinned Alpheios stemlib revision
`4632415fe93c85e9fdca47a0c5a13f31385f0023` on the controlled Apple Silicon
host, with the toolchain of the baseline (Apple Clang 21 build 2100.4.1.1,
Node.js 26.13.0, libuv thread pool of four) and the tree's Node.js binding,
0.2.0. It is retained as
[`benchmark-0.5.0.json`](../bench/release-evidence/benchmark-0.5.0.json);
its SHA-256 is
`0319d6a02e9fe549a2368da7e501dc2c348ee499c3af97aeddce5d005cc9611d`. The
release validator passes with the recorded source revision and compiler,
and the comparison with
[`benchmark-0.4.6.json`](../bench/release-evidence/benchmark-0.4.6.json)
has `complete` scope. All thirteen result counts equal the baseline's.

| Row | 0.4.6 (µs) | 0.5.0 (µs) | Change |
| --- | --- | --- | --- |
| `node`, 1 context | 215 | 213 | −0.7 % |
| `node`, 2 contexts | 132 | 131 | −0.7 % |
| `node`, 4 contexts | 87 | 86 | −1.4 % |
| `cruncher-persistent` | 202 | 211 | +4.4 % |
| `cruncher-cold` | 2,743 | 2,700 | −1.6 % |
| maximal generation, warm, 1 / 2 / 4 contexts | 5,729 / 3,598 / 3,751 | 3,659 / 1,755 / 1,113 | −36.1 / −51.2 / −70.3 % |
| small generation, warm, 1 / 2 / 4 contexts | 120 / 27 / 31 | 35 / 21 / 14 | −71.1 / −22.9 / −55.0 % |
| maximal / small generation, cold | 21,077 / 14,820 | 19,036 / 14,708 | −9.7 / −0.8 % |

Analysis is within noise. `cruncher-persistent` is 4.4 % slower than in the
baseline but within the 202–227 µs that the retained reports since 0.4.6
measured for the same runtime analysis; analysis code did not change.

The generation gains are not this release's. The baseline was measured
through Node.js binding 0.1.3. The tree's binding decodes named results
directly since pull request #71, published in Node.js 0.2.0, and the gains
come from that decoding. The reports that measured that binding on native
0.4.6 isolate the runtime. Against
[`benchmark-0.4.6-bindings-2.json`](../bench/release-evidence/benchmark-0.4.6-bindings-2.json),
maximal warm generation moves by +0.1, −1.7 and +3.7 %, small warm
generation by −13.1, +39.3 and +14.8 % (12 to 40 µs per operation), and
cold generation by −5.7 and −10.8 %. Against
[`benchmark-0.4.6-node-decoding.json`](../bench/release-evidence/benchmark-0.4.6-node-decoding.json),
which measured maximal warm generation 3,170 µs at one context where
`bindings-2` measured 3,656 µs, it moves by +15.4, +9.5 and +9.6 %. The
spread between those two reports of the same code bounds the noise. The
sandbox comparison above, without the binding, found native 0.5.0
generation 6 % faster than 0.4.6's. No claim is made for generation in
either direction.

Peak RSS falls on every row (−9.8 to −56.4 %), from the binding's decoding
for the generation rows. The RSS growth of the four-context analysis row
(3.4 MiB against 0.6 MiB) moves as the order of allocations within one
process does. This report replaces `benchmark-0.4.6.json` as the baseline
of the next native release.

## Publication record

The tag was created by the maintainer on 2026-11-11 on `667ca57`, the merge
of the accepted benchmark evidence, a descendant of the measured revision
`fa7f0a6` that differs from it only by that evidence and these documents.

The Linux CI of the merge commit on `main` passed at its first attempt,
including the push-only sanitizer, ThreadSanitizer, byte-conversion,
legacy-make and release jobs, and so did the manual `package_artifacts`
dispatch, which produced the three archives.

On the tag, Linux CI and WebAssembly passed at their first attempt. The
platform run's first `apple-silicon` job waited fifteen minutes without a
macOS runner and was cancelled before any step ran, as during the 0.4.4 and
0.4.6 dispatches; the other qualification jobs had passed. The second
attempt qualified Apple Silicon and published the release. The tag never
moved.

The release carries the three native archives and their digests, plus the
accepted benchmark report and its sidecar:

| Asset | SHA-256 |
|---|---|
| `libmorpheus-0.5.0-Linux-x86_64-glibc.tar.gz` | `8df4440d92630114444324fd2000c76ddb0065db647fb75953e58aef7af131eb` |
| `libmorpheus-0.5.0-Linux-aarch64-glibc.tar.gz` | `73d83e743204e06327750c4cef15ecf758e30b7c006d6f81d2d7b93317a92766` |
| `libmorpheus-0.5.0-macOS-arm64.tar.gz` | `3d8e46407ceff23972d84e01d0edf4e914a27580b45cbdfc98479894af1e8682` |
| `benchmark-0.5.0.json` | `0319d6a02e9fe549a2368da7e501dc2c348ee499c3af97aeddce5d005cc9611d` |

After publication, the Linux x86-64 archive was downloaded, checked against
its sidecar and exercised through the Python binding of the tree: it exports
`morpheus_generation_result_skipped_records`, and δίδωμι generates 3,636
records (2,544 distinct surfaces) over the index of `@libmorpheus/data` 0.2.0
with one record skipped.

WebAssembly binding 0.2.0 and data package 0.2.0 were tagged on the same
commit afterwards; see [`release-wasm-0.2.0.md`](release-wasm-0.2.0.md) and
[`release-data-0.2.0.md`](release-data-0.2.0.md).
