# SPDX-License-Identifier: AGPL-3.0-or-later
"""``python -m libmorpheus.setup``: the ``libmorpheus-setup`` command."""

from ._cli import setup_main as main

if __name__ == "__main__":
    raise SystemExit(main())
