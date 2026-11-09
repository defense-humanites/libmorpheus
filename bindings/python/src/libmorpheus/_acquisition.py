# SPDX-License-Identifier: AGPL-3.0-or-later
"""Acquisition of the native runtime and of the stem data.

Standard library only: ``urllib`` for the downloads, ``zlib`` and ``tarfile``
for the archives, ``hashlib`` for the digests. Every download is bounded in
size, verified against a pinned digest or a published sidecar before anything
is used, written into a directory that must not exist beforehand, and rolled
back on failure. The contracts mirror the Node.js binding's commands.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import platform
import posixpath
import shutil
import sys
import tarfile
import urllib.error
import urllib.parse
import urllib.request
import zlib
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from ._manifest import (
    DATA_LICENSE_FILE,
    DATA_MANIFEST_FILE,
    DATA_RECEIPT_FILE,
    DATASETS,
    GENER_INDEX_SHA256,
    MORPHEUS_DATA_SCHEMA_VERSION,
    MORPHEUS_MANIFEST_SCHEMA_VERSION,
    MORPHEUS_NATIVE_ABI_VERSION,
    MORPHEUS_NATIVE_REPOSITORY,
    MORPHEUS_NATIVE_SCHEMA_VERSION,
    MORPHEUS_NATIVE_VERSION,
    NATIVE_RECEIPT_FILE,
    Dataset,
    NativeTarget,
    is_runtime_file,
    select_languages,
    select_native_target,
)
from ._version import MORPHEUS_PYTHON_VERSION

MAX_COMPRESSED_SIZE = 64 * 1024 * 1024
MAX_UNCOMPRESSED_SIZE = 256 * 1024 * 1024
MAX_CHECKSUM_SIZE = 4096
RELEASE_ASSET_HOST = "release-assets.githubusercontent.com"
_CHUNK = 64 * 1024
_PRODUCER = "libmorpheus-python"


class AcquisitionError(RuntimeError):
    """A download, verification or extraction failed; the output was removed."""


class Response(Protocol):
    """What a fetcher returns: the status, the headers and a bounded body."""

    status: int
    headers: Mapping[str, str]

    def read_limited(self, limit: int, description: str) -> bytes: ...


Fetcher = Callable[[str], Response]


class _UrllibResponse:
    def __init__(self, status: int, headers: Mapping[str, str], body: Any) -> None:
        self.status = status
        self.headers = headers
        self._body = body

    def read_limited(self, limit: int, description: str) -> bytes:
        chunks: list[bytes] = []
        size = 0
        with self._body as body:
            while True:
                chunk = body.read(_CHUNK)
                if not chunk:
                    break
                size += len(chunk)
                if size > limit:
                    raise AcquisitionError(f"{description} exceeds size limit")
                chunks.append(chunk)
        return b"".join(chunks)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def default_fetch(url: str) -> Response:
    """Fetch ``url`` over HTTPS without following redirects."""
    if not url.startswith("https://"):
        raise AcquisitionError(f"refusing a non-HTTPS download: {url}")
    request = urllib.request.Request(
        url, headers={"User-Agent": f"{_PRODUCER}/{MORPHEUS_PYTHON_VERSION}"}
    )
    try:
        response = _opener.open(request, timeout=300)
    except urllib.error.HTTPError as error:
        return _UrllibResponse(error.code, error.headers, error)
    except urllib.error.URLError as error:
        raise AcquisitionError(f"download failed: {url}: {error.reason}") from error
    return _UrllibResponse(response.status, response.headers, response)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_ok(response: Response, limit: int, description: str) -> bytes:
    if response.status != 200:
        raise AcquisitionError(f"{description} download failed: HTTP {response.status}")
    return response.read_limited(limit, description)


def _fetch_release_asset(url: str, limit: int, description: str, fetch: Fetcher) -> bytes:
    response = fetch(url)
    if response.status in (301, 302, 303, 307, 308):
        location = response.headers.get("location") or response.headers.get("Location")
        if location is None:
            raise AcquisitionError(f"{description} redirect is missing")
        redirect = urllib.parse.urljoin(url, location)
        parts = urllib.parse.urlsplit(redirect)
        if parts.scheme != "https" or parts.hostname != RELEASE_ASSET_HOST or parts.username or parts.password:
            raise AcquisitionError(f"{description} has unsafe redirect target")
        response = fetch(redirect)
        if response.status in (301, 302, 303, 307, 308):
            raise AcquisitionError(f"{description} redirected twice")
    return _read_ok(response, limit, description)


def _gunzip_limited(compressed: bytes, limit: int, description: str) -> bytes:
    decompressor = zlib.decompressobj(wbits=31)
    chunks: list[bytes] = []
    size = 0
    data = compressed
    while data:
        chunk = decompressor.decompress(data, _CHUNK)
        size += len(chunk)
        if size > limit:
            raise AcquisitionError(f"{description} exceeds size limit once decompressed")
        chunks.append(chunk)
        data = decompressor.unconsumed_tail
    chunks.append(decompressor.flush())
    if not decompressor.eof:
        raise AcquisitionError(f"{description} is a truncated gzip stream")
    return b"".join(chunks)


@dataclass(frozen=True)
class _Entry:
    path: str
    kind: str  # "file", "dir", "symlink"
    content: bytes
    mode: int
    link: str


def _iter_tar(archive: bytes, description: str) -> Iterator[_Entry]:
    try:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
            for member in tar:
                if member.isdir():
                    # tarfile strips the trailing slash that marks a directory.
                    name = member.name if member.name.endswith("/") else f"{member.name}/"
                    yield _Entry(name, "dir", b"", member.mode & 0o777, "")
                elif member.isfile():
                    stream = tar.extractfile(member)
                    content = b"" if stream is None else stream.read()
                    yield _Entry(member.name, "file", content, member.mode & 0o777, "")
                elif member.issym():
                    yield _Entry(member.name, "symlink", b"", member.mode & 0o777, member.linkname)
                else:
                    raise AcquisitionError(f"unsupported {description} entry type: {member.name}")
    except tarfile.TarError as error:
        raise AcquisitionError(f"{description} is not a valid tar archive: {error}") from error


def _safe_relative_path(path: str) -> str:
    if path == "" or path.startswith("/") or "\\" in path or "\0" in path:
        raise AcquisitionError(f"unsafe archive path: {path}")
    components = path.split("/")
    if any(component in ("", ".", "..") for component in components):
        raise AcquisitionError(f"unsafe archive path: {path}")
    return "/".join(components)


def _tree_digest(lines: list[str]) -> str:
    lines.sort(key=lambda line: line[66:])
    return sha256(("\n".join(lines) + "\n").encode("utf-8"))


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    with open(path, "x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def _ensure_absent(output: Path) -> None:
    if output.exists() or output.is_symlink():
        raise AcquisitionError(f"output path already exists: {output}")


def _rollback(output: Path, error: BaseException) -> None:
    try:
        shutil.rmtree(output)
    except OSError as cleanup_error:
        raise AcquisitionError(
            f"acquisition and cleanup both failed for {output}: {error}; {cleanup_error}"
        ) from error


# Native runtime ------------------------------------------------------------


def _checksum_from_sidecar(sidecar: bytes, asset: str) -> str:
    text = sidecar.decode("utf-8", errors="replace").strip()
    fields = text.split()
    if len(fields) != 2 or len(fields[0]) != 64 or fields[1].lstrip("*") != asset:
        raise AcquisitionError("invalid native archive checksum sidecar")
    digest = fields[0].lower()
    if any(character not in "0123456789abcdef" for character in digest):
        raise AcquisitionError("invalid native archive checksum sidecar")
    return digest


def _extract_native_archive(archive: bytes, directory: Path, target: NativeTarget) -> None:
    paths: set[str] = set()
    regular: dict[str, tuple[bytes, int]] = {}
    symlinks: dict[str, str] = {}
    for entry in _iter_tar(archive, "native archive"):
        if not entry.path.startswith(target.archive_root):
            raise AcquisitionError(f"unexpected native archive root: {entry.path}")
        without_root = entry.path[len(target.archive_root):]
        if without_root == "":
            continue
        relative = _safe_relative_path(without_root.rstrip("/"))
        if relative in paths:
            raise AcquisitionError(f"duplicate archive path: {relative}")
        paths.add(relative)
        destination = directory.joinpath(*relative.split("/"))
        if entry.kind == "dir":
            destination.mkdir(parents=True, exist_ok=True)
        elif entry.kind == "file":
            destination.parent.mkdir(parents=True, exist_ok=True)
            with open(destination, "xb") as stream:
                stream.write(entry.content)
            os.chmod(destination, entry.mode)
            regular[relative] = (entry.content, entry.mode)
        else:
            link = entry.link
            if link == "" or link.startswith("/") or "\\" in link or "\0" in link:
                raise AcquisitionError(f"unsafe symbolic link: {relative}")
            normalized = posixpath.normpath(posixpath.join(posixpath.dirname(relative), link))
            if normalized == ".." or normalized.startswith("../"):
                raise AcquisitionError(f"symbolic link escapes output: {relative}")
            symlinks[relative] = normalized
    if target.library_path not in regular and target.library_path not in symlinks:
        raise AcquisitionError(f"native archive is missing {target.library_path}")

    def resolve(path: str, visited: set[str]) -> tuple[bytes, int]:
        if path in regular:
            return regular[path]
        linked = symlinks.get(path)
        if linked is None:
            raise AcquisitionError(f"symbolic link target is absent or not regular: {path}")
        if path in visited:
            raise AcquisitionError(f"symbolic link cycle in native archive: {path}")
        visited.add(path)
        return resolve(linked, visited)

    # Links are materialized as copies, so the installation has no dangling
    # or escaping links whatever the host's view of the archive.
    for path in symlinks:
        content, mode = resolve(path, set())
        destination = directory.joinpath(*path.split("/"))
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, "xb") as stream:
            stream.write(content)
        os.chmod(destination, mode)


def host_platform() -> tuple[str, str, str | None]:
    """``(system, machine, libc)`` of this host in ``platform`` module terms."""
    system = sys.platform
    if system.startswith("linux"):
        system = "linux"
    machine = platform.machine().lower()
    if machine in ("amd64", "x64"):
        machine = "x86_64"
    if machine == "aarch64" and system == "darwin":
        machine = "arm64"
    if machine == "arm64" and system == "linux":
        machine = "aarch64"
    libc = platform.libc_ver()[0] or None
    return system, machine, libc


def acquire_native(
    output: str | os.PathLike[str],
    *,
    fetch: Fetcher | None = None,
    host: tuple[str, str, str | None] | None = None,
) -> dict[str, Any]:
    """Download, verify and extract the declared native release into
    ``output``, which must not exist. Returns the receipt also written as
    ``MORPHEUS-NATIVE.json``."""
    fetch = fetch or default_fetch
    system, machine, libc = host or host_platform()
    target = select_native_target(system, machine, libc)
    destination = Path(output).resolve()
    _ensure_absent(destination)
    destination.mkdir()
    try:
        source_url = f"{MORPHEUS_NATIVE_REPOSITORY}/releases/download/v{MORPHEUS_NATIVE_VERSION}/{target.asset}"
        compressed = _fetch_release_asset(source_url, MAX_COMPRESSED_SIZE, "native archive", fetch)
        sidecar = _fetch_release_asset(f"{source_url}.sha256", MAX_CHECKSUM_SIZE, "native archive checksum", fetch)
        archive_sha256 = sha256(compressed)
        if archive_sha256 != _checksum_from_sidecar(sidecar, target.asset):
            raise AcquisitionError("native archive checksum mismatch")
        archive = _gunzip_limited(compressed, MAX_UNCOMPRESSED_SIZE, "native archive")
        _extract_native_archive(archive, destination, target)
        receipt: dict[str, Any] = {
            "schema": MORPHEUS_NATIVE_SCHEMA_VERSION,
            "producer": _PRODUCER,
            "packageVersion": MORPHEUS_PYTHON_VERSION,
            "nativeVersion": MORPHEUS_NATIVE_VERSION,
            "abiVersion": MORPHEUS_NATIVE_ABI_VERSION,
            "target": target.name,
            "asset": target.asset,
            "archiveSha256": archive_sha256,
            "sourceUrl": source_url,
            "libraryPath": target.library_path,
        }
        _write_json(destination / NATIVE_RECEIPT_FILE, receipt)
        return receipt
    except BaseException as error:
        _rollback(destination, error)
        raise


# Stem data -----------------------------------------------------------------


def _extract_dataset(archive: bytes, definition: Dataset) -> tuple[dict[str, bytes], bytes]:
    data_root = f"{definition.archive_root}{definition.data_prefix}"
    license_path = f"{definition.archive_root}{definition.license_path}"
    files: dict[str, bytes] = {}
    digest_lines: list[str] = []
    license_text: bytes | None = None
    for entry in _iter_tar(archive, f"{definition.name} dataset archive"):
        if entry.path == license_path:
            if entry.kind != "file":
                raise AcquisitionError("upstream license is not a file")
            license_text = entry.content
            continue
        if not entry.path.startswith(data_root):
            continue
        relative = entry.path[len(data_root):].rstrip("/")
        if relative == "":
            continue
        path = _safe_relative_path(relative)
        if entry.kind == "dir":
            continue
        if entry.kind != "file":
            raise AcquisitionError(f"unsupported dataset archive entry: {entry.path}")
        if path in files:
            raise AcquisitionError(f"duplicate dataset path: {path}")
        files[path] = entry.content
        digest_lines.append(f"{sha256(entry.content)}  {path}")
    if len(files) != definition.file_count:
        raise AcquisitionError(
            f"{definition.name} archive contains {len(files)} dataset files; expected {definition.file_count}"
        )
    actual_tree = _tree_digest(digest_lines)
    if actual_tree != definition.tree_sha256:
        raise AcquisitionError(f"{definition.name} dataset digest mismatch: {actual_tree}")
    if license_text is None or sha256(license_text) != definition.license_sha256:
        raise AcquisitionError(f"{definition.name} upstream license digest mismatch")
    return files, license_text


def _download_dataset(definition: Dataset, fetch: Fetcher) -> bytes:
    response = fetch(definition.archive_url)
    if response.status in (301, 302, 303, 307, 308):
        raise AcquisitionError(f"{definition.name} dataset download redirected")
    compressed = _read_ok(response, MAX_COMPRESSED_SIZE, f"{definition.name} dataset")
    return _gunzip_limited(compressed, MAX_UNCOMPRESSED_SIZE, f"{definition.name} dataset")


def select_files(files: Mapping[str, bytes], subset: str, languages: tuple[str, ...]) -> dict[str, bytes]:
    """The files to write out of the verified ``files``: the whole tree, or
    the runtime subset of the selected languages, in the dataset's order."""
    if subset == "full":
        return dict(files)
    if subset != "runtime":
        raise ValueError(f"unsupported subset: {subset}")
    return {path: content for path, content in files.items() if is_runtime_file(path, languages)}


