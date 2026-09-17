<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Release decision: 0.4.0

Status: candidate prepared; benchmark and platform qualification pending.

- Project version: **0.4.0**
- C ABI: **2**
- SONAME major: **1**
- Previous release tag: `v0.3.2`
- Benchmark evidence: **pending**

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

## Benchmark plan

The accepted 0.3.2 schema 2 report is the comparison baseline. A new 0.4.0
report must be produced on the same controlled Apple Silicon host from the
exact finalized candidate commit with the pinned Alpheios revision and
canonical generation index. The result must pass `bench/validate.ts`, retain
all thirteen required analysis and generation configurations, and receive an
explicit regression review before its JSON and SHA-256 sidecar are committed
as accepted evidence.

The evidence-finalization commit may update only the benchmark evidence,
release decision, changelog and qualification metadata. Any subsequent native
or stemlib-production change invalidates the measurement and requires a new
report.

## Remaining gates

1. Require the complete Linux CI, including stemlib reconstruction,
   sanitizers, signedness builds, bindings, fixtures and release metadata, to
   pass on the candidate commit.
2. Produce and review the 0.4.0 benchmark against accepted 0.3.2 evidence;
   update this decision to record its revision, digest and accepted comparison.
3. Manually dispatch `Platform and release qualification` for the exact
   benchmark-finalized commit with package artifacts enabled; inspect all
   three data-free native archives and checksums.
4. Tag that qualified commit as `v0.4.0` only after explicit authorization.
   Require the tag workflows to rebuild and publish the native assets and
   accepted benchmark evidence.
