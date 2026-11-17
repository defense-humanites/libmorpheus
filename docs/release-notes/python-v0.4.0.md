<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

`libmorpheus` 0.4.0 for Python 3.11+ — `ctypes` binding; targets native libmorpheus 0.6.0 (C ABI 2). Qualified on Python 3.11, 3.14 and 3.15.

- `generate()` accepts the compound verbs analysis reports and returns their preverb variants; `GenerationOptions(exclude_preverb_variants=True)` leaves the variants out.
- It also returns the unaugmented indicatives, movable ν and accented clitics analysis reads, with the dialects all of a form's parts allow. The default limit becomes 65,536 records.
- `libmorpheus-data --gener-index` accepts the index that `@libmorpheus/data` 0.3.0 prepares (`8ba328ca…`), which compound verbs need.

Install: `pip install libmorpheus==0.4.0`, then `libmorpheus-setup --dataset perseids`

Assets: the universal wheel, the source distribution and `SHA256SUMS`.

Release decision: [release-python-0.4.0.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/release-python-0.4.0.md)
