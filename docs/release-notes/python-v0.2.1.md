<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

`libmorpheus` 0.2.1 for Python 3.11+ — `ctypes` binding; targets native libmorpheus 0.4.6 (C ABI 2).

- Declares native 0.4.6 instead of 0.4.5: analysis about three times faster, results unchanged.
- A context that cannot be opened names its stemlib and language (`opening … for Latin failed: …`) instead of giving the status text alone.

Install: `pip install libmorpheus==0.2.1`, then `libmorpheus-setup --dataset perseids`

Assets: the universal wheel, the source distribution and `SHA256SUMS`.

Release decision: [release-python-0.2.1.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/release-python-0.2.1.md)
