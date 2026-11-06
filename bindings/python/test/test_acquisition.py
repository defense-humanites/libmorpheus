# SPDX-License-Identifier: AGPL-3.0-or-later
"""Acquisition commands against synthetic archives served by a fake fetcher."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import tarfile
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from libmorpheus import AcquisitionError, acquire_data, acquire_native, setup_morpheus
from libmorpheus._acquisition import select_files, sha256
from libmorpheus._cli import data_main, native_main, setup_main
from libmorpheus._manifest import (
    DATASETS,
    GENER_INDEX_SHA256,
    MORPHEUS_NATIVE_VERSION,
    Dataset,
    is_runtime_file,
    select_languages,
    select_native_target,
)

HOST = ("linux", "x86_64", "glibc")
ASSET = f"libmorpheus-{MORPHEUS_NATIVE_VERSION}-Linux-x86_64-glibc.tar.gz"
ROOT = f"libmorpheus-{MORPHEUS_NATIVE_VERSION}-Linux-x86_64-glibc/"
NATIVE_URL = f"https://github.com/defense-humanites/libmorpheus/releases/download/v{MORPHEUS_NATIVE_VERSION}/{ASSET}"
REDIRECT_HOST = "https://release-assets.githubusercontent.com/github-production-release-asset/"


def tar_bytes(entries: list[tuple[str, bytes | None, str | None]]) -> bytes:
    """Build a tar archive from (path, content, link) tuples: content for a
    regular file, link for a symbolic link, neither for a directory."""
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:") as tar:
        for path, content, link in entries:
            info = tarfile.TarInfo(path)
            if content is not None:
                info.type = tarfile.REGTYPE
                info.size = len(content)
                info.mode = 0o644
                tar.addfile(info, io.BytesIO(content))
            elif link is not None:
                info.type = tarfile.SYMTYPE
                info.linkname = link
                tar.addfile(info)
            else:
                info.type = tarfile.DIRTYPE
                info.mode = 0o755
                tar.addfile(info)
    return stream.getvalue()


def native_archive() -> bytes:
    return tar_bytes([
        (ROOT, None, None),
        (f"{ROOT}lib/", None, None),
        (f"{ROOT}lib/libmorpheus.so.{MORPHEUS_NATIVE_VERSION}", b"native fixture", None),
        (f"{ROOT}lib/libmorpheus.so.1", None, f"libmorpheus.so.{MORPHEUS_NATIVE_VERSION}"),
        (f"{ROOT}lib/libmorpheus.so", None, "libmorpheus.so.1"),
        (f"{ROOT}include/morpheus/morpheus.h", b"/* header */", None),
    ])


class Response:
    def __init__(self, status: int, body: bytes = b"", headers: dict[str, str] | None = None) -> None:
        self.status = status
        self.headers = headers or {}
        self._body = body

    def read_limited(self, limit: int, description: str) -> bytes:
        if len(self._body) > limit:
            raise AcquisitionError(f"{description} exceeds size limit")
        return self._body


class Fetcher:
    """Serves a table of URLs and records every request."""

    def __init__(self, table: dict[str, Response]) -> None:
        self.table = table
        self.requests: list[str] = []

    def __call__(self, url: str) -> Response:
        self.requests.append(url)
        try:
            return self.table[url]
        except KeyError:
            return Response(404)


def native_fetcher(compressed: bytes, sidecar: bytes, redirect: bool = False) -> Fetcher:
    if redirect:
        target = f"{REDIRECT_HOST}{ASSET}"
        return Fetcher({
            NATIVE_URL: Response(302, headers={"Location": target}),
            target: Response(200, compressed),
            f"{NATIVE_URL}.sha256": Response(200, sidecar),
        })
    return Fetcher({NATIVE_URL: Response(200, compressed), f"{NATIVE_URL}.sha256": Response(200, sidecar)})


def sidecar_for(compressed: bytes) -> bytes:
    return f"{hashlib.sha256(compressed).hexdigest()}  {ASSET}\n".encode()


class TemporaryDirectoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory(prefix="libmorpheus-python-acquisition-")
        self.parent = Path(self._directory.name)
        self.addCleanup(self._directory.cleanup)


class NativeAcquisitionTest(TemporaryDirectoryTest):
    def test_verifies_extracts_materializes_links_and_records_provenance(self) -> None:
        compressed = gzip.compress(native_archive())
        fetch = native_fetcher(compressed, sidecar_for(compressed), redirect=True)
        output = self.parent / "runtime"
        receipt = acquire_native(output, fetch=fetch, host=HOST)
        self.assertEqual(receipt["archiveSha256"], hashlib.sha256(compressed).hexdigest())
        self.assertEqual(receipt["nativeVersion"], MORPHEUS_NATIVE_VERSION)
        self.assertEqual(receipt["abiVersion"], 2)
        self.assertEqual(receipt["target"], "linux-x86_64-glibc")
        self.assertEqual(receipt["libraryPath"], "lib/libmorpheus.so")
        self.assertEqual((output / "lib/libmorpheus.so").read_bytes(), b"native fixture")
        self.assertEqual((output / "lib/libmorpheus.so.1").read_bytes(), b"native fixture")
        self.assertFalse((output / "lib/libmorpheus.so").is_symlink())
        self.assertEqual(json.loads((output / "MORPHEUS-NATIVE.json").read_text()), receipt)
        self.assertEqual(fetch.requests[0], NATIVE_URL)
        self.assertTrue(fetch.requests[1].startswith(REDIRECT_HOST))

    def test_rolls_back_a_checksum_mismatch(self) -> None:
        compressed = gzip.compress(native_archive())
        fetch = native_fetcher(compressed, f"{'0' * 64}  {ASSET}\n".encode())
        output = self.parent / "runtime"
        with self.assertRaisesRegex(AcquisitionError, "checksum mismatch"):
            acquire_native(output, fetch=fetch, host=HOST)
        self.assertFalse(output.exists())

    def test_refuses_an_unsafe_redirect_and_an_existing_output(self) -> None:
        compressed = gzip.compress(native_archive())
        fetch = Fetcher({
            NATIVE_URL: Response(302, headers={"Location": "https://example.com/evil.tar.gz"}),
            f"{NATIVE_URL}.sha256": Response(200, sidecar_for(compressed)),
        })
        with self.assertRaisesRegex(AcquisitionError, "unsafe redirect"):
            acquire_native(self.parent / "runtime", fetch=fetch, host=HOST)
        existing = self.parent / "existing"
        existing.mkdir()
        with self.assertRaisesRegex(AcquisitionError, "already exists"):
            acquire_native(existing, fetch=fetch, host=HOST)
        self.assertTrue(existing.exists())

    def test_refuses_escaping_links_and_a_missing_library(self) -> None:
        escaping = tar_bytes([(f"{ROOT}lib/libmorpheus.so", None, "../../etc/passwd")])
        compressed = gzip.compress(escaping)
        with self.assertRaisesRegex(AcquisitionError, "escapes output"):
            acquire_native(self.parent / "a", fetch=native_fetcher(compressed, sidecar_for(compressed)), host=HOST)
        missing = tar_bytes([(f"{ROOT}include/morpheus/morpheus.h", b"/* header */", None)])
        compressed = gzip.compress(missing)
        with self.assertRaisesRegex(AcquisitionError, "missing lib/libmorpheus.so"):
            acquire_native(self.parent / "b", fetch=native_fetcher(compressed, sidecar_for(compressed)), host=HOST)
        self.assertFalse((self.parent / "a").exists())
        self.assertFalse((self.parent / "b").exists())

    def test_target_selection(self) -> None:
        self.assertEqual(select_native_target("darwin", "arm64", None).name, "macos-arm64")
        self.assertEqual(select_native_target("linux", "aarch64", "glibc").name, "linux-aarch64-glibc")
        with self.assertRaisesRegex(ValueError, "requires glibc"):
            select_native_target("linux", "x86_64", None)
        with self.assertRaisesRegex(ValueError, "unsupported native platform"):
            select_native_target("win32", "x86_64", None)


def synthetic_dataset(files: dict[str, bytes], license_text: bytes, name: str = "synthetic") -> tuple[Dataset, bytes]:
    revision = "f" * 40
    root = f"morpheus-{revision}/"
    lines = sorted((f"{sha256(content)}  {path}" for path, content in files.items()), key=lambda line: line[66:])
    definition = Dataset(
        name=name,
        repository=f"https://github.com/example/{name}",
        revision=revision,
        archive_url=f"https://codeload.github.com/example/{name}/tar.gz/{revision}",
        archive_root=root,
        data_prefix="stemlib/",
        file_count=len(files),
        tree_sha256=sha256(("\n".join(lines) + "\n").encode()),
        license_path="LICENSE",
        license_sha256=sha256(license_text),
        languages=("grc", "lat"),
        generation=True,
    )
    entries: list[tuple[str, bytes | None, str | None]] = [(root, None, None), (f"{root}LICENSE", license_text, None)]
    entries.extend((f"{root}stemlib/{path}", content, None) for path, content in files.items())
    entries.append((f"{root}README.md", b"ignored", None))
    return definition, gzip.compress(tar_bytes(entries))


DATA_FILES = {
    "Greek/rule_files/ending": b"ending",
    "Greek/steminds/nomind": b"nomind",
    "Greek/steminds/nomind.lindex": b"lindex",
    "Greek/endtables/out/os_ou.out": b"table",
    "Greek/derivs/indices/derivind": b"deriv",
    "Greek/stemsrc/nom01": b"source",
    "Latin/rule_files/ending": b"latin ending",
    "Latin/stemsrc/vbs.cmp.ml": b"compounds",
    "Latin/stemsrc/ls.nom": b"lexicon",
}


class DataAcquisitionTest(TemporaryDirectoryTest):
    def setUp(self) -> None:
        super().setUp()
        self.definition, self.compressed = synthetic_dataset(DATA_FILES, b"MIT-like license\n")
        self.datasets = {"synthetic": self.definition, "perseids": DATASETS["perseids"]}
        self.fetch = Fetcher({self.definition.archive_url: Response(200, self.compressed)})

    def test_verifies_and_writes_the_full_tree_with_receipt_and_license(self) -> None:
        output = self.parent / "data"
        receipt = acquire_data("synthetic", output, fetch=self.fetch, datasets=self.datasets)
        self.assertEqual(receipt["files"], {"count": len(DATA_FILES), "treeSha256": self.definition.tree_sha256})
        self.assertEqual(receipt["subset"]["name"], "full")
        self.assertEqual(receipt["subset"]["count"], len(DATA_FILES))
        self.assertEqual(receipt["languages"], ["grc", "lat"])
        self.assertFalse(receipt["generation"]["available"])
        self.assertIsNone(receipt["manifest"])
        self.assertEqual((output / "Latin/stemsrc/ls.nom").read_bytes(), b"lexicon")
        self.assertEqual((output / "UPSTREAM-LICENSE").read_bytes(), b"MIT-like license\n")
        self.assertFalse((output / "README.md").exists())
        self.assertEqual(json.loads((output / "MORPHEUS-DATA.json").read_text()), receipt)

    def test_runtime_subset_languages_and_manifest(self) -> None:
        output = self.parent / "runtime"
        receipt = acquire_data(
            "synthetic", output, subset="runtime", languages=["lat"], manifest=True,
            fetch=self.fetch, datasets=self.datasets,
        )
        written = sorted(str(path.relative_to(output)) for path in output.rglob("*") if path.is_file())
        self.assertEqual(written, [
            "Latin/rule_files/ending", "Latin/stemsrc/vbs.cmp.ml",
            "MORPHEUS-DATA.json", "UPSTREAM-LICENSE", "stemlib-manifest.json",
        ])
        self.assertEqual(receipt["languages"], ["lat"])
        self.assertEqual(receipt["subset"]["count"], 2)
        manifest = json.loads((output / "stemlib-manifest.json").read_text())
        self.assertEqual(manifest["schema"], 1)
        self.assertEqual([entry["path"] for entry in manifest["files"]], ["Latin/rule_files/ending", "Latin/stemsrc/vbs.cmp.ml"])
        self.assertEqual(manifest["files"][1]["sha256"], sha256(b"compounds"))

    def test_rejects_a_tampered_tree_and_rolls_back(self) -> None:
        tampered, _ = synthetic_dataset({**DATA_FILES, "Greek/rule_files/ending": b"changed"}, b"MIT-like license\n")
        _, compressed = synthetic_dataset({**DATA_FILES, "Greek/rule_files/ending": b"changed"}, b"MIT-like license\n")
        fetch = Fetcher({self.definition.archive_url: Response(200, compressed)})
        output = self.parent / "data"
        with self.assertRaisesRegex(AcquisitionError, "digest mismatch"):
            acquire_data("synthetic", output, fetch=fetch, datasets=self.datasets)
        self.assertFalse(output.exists())
        self.assertNotEqual(tampered.tree_sha256, self.definition.tree_sha256)

    def test_installs_a_verified_generation_index_only(self) -> None:
        index = self.parent / "gener.index"
        index.write_bytes(b"not the pinned index")
        with self.assertRaisesRegex(AcquisitionError, "differs from the pinned"):
            acquire_data("synthetic", self.parent / "a", gener_index=index, fetch=self.fetch, datasets=self.datasets)
        self.assertFalse((self.parent / "a").exists())
        with self.assertRaisesRegex(ValueError, "requires Greek"):
            acquire_data(
                "synthetic", self.parent / "b", languages=["lat"], gener_index=index,
                fetch=self.fetch, datasets=self.datasets,
            )
        self.assertEqual(len(GENER_INDEX_SHA256), 64)

    def test_language_validation_and_subset_selection(self) -> None:
        self.assertEqual(select_languages(None, ("grc", "lat")), ("grc", "lat"))
        self.assertEqual(select_languages(["lat", "grc", "lat"], ("grc", "lat")), ("grc", "lat"))
        with self.assertRaisesRegex(ValueError, "not in this dataset"):
            select_languages(["lat"], ("grc",))
        with self.assertRaisesRegex(ValueError, "unknown language"):
            select_languages(["xyz"], ("grc",))
        self.assertTrue(is_runtime_file("Greek/steminds/vbind.lindex", ["grc"]))
        self.assertTrue(is_runtime_file("gener.index", []))
        self.assertFalse(is_runtime_file("Greek/stemsrc/nom01", ["grc"]))
        self.assertFalse(is_runtime_file("Latin/rule_files/ending", ["grc"]))
        self.assertEqual(
            list(select_files(DATA_FILES, "runtime", ("grc",))),
            ["Greek/rule_files/ending", "Greek/steminds/nomind", "Greek/steminds/nomind.lindex",
             "Greek/endtables/out/os_ou.out", "Greek/derivs/indices/derivind"],
        )
        with self.assertRaisesRegex(ValueError, "unsupported subset"):
            select_files(DATA_FILES, "half", ("grc",))

    def test_pinned_datasets_are_the_audited_revisions(self) -> None:
        self.assertEqual(DATASETS["alpheios"].revision, "4632415fe93c85e9fdca47a0c5a13f31385f0023")
        self.assertEqual(DATASETS["perseids"].revision, "ab6898ffed335fc6169fa02c9940657a9b5a78e0")
        self.assertTrue(DATASETS["alpheios"].generation)
        self.assertEqual(DATASETS["perseids"].languages, ("grc", "lat"))


class SetupTest(TemporaryDirectoryTest):
    def test_refuses_overlapping_outputs(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-overlapping"):
            setup_morpheus("perseids", native_output=self.parent / "x", data_output=self.parent / "x" / "data")
        with self.assertRaisesRegex(ValueError, "only with the Alpheios"):
            setup_morpheus("perseids", native_output=self.parent / "a", data_output=self.parent / "b", gener_index="i")

    def test_rolls_back_the_native_installation_when_data_fails(self) -> None:
        compressed = gzip.compress(native_archive())
        fetch = native_fetcher(compressed, sidecar_for(compressed))
        native_output = self.parent / "native"
        data_output = self.parent / "data"
        with self.assertRaisesRegex(AcquisitionError, "download failed: HTTP 404"):
            setup_morpheus("perseids", native_output=native_output, data_output=data_output, fetch=fetch, host=HOST)
        self.assertFalse(native_output.exists())
        self.assertFalse(data_output.exists())


class CommandLineTest(TemporaryDirectoryTest):
    def test_commands_require_their_options(self) -> None:
        for main, arguments in ((native_main, []), (data_main, ["--output", "x"]), (setup_main, [])):
            with self.assertRaises(SystemExit) as raised:
                main(arguments)
            self.assertEqual(raised.exception.code, 2)
        with self.assertRaises(SystemExit):
            data_main(["--dataset", "perseids", "--output", "x", "--languages", "xyz"])

    def test_commands_report_acquisition_failures_on_stderr(self) -> None:
        existing = self.parent / "existing"
        existing.mkdir()
        with open(os.devnull, "w") as sink, unittest.mock.patch("sys.stderr", sink):
            self.assertEqual(native_main(["--output", str(existing)]), 1)
            self.assertEqual(data_main(["--dataset", "perseids", "--output", str(existing)]), 1)


if __name__ == "__main__":
    unittest.main()