def _manifest_of(files: Mapping[str, bytes], receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": MORPHEUS_MANIFEST_SCHEMA_VERSION,
        "dataset": receipt["dataset"],
        "revision": receipt["source"]["revision"],
        "subset": receipt["subset"]["name"],
        "languages": receipt["languages"],
        "files": [
            {"path": path, "size": len(content), "sha256": sha256(content)}
            for path, content in sorted(files.items())
        ],
    }


def verify_gener_index(path: str | os.PathLike[str]) -> bytes:
    """Read a prepared experimental generation index and check that it is the
    one derived from the pinned Alpheios and Perseids revisions."""
    index = Path(path).read_bytes()
    actual = sha256(index)
    if actual != GENER_INDEX_SHA256:
        raise AcquisitionError(
            f"gener.index digest {actual} differs from the pinned {GENER_INDEX_SHA256}"
        )
    return index


def acquire_data(
    dataset: str,
    output: str | os.PathLike[str],
    *,
    subset: str = "full",
    languages: list[str] | tuple[str, ...] | None = None,
    manifest: bool = False,
    gener_index: str | os.PathLike[str] | None = None,
    fetch: Fetcher | None = None,
    datasets: Mapping[str, Dataset] = DATASETS,
) -> dict[str, Any]:
    """Download the pinned upstream ``dataset`` (``alpheios`` or ``perseids``),
    verify its tree and license, and write it into ``output``, which must not
    exist, with ``UPSTREAM-LICENSE`` and the receipt ``MORPHEUS-DATA.json``.

    ``subset="runtime"`` writes only the files the libmorpheus runtime reads;
    ``languages`` keeps only those ISO 639-3 languages; ``manifest`` also
    writes ``stemlib-manifest.json``. ``gener_index`` installs a prepared
    experimental Greek generation index after verifying its digest against
    the pinned one; the Python package does not prepare the index itself.
    """
    fetch = fetch or default_fetch
    definition = datasets.get(dataset)
    if definition is None:
        raise ValueError(f"unsupported Morpheus dataset: {dataset}")
    if subset not in ("full", "runtime"):
        raise ValueError(f"unsupported subset: {subset}")
    selected_languages = select_languages(languages, definition.languages)
    index: bytes | None = None
    if gener_index is not None:
        if not definition.generation:
            raise ValueError(f"dataset {definition.name} does not support experimental generation")
        if "grc" not in selected_languages:
            raise ValueError("a generation index requires Greek among the selected languages")
        index = verify_gener_index(gener_index)
    destination = Path(output).resolve()
    _ensure_absent(destination)
    destination.mkdir()
    try:
        files, license_text = _extract_dataset(_download_dataset(definition, fetch), definition)
        written = select_files(files, subset, selected_languages)
        support_source = None
        if index is not None:
            written["gener.index"] = index
            support = datasets.get("perseids")
            support_source = None if support is None else {
                "repository": support.repository,
                "revision": support.revision,
                "archiveUrl": support.archive_url,
            }
        for path, content in written.items():
            file_path = destination.joinpath(*path.split("/"))
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "xb") as stream:
                stream.write(content)
        with open(destination / DATA_LICENSE_FILE, "xb") as stream:
            stream.write(license_text)
        subset_lines = [f"{sha256(content)}  {path}" for path, content in written.items()]
        receipt: dict[str, Any] = {
            "schema": MORPHEUS_DATA_SCHEMA_VERSION,
            "producer": _PRODUCER,
            "packageVersion": MORPHEUS_PYTHON_VERSION,
            "dataset": definition.name,
            "languages": list(selected_languages),
            "source": {
                "repository": definition.repository,
                "revision": definition.revision,
                "archiveUrl": definition.archive_url,
            },
            "files": {"count": definition.file_count, "treeSha256": definition.tree_sha256},
            "subset": {"name": subset, "count": len(written), "treeSha256": _tree_digest(subset_lines)},
            "generation": {
                "experimental": True,
                "available": index is not None,
                "indexSha256": None if index is None else GENER_INDEX_SHA256,
                "supportSource": support_source,
            },
            "manifest": DATA_MANIFEST_FILE if manifest else None,
        }
        if manifest:
            _write_json(destination / DATA_MANIFEST_FILE, _manifest_of(written, receipt))
        _write_json(destination / DATA_RECEIPT_FILE, receipt)
        return receipt
    except BaseException as error:
        _rollback(destination, error)
        raise


