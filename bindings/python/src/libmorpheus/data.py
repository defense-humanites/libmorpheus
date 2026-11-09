# SPDX-License-Identifier: AGPL-3.0-or-later
"""``python -m libmorpheus.data``: the ``libmorpheus-data`` command."""

from ._cli import data_main as main

if __name__ == "__main__":
    raise SystemExit(main())
