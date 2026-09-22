#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Create a deterministic, internal runtime artifact from a production stage."""

import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import tarfile
import tempfile


RECEIPT_NAME = "MORPHEUS-STEMLIB-RUNTIME-RECEIPT.json"
PRODUCTION_RECEIPT_NAME = "MORPHEUS-STEMLIB-PRODUCTION-RECEIPT.json"
REQUIRED_RUNTIME_PATHS = {
    "rule_files/vowcontr.table",
    "rule_files/conseuph.table",
    "rule_files/stemtypes.table",
    "rule_files/derivtypes.table",
    "rule_files/domainlist.table",
    "rule_files/raw_preverbs.table",
    "steminds/nomind",
    "steminds/nomind.lindex",
    "steminds/vbind",
    "steminds/vbind.lindex",
    "endtables/indices/nendind",
    "endtables/indices/vbendind",
    "derivs/indices/derivind",
}


def digest(data):
    if isinstance(data, Path):
        data = data.read_bytes()
    return hashlib.sha256(data).hexdigest()


def safe_relative(value):
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"unsafe receipt path: {value!r}")
    return path


def verified_file(stage, relative, expected):
    relative = safe_relative(relative)
    path = stage
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError(f"runtime member traverses a symbolic link: {relative}")
    if not path.is_file():
        raise ValueError(f"runtime member is not a regular file: {relative}")
    received = digest(path)
    if received != expected:
        raise ValueError(f"runtime member digest changed: {relative}")
    return path


def add_bytes(archive, name, data, mode=0o644):
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mode = mode
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    archive.addfile(info, io.BytesIO(data))


def selected_members(stage, production, language):
    prefix = language + "/"
    selected = {}

    for item in production["inputs"]["table"]:
        relative = safe_relative(item["path"])
        if item.get("kind") == "rule":
            archive_path = PurePosixPath(language) / relative
            selected[archive_path.as_posix()] = (
                verified_file(stage, archive_path.as_posix(), item["sha256"]),
                item["sha256"],
                "rule-input",
            )

    for item in production["inputs"]["lexical"]:
        if item.get("role") == "runtime":
            relative = safe_relative(item["path"])
            archive_path = PurePosixPath(language) / relative
            selected[archive_path.as_posix()] = (
                verified_file(stage, archive_path.as_posix(), item["sha256"]),
                item["sha256"],
                "runtime-input",
            )

    for group in ("table", "lexical"):
        for item in production["outputs"][group]:
            relative = safe_relative(item["path"])
            value = relative.as_posix()
            if not value.startswith(prefix):
                raise ValueError(f"output is outside the language directory: {value}")
            runtime_path = value[len(prefix):]
            include = (
                runtime_path.startswith("endtables/out/")
                or runtime_path.startswith("endtables/indices/")
                or runtime_path.startswith("derivs/out/")
                or runtime_path.startswith("derivs/indices/")
                or runtime_path.startswith("derivs/ascii/")
                or runtime_path.startswith("steminds/")
                or runtime_path in ("stemsrc/nom.irreg", "stemsrc/vbs.irreg")
            )
            if include:
                selected[value] = (
                    verified_file(stage, value, item["sha256"]),
                    item["sha256"],
                    f"{group}-output",
                )

    runtime_paths = {name[len(prefix):] for name in selected if name.startswith(prefix)}
    required = set(REQUIRED_RUNTIME_PATHS)
    required.add("stemsrc/vbs.cmp.ml")
    if language == "Greek":
        required.add("rule_files/ppasslist.table")
        required.add("stemsrc/lemlist")
    missing = sorted(required - runtime_paths)
    if missing:
        raise ValueError("production receipt lacks required runtime members: " + ", ".join(missing))
    return selected


def package(args):
    stage = args.stage.resolve()
    output = args.output.resolve()
    receipt_output = Path(str(output) + ".receipt.json")
    checksum_output = Path(str(output) + ".sha256")
    for path in (output, receipt_output, checksum_output):
        if path.exists():
            raise ValueError(f"refusing to replace existing output: {path}")
    if not stage.is_dir():
        raise ValueError(f"production stage is missing: {stage}")

    production_path = stage / PRODUCTION_RECEIPT_NAME
    production_bytes = production_path.read_bytes()
    production = json.loads(production_bytes)
    if production.get("schema") != 2 or production.get("language") != args.language:
        raise ValueError("invalid production receipt schema or language")
    members = selected_members(stage, production, args.language)

    root = f"morpheus-stemlib-{args.language.lower()}"
    payload = [
        {"path": name, "sha256": sha256, "source": source}
        for name, (_, sha256, source) in sorted(members.items())
    ]
    receipt = {
        "schema": 1,
        "artifact": "internal-runtime-qualification",
        "language": args.language,
        "runtime_root": root,
        "redistribution": "not-qualified",
        "production_receipt_sha256": digest(production_bytes),
        "payload": payload,
    }
    receipt_bytes = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(prefix=".stemlib-runtime-", dir=output.parent)
        os.close(descriptor)
        temporary = Path(temporary_name)
        with temporary.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                    archive_members = {
                        f"{root}/{RECEIPT_NAME}": receipt_bytes,
                        f"{root}/{PRODUCTION_RECEIPT_NAME}": production_bytes,
                    }
                    archive_members.update(
                        (f"{root}/{name}", path.read_bytes())
                        for name, (path, _, _) in members.items()
                    )
                    for name, data in sorted(archive_members.items()):
                        add_bytes(archive, name, data)
        archive_hash = digest(temporary)
        temporary.chmod(0o644)
        receipt_output.write_bytes(receipt_bytes)
        checksum_output.write_text(f"{archive_hash}  {output.name}\n")
        temporary.replace(output)
    except Exception:
        receipt_output.unlink(missing_ok=True)
        checksum_output.unlink(missing_ok=True)
        if temporary:
            temporary.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--language", choices=("Greek", "Latin"), required=True)
    args = parser.parse_args()
    try:
        package(args)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        parser.exit(1, f"stemlib runtime artifact: {error}\n")


if __name__ == "__main__":
    main()
