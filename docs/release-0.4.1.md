<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Release decision: 0.4.1

Status: benchmark accepted; platform qualification pending.

- Project version: **0.4.1**
- C ABI: **2**
- SONAME major: **1**
- Previous release tag: `v0.4.0`
- Benchmark evidence: **accepted**

## Scope and compatibility

This corrective native release removes the fixed 25-analysis storage limit.
Analysis storage grows on demand, and the legacy `cruncher` print buffer scales
with the result count. Allocation failures retain their memory-error status.
The Linux CI on the source candidate passed the public analysis fixture and
40-analysis storage and printing regressions under its normal, optimized and
sanitized builds. A separate regression against the pinned Alpheios stemlib
checks the reported counts of 26 and 39 for `a)nalow` and `a(napinw` when
that stemlib is available. The release CI must pass this additional test.

The public C headers, function signatures, record layout and exported symbol
set are unchanged from 0.4.0. C ABI 2 and SONAME 1 therefore remain correct.
The existing Deno, Node.js and Python bindings retain their independent
versions and native 0.3.2 acquisition pins. Publishing this native release
does not update those packages or the Bailly API automatically.

The release archives contain the runtime, headers, metadata and `cruncher`,
without stem data. The corpus-specific redistribution decision remains
separate from this native release.

## Benchmark evidence

The schema 2 report from source revision
`64e09a95c56db782b32c3fdff80c9e972192620b` uses the pinned Alpheios
stemlib revision `4632415fe93c85e9fdca47a0c5a13f31385f0023` on Apple
Silicon with Apple Clang 21 and Deno 2.9.7. Its SHA-256 is
`58b9f7e7d4a20833ab53b177914bbef98a7a8362a026458907713c4dfb750afa`.
The corpus and generation-index digests match the published 0.4.0 report.
All thirteen workloads have unchanged result counts, and their embedded
comparisons reproduce against that report.

Relative to 0.4.0, analysis FFI throughput rises by 2.0 %, 1.7 % and 2.5 %
at one, two and four contexts. Persistent `cruncher` changes by −0.5 % and
cold `cruncher` by +5.0 %. Generation workloads range from −1.6 % to +16.0 %;
the largest increase is small warm generation at four contexts. Peak process
RSS rises at most 1.6 % in workloads reporting it and falls by approximately
10 % in the final maximal and cold workloads. These are whole-process
measurements and the observed variations are accepted; they do not isolate
the allocation cost of a single high-ambiguity form.

The measurement precedes only version metadata, release documentation and
evidence integration, plus a Git-less source-package policy-test correction.
That test still checks policy values and license evidence inside Docker; Git
tree provenance remains checked in the source CI checkout. Any further native
or stemlib-production change needs a fresh benchmark before tagging.

## Remaining gates

1. Require complete Linux CI on the benchmark-finalized commit.
2. Run `Platform and release qualification` with package artifacts enabled on
   that exact commit and inspect all three data-free native archives and
   checksums.
3. Tag the qualified commit as `v0.4.1` after the gates pass, then verify the
   tag workflows and published native assets.
