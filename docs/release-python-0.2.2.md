<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Python binding 0.2.2 release decision

Version 0.2.2 of the Python binding supersedes 0.2.1 for performance only:
normalized records are built faster, and generation no longer slows down
when threads are added. Results and API are unchanged. This document
records the intended contract; it does not authorize or record creation of
the `python-v0.2.2` tag.

## Why a new version

Two costs of the binding itself, found by profiling and confirmed on the
controlled host:

- **Normalization** (pull request #72). `analyze()` and `generate()`
  recomputed every name tuple for every record, the morph flags by testing
  each of the 84 known flags. The tuples are now cached per code and shared;
  tuples in frozen dataclasses being immutable, nothing changes for callers.
  `generate("i(/hmi")` (2,918 forms) went from 173 to about 36 ms on a Linux
  test host.
- **The GIL** (pull request #75). Each record cost result-accessor calls
  through `ctypes.CDLL`, which releases and reacquires the GIL around every
  call; with several threads those thousands of reacquisitions per paradigm
  queued on the GIL, and generation got slower with each thread. The
  accessors (count, copy, truncation mask, free) are now bound through
  `ctypes.PyDLL`, which keeps the GIL for these short memory operations,
  while analysis and generation still release it. Named records are decoded
  directly from the copied bytes through one reused buffer.

Measured on the controlled host (Python 3.14.10, native 0.4.6), maximal
warm generation:

| Contexts (threads) | 1 | 2 | 4 |
| --- | --- | --- | --- |
| With #72, before #75 ([`benchmark-0.4.6-bindings-1.json`](../bench/release-evidence/benchmark-0.4.6-bindings-1.json), `fdfd576`) | 68 | 69 | 42 |
| 0.2.2 ([`benchmark-0.4.6-bindings-2.json`](../bench/release-evidence/benchmark-0.4.6-bindings-2.json), `53c6db9`) | 102 | 136 | 136 |

operations per second; small warm generation 61, 59 and 59 µs instead of 89,
110 and 184 µs. Analysis is bound by the runtime: 214, 131 and 91 µs per
word at one, two and four contexts, against 226 µs for `cruncher` in the
same run, and on a par with the Node.js binding (239, 142 and 94 µs). The
remaining ceiling near 136 maximal paradigms per second is the construction
of Python objects under the GIL; further work there is deferred until a real
need appears. Named and raw results hash identically to 0.2.1's over 7,870
analysis records and 68,534 generation records.

The binding still declares native **0.4.6** (C ABI 2) and keeps its
acquisition pins.

## Distribution, behavioral and licensing contracts

Unchanged from [0.2.1](release-python-0.2.1.md).

## Qualification and publication

As for 0.2.1: tagged Linux CI on the exact commit, then
`python-release.yml` verifies that `v0.4.6` is published, publishes through
PyPI trusted publishing, creates the `python-v0.2.2` GitHub release from
`docs/release-notes/python-v0.2.2.md` and the distributions PyPI serves,
and the published PyPI smoke test runs.

## Publication record

- Tag: `python-v0.2.2`, created by the maintainer on 2026-11-10 on
  `875268ee423a27c4507cfc5bb436c7913a268efa`, the merge of this decision,
  together with `node-v0.2.0`.
- Tagged Linux CI: [passed](https://github.com/defense-humanites/libmorpheus/actions/runs/42811403597).
- Publication workflow: [passed at the first attempt](https://github.com/defense-humanites/libmorpheus/actions/runs/42811403333);
  `libmorpheus` 0.2.2 is on PyPI; the wheel
  `libmorpheus-0.2.2-py3-none-any.whl` has SHA-256
  `7b10e71ae683357773b33f8ea76ff9de04c27cc3fb4d579671374e1cea847642` and
  the source distribution
  `f3e5f330a733ed9322a6e629cfa79823a32413a98dfd9b514dc9a8b664a5bdc4`.
- GitHub release: [`python-v0.2.2`](https://github.com/defense-humanites/libmorpheus/releases/tag/python-v0.2.2),
  with the two distributions PyPI serves and `SHA256SUMS`.
- Published PyPI smoke test: [passed](https://github.com/defense-humanites/libmorpheus/actions/runs/42812316406):
  the public wheel repeated the analysis and generation checks against a
  runtime built from the tagged sources, and its published
  `libmorpheus-setup` acquired the declared runtime 0.4.6 and the Perseids
  data from the public endpoints.
