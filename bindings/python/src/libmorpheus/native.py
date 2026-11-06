# SPDX-License-Identifier: AGPL-3.0-or-later
"""``python -m libmorpheus.native``: the ``libmorpheus-native`` command."""

from ._cli import native_main as main

if __name__ == "__main__":
    raise SystemExit(main())
