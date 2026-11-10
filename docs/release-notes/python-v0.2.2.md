<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

`libmorpheus` 0.2.2 for Python 3.11+ — `ctypes` binding; targets native libmorpheus 0.4.6 (C ABI 2).

- Faster normalized records: generating a large paradigm takes about a fifth of the time it took in 0.2.1 on a test host.
- Generation no longer slows down with threads: the result accessors keep the GIL instead of contending for it on every record (136 instead of 42 large paradigms per second at four threads on the controlled host).
- Results and API are unchanged.

Install: `pip install libmorpheus==0.2.2`, then `libmorpheus-setup --dataset perseids`

Assets: the universal wheel, the source distribution and `SHA256SUMS`.

Release decision: [release-python-0.2.2.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/release-python-0.2.2.md)
