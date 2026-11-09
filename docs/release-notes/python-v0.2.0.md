<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

`libmorpheus` 0.2.0 for Python 3.11+ — `ctypes` binding; targets native libmorpheus 0.4.5 (C ABI 2).

- Acquires the native runtime and the stem data like the Node.js binding: `libmorpheus-native`, `libmorpheus-data` and `libmorpheus-setup`, standard library only.
- Experimental generation takes a prepared `gener.index` through `--gener-index`, verified against the pinned digest.

Install: `pip install libmorpheus==0.2.0`, then `libmorpheus-setup --dataset perseids`

Assets: the universal wheel, the source distribution and `SHA256SUMS`.

Release decision: [release-python-0.2.0.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/release-python-0.2.0.md)