# Combined setup ------------------------------------------------------------


def _contains(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def setup_morpheus(
    dataset: str,
    *,
    native_output: str | os.PathLike[str] = "./morpheus-native",
    data_output: str | os.PathLike[str] = "./morpheus-data",
    gener_index: str | os.PathLike[str] | None = None,
    fetch: Fetcher | None = None,
    host: tuple[str, str, str | None] | None = None,
) -> dict[str, Any]:
    """Acquire the native runtime and one dataset into two separate new
    directories; the native installation is removed if the data fails."""
    if dataset not in DATASETS:
        raise ValueError(f"unsupported dataset: {dataset}")
    if gener_index is not None and dataset != "alpheios":
        raise ValueError("a generation index is supported only with the Alpheios dataset")
    native_path = Path(native_output).resolve()
    data_path = Path(data_output).resolve()
    if _contains(native_path, data_path) or _contains(data_path, native_path):
        raise ValueError("native and data outputs must be separate, non-overlapping directories")
    for path in (native_path, data_path):
        _ensure_absent(path)
    native = acquire_native(native_path, fetch=fetch, host=host)
    try:
        data = acquire_data(dataset, data_path, gener_index=gener_index, fetch=fetch)
    except BaseException as error:
        _rollback(native_path, error)
        raise
    return {
        "native": native,
        "data": data,
        "nativeOutput": str(native_path),
        "dataOutput": str(data_path),
        "nativeLibraryPath": str(native_path / native["libraryPath"]),
    }


__all__ = [
    "AcquisitionError",
    "Fetcher",
    "Response",
    "acquire_data",
    "acquire_native",
    "default_fetch",
    "host_platform",
    "select_files",
    "setup_morpheus",
    "sha256",
    "verify_gener_index",
]
