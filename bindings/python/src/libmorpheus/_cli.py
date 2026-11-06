# SPDX-License-Identifier: AGPL-3.0-or-later
"""Command lines of the acquisition commands (``libmorpheus-native``,
``libmorpheus-data``, ``libmorpheus-setup``)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from ._acquisition import AcquisitionError, acquire_data, acquire_native, setup_morpheus
from ._manifest import DATASETS, LANGUAGE_DIRECTORIES


def _languages(value: str) -> list[str]:
    codes = [code.strip() for code in value.split(",") if code.strip()]
    if not codes:
        raise argparse.ArgumentTypeError("at least one language is required")
    for code in codes:
        if code not in LANGUAGE_DIRECTORIES:
            raise argparse.ArgumentTypeError(f"unknown language: {code}")
    return codes


def _run(parser: argparse.ArgumentParser, action, argv: Sequence[str] | None) -> int:
    arguments = parser.parse_args(argv)
    try:
        message = action(arguments)
    except (AcquisitionError, ValueError, OSError) as error:
        print(f"{parser.prog}: {error}", file=sys.stderr)
        return 1
    print(message)
    return 0


def native_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="libmorpheus-native",
        description="Download, verify and extract the libmorpheus native runtime "
        "this package declares. The destination must not exist.",
    )
    parser.add_argument("--output", required=True, help="directory to create")

    def action(arguments: argparse.Namespace) -> str:
        receipt = acquire_native(arguments.output)
        return f"Installed {receipt['target']} native runtime {receipt['nativeVersion']} in {arguments.output}."

    return _run(parser, action, argv)


def data_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="libmorpheus-data",
        description="Download a pinned upstream Morpheus stem dataset, verify its tree "
        "and license, and write it into a new directory with a provenance receipt "
        "(MORPHEUS-DATA.json). Alpheios provides Greek analysis and experimental "
        "generation; Perseids provides Greek and Latin analysis.",
    )
    parser.add_argument("--dataset", required=True, choices=sorted(DATASETS))
    parser.add_argument("--output", required=True, help="directory to create")
    parser.add_argument(
        "--subset", choices=("full", "runtime"), default="full",
        help="runtime: write only the files the libmorpheus runtime reads",
    )
    parser.add_argument(
        "--languages", type=_languages, default=None, metavar="grc,lat",
        help="keep only these ISO 639-3 languages (default: all)",
    )
    parser.add_argument("--manifest", action="store_true", help="also write stemlib-manifest.json (paths, sizes, SHA-256)")
    parser.add_argument(
        "--gener-index", metavar="PATH", default=None,
        help="install this prepared experimental Greek generation index after verifying "
        "its digest (prepare it with @libmorpheus/data --with-gener or a source checkout)",
    )

    def action(arguments: argparse.Namespace) -> str:
        receipt = acquire_data(
            arguments.dataset,
            arguments.output,
            subset=arguments.subset,
            languages=arguments.languages,
            manifest=arguments.manifest,
            gener_index=arguments.gener_index,
        )
        files = receipt["subset"]["count"]
        return f"Installed {receipt['dataset']} dataset ({files} files, {arguments.subset}) in {arguments.output}."

    return _run(parser, action, argv)


def setup_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="libmorpheus-setup",
        description="Acquire the native runtime and one dataset into two new directories.",
    )
    parser.add_argument("--dataset", required=True, choices=sorted(DATASETS))
    parser.add_argument("--native-output", default="./morpheus-native", help="directory to create (default: ./morpheus-native)")
    parser.add_argument("--data-output", default="./morpheus-data", help="directory to create (default: ./morpheus-data)")
    parser.add_argument("--gener-index", metavar="PATH", default=None, help="install this prepared generation index (Alpheios only)")

    def action(arguments: argparse.Namespace) -> str:
        result = setup_morpheus(
            arguments.dataset,
            native_output=arguments.native_output,
            data_output=arguments.data_output,
            gener_index=arguments.gener_index,
        )
        return (
            f"Installed native runtime in {result['nativeOutput']} "
            f"({result['nativeLibraryPath']}) and {arguments.dataset} dataset in {result['dataOutput']}."
        )

    return _run(parser, action, argv)
