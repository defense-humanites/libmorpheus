<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Release decision: 0.4.0

Status: benchmark refresh and platform qualification pending.

- Project version: **0.4.0**
- C ABI: **2**
- SONAME major: **1**
- Previous release tag: `v0.3.2`
- Benchmark evidence: **accepted**

## Version and ABI rationale

Version 0.4.0 adds a qualified, opt-in production path for the Greek and Latin
stem libraries and records the independently published JavaScript and Python
binding tracks. This is a new project capability rather than a corrective
0.3.x release, even though the production tools remain internal and are not
installed.

The public C declarations and symbol set remain identical to 0.3.2. No public
function, signature, constant, or `morpheus_analysis` or
`morpheus_generation` layout changes, so C ABI 2 and SONAME 1 remain correct.
The generation API remains experimental within that compatibility contract.

## Candidate scope

- Restore the ending, derivation, nominal and verbal stemlib producers as
  explicit internal C17 targets with fail-closed command and output handling.
- Reconstruct complete Greek and Latin table and lexical distributions from a
  checksum-pinned 379-source manifest in fresh language-scoped staging trees.
- Require two clean builds per language to produce byte-identical receipts and
  outputs, with every reviewed Perseids and Alpheios baseline difference
  recorded explicitly.
- Expose the complete process through the non-installed, default-disabled
  `morpheus_stemlib_production` target and retain its deterministic provenance
  and qualification report as CI evidence.
- Keep the separately released Deno 0.4.0, Node.js 0.1.1 and Python 0.1.0
  bindings pinned to native 0.3.2 and C ABI 2. This native release does not
  silently republish or retarget those packages.

## Stem data and licensing boundary

The native release archives contain the runtime, public headers, metadata and
`cruncher`; they contain neither stem data nor a generated `gener.index`.
Stemlib production is source-tree qualification infrastructure, not an
installed compiler and not an authorization to redistribute the reconstructed
datasets. Container images embedding the pinned Alpheios data remain
qualification artifacts only.

The restored Morpheus producers and inherited engine remain MPL-2.0. New
orchestration, manifests, tests, receipts, binding code and documentation
remain AGPL-3.0-or-later. The existing notices and file-level SPDX boundaries
remain authoritative; this release makes no relicensing claim.

## Reproducibility evidence

The reference stemlib qualification uses the pinned Ubuntu 24.04 x86-64
profile with GCC 14, Python 3.12 and Perl 5.38. It requires the complete public
runtime suite, two clean Greek and Latin reconstructions, 229 reviewed binary
table exceptions, twelve reviewed lexical differences, and the complete
selected Alpheios comparison to agree with their manifests and receipts. The
machine-readable report also parses the CTest JUnit result and rejects missing,
failed, skipped or duplicate required tests.

This evidence qualifies the production graph and its declared baselines. It
does not make the historical in-memory `.out` serialization portable, promote
quarantined utilities, or turn checked-in and external stemlibs into native
release assets.

## Benchmark evidence

The earlier accepted schema 2 report was produced on Apple Silicon from
`3048fdad64b30f5ba35423bacb5197f5a347e228` with Deno 2.9.6, Apple Clang 21,
the pinned Alpheios revision and the canonical generation-index digest. Its
SHA-256 is
`1ad54b590a1a30be3ffb9c79d52f4c58944d12edcb1d92c527d0fb845a4e3793`.
The validator accepts all thirteen required configurations and identities; the
embedded comparison reproduces exactly from the accepted 0.3.2 report. The
compiler remains Apple Clang 21 but advances from build 2100.1.1.101 to
2100.3.34.2, which is retained verbatim in the report identity.

Compared with 0.3.2, analysis FFI throughput changes by -3.5%, +2.1% and
-2.7% across one, two and four contexts. Persistent `cruncher` is unchanged;
cold `cruncher` is 6.4% slower. Small warm generation changes by -5.9%, +2.9%
and -3.8%, while maximal warm generation changes by +0.1%, +1.8% and -0.9%.
Both cold generation workloads remain within 1.1% of the baseline. These
timing variations are accepted as normal measurement noise for unchanged
native analysis and generation paths.

Peak process RSS is 0.7% to 12.3% higher. Most per-workload RSS growth is
stable or lower; maximal generation with four contexts touches approximately
31 MiB more and raises the cumulative high-water mark inherited by the two
following cold measurements. Returned records, corpus, generation index and
runtime paths are unchanged, and the report measures the whole Deno process
rather than isolated native allocations. The increase is recorded and
accepted as allocator and high-water-mark variability rather than evidence of
a functional regression.

The subsequent dynamic analysis-storage correction on `main` invalidates that
measurement for the release candidate. Linux CI passed on
[`186fbc5`](https://github.com/defense-humanites/libmorpheus/actions/runs/36385002610),
including the 40-analysis storage and printing regressions. A new benchmark
from the final source revision and pinned Alpheios stemlib is required before
the historical performance comparison can be accepted again. The
evidence-finalization commit should change only benchmark evidence, release
decision, changelog and qualification metadata; any later native or
stemlib-production change requires another report.

## Remaining gates

1. Run `bench/release.sh` from the source candidate on a controlled host with
   the pinned Alpheios submodule, `cmake`, `ctest` and Deno. Validate and
   review the new report against the accepted 0.3.2 baseline, then update
   `bench/release-evidence/benchmark-0.4.0.json` and its SHA-256 record.
2. Require the complete Linux CI, including stemlib reconstruction,
   sanitizers, signedness builds, bindings, fixtures and release metadata, to
   pass on the benchmark-finalized commit.
3. Manually dispatch `Platform and release qualification` for the exact
   benchmark-finalized commit with package artifacts enabled; inspect all
   three data-free native archives and checksums.
4. Tag that qualified commit as `v0.4.0` only after explicit authorization.
   Require the tag workflows to rebuild and publish the native assets and
   accepted benchmark evidence.
