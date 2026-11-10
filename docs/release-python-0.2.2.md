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

## Remaining authorization

Before publication, a maintainer must confirm the tagged Linux CI run on the
candidate commit and explicitly authorize creation of `python-v0.2.2`.
