<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

`libmorpheus` 0.3.0 for Python 3.11+ — `ctypes` binding; targets native libmorpheus 0.5.0 (C ABI 2). Qualified on Python 3.11, 3.14 and 3.15.

- Generation no longer fails a lemma on one record the engine cannot generate: the record is skipped, and `generate()` and `generate_raw()` return a `Generations` tuple with a `skipped_records` count.
- Generated records carry the degree and flags analysis reports, and surfaces lose the stem hyphen.
- `libmorpheus-data --gener-index` accepts the new generation index (`a2f97677…`), prepared by `@libmorpheus/data` 0.2.0. Generation returns the forms analysis accepts, not a reference paradigm.

Install: `pip install libmorpheus==0.3.0`, then `libmorpheus-setup --dataset perseids`

Assets: the universal wheel, the source distribution and `SHA256SUMS`.

Release decision: [release-python-0.3.0.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/release-python-0.3.0.md)
