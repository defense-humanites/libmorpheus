# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pinned acquisition sources: native release targets and upstream datasets.

The values mirror the Node.js binding's ``internal/native-manifest.js`` and
the ``@libmorpheus/data`` package's ``internal/data-manifest.js`` and
``internal/runtime-subset.js``; the CMake guard ``python_package_metadata``
keeps the revisions and digests identical across the bindings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from types import MappingProxyType

from ._version import MORPHEUS_NATIVE_ABI_VERSION, MORPHEUS_NATIVE_VERSION

MORPHEUS_NATIVE_REPOSITORY = "https://github.com/defense-humanites/libmorpheus"
MORPHEUS_NATIVE_SCHEMA_VERSION = 2
MORPHEUS_DATA_SCHEMA_VERSION = 1
MORPHEUS_MANIFEST_SCHEMA_VERSION = 1

NATIVE_RECEIPT_FILE = "MORPHEUS-NATIVE.json"
DATA_RECEIPT_FILE = "MORPHEUS-DATA.json"
DATA_LICENSE_FILE = "UPSTREAM-LICENSE"
DATA_MANIFEST_FILE = "stemlib-manifest.json"

#: SHA-256 of the experimental Greek generation index prepared from the
#: pinned Alpheios and Perseids revisions (``gener.index``). The Python package
#: does not prepare the index itself; it verifies and installs one.
GENER_INDEX_SHA256 = "eeef2145c7d95c0f2e36b0efdd9ebfcdde7fbc51b8ba903b6dca723801a72adf"


@dataclass(frozen=True)
class NativeTarget:
    """One prebuilt native archive of the declared release."""

    system: str
    machine: str
    name: str
    asset: str
    archive_root: str
    library_path: str


def _native_target(system: str, machine: str, name: str, suffix: str, library: str) -> NativeTarget:
    stem = f"libmorpheus-{MORPHEUS_NATIVE_VERSION}-{suffix}"
    return NativeTarget(
        system=system,
        machine=machine,
        name=name,
        asset=f"{stem}.tar.gz",
        archive_root=f"{stem}/",
        library_path=library,
    )


NATIVE_TARGETS: tuple[NativeTarget, ...] = (
    _native_target("linux", "x86_64", "linux-x86_64-glibc", "Linux-x86_64-glibc", "lib/libmorpheus.so"),
    _native_target("linux", "aarch64", "linux-aarch64-glibc", "Linux-aarch64-glibc", "lib/libmorpheus.so"),
    _native_target("darwin", "arm64", "macos-arm64", "macOS-arm64", "lib/libmorpheus.dylib"),
)


def select_native_target(system: str, machine: str, libc: str | None) -> NativeTarget:
    """Select the archive for ``system``/``machine`` (``platform`` module names).

    On Linux ``libc`` is the C library name reported by ``platform.libc_ver()``;
    the prebuilt archives link against glibc, so musl hosts are refused rather
    than given an incompatible binary.
    """
    if system == "linux" and libc != "glibc":
        raise ValueError("the libmorpheus native runtime requires glibc on Linux")
    for target in NATIVE_TARGETS:
        if target.system == system and target.machine == machine:
            return target
    raise ValueError(f"unsupported native platform: {system}/{machine}")


@dataclass(frozen=True)
class Dataset:
    """One audited upstream stem dataset, pinned to a revision."""

    name: str
    repository: str
    revision: str
    archive_url: str
    archive_root: str
    data_prefix: str
    file_count: int
    tree_sha256: str
    license_path: str
    license_sha256: str
    languages: tuple[str, ...]
    generation: bool


_ALPHEIOS_REVISION = "4632415fe93c85e9fdca47a0c5a13f31385f0023"
_PERSEIDS_REVISION = "ab6898ffed335fc6169fa02c9940657a9b5a78e0"

DATASETS: MappingProxyType[str, Dataset] = MappingProxyType({
    "alpheios": Dataset(
        name="alpheios",
        repository="https://github.com/alpheios-project/morpheus",
        revision=_ALPHEIOS_REVISION,
        archive_url=f"https://codeload.github.com/alpheios-project/morpheus/tar.gz/{_ALPHEIOS_REVISION}",
        archive_root=f"morpheus-{_ALPHEIOS_REVISION}/",
        data_prefix="dist/stemlib/",
        file_count=237,
        tree_sha256="ab3b52c50a0c970647a81cd2dce56317fd7502eab697caa58da4dd97cec743a0",
        license_path="LICENSE",
        license_sha256="f27c9386a3a6dcad6e733e951aadb7dd548fcdde7518de82f60ac6ed5da67951",
        languages=("grc",),
        generation=True,
    ),
    "perseids": Dataset(
        name="perseids",
        repository="https://github.com/perseids-tools/morpheus",
        revision=_PERSEIDS_REVISION,
        archive_url=f"https://codeload.github.com/perseids-tools/morpheus/tar.gz/{_PERSEIDS_REVISION}",
        archive_root=f"morpheus-{_PERSEIDS_REVISION}/",
        data_prefix="stemlib/",
        file_count=1083,
        tree_sha256="b1ee71e27f00f6f69ec3c162bfb504b5165264d4de5515842e546242d597e7d2",
        license_path="LICENSE",
        license_sha256="1f256ecad192880510e84ad60474eab7589218784b9a50bc7ceee34c2b91f1d5",
        languages=("grc", "lat"),
        generation=False,
    ),
})

#: Stemlib directory of each ISO 639-3 language code the datasets declare.
LANGUAGE_DIRECTORIES: MappingProxyType[str, str] = MappingProxyType({"grc": "Greek", "lat": "Latin"})

# The subset of a stemlib that the libmorpheus runtime reads: what open()
# validates (the rule tables, the stem indices and their pre-index sidecars,
# the ending and derivation indices) plus what analysis and generation read
# lazily (the ending tables by stem class, the compound verb list, the
# dictionary entries, and gener.index at the stemlib root).
_RUNTIME_FILE = re.compile(
    r"^(?:rule_files/[^/]+|steminds/(?:nomind|vbind)(?:\.lindex)?"
    r"|endtables/(?:indices|out)/[^/]+|derivs/indices/derivind"
    r"|stemsrc/(?:vbs\.cmp\.ml|lemlist))$"
)


def is_runtime_file(path: str, languages: tuple[str, ...] | list[str]) -> bool:
    """Whether ``path`` (relative to the stemlib root) is read at run time
    for one of ``languages``."""
    if path == "gener.index":
        return True
    directory, separator, rest = path.partition("/")
    if not separator:
        return False
    for code, name in LANGUAGE_DIRECTORIES.items():
        if name == directory:
            return code in languages and _RUNTIME_FILE.match(rest) is not None
    return False


def select_languages(requested: list[str] | tuple[str, ...] | None, available: tuple[str, ...]) -> tuple[str, ...]:
    """Validate ISO 639-3 codes against a dataset's languages, keeping the
    dataset's own order."""
    if requested is None:
        return tuple(available)
    codes = list(dict.fromkeys(requested))
    if not codes:
        raise ValueError("at least one language is required")
    for code in codes:
        if code not in LANGUAGE_DIRECTORIES:
            raise ValueError(f"unknown language: {code}")
        if code not in available:
            raise ValueError(f"language {code} is not in this dataset")
    return tuple(code for code in available if code in codes)


__all__ = [
    "DATASETS",
    "DATA_LICENSE_FILE",
    "DATA_MANIFEST_FILE",
    "DATA_RECEIPT_FILE",
    "Dataset",
    "GENER_INDEX_SHA256",
    "LANGUAGE_DIRECTORIES",
    "MORPHEUS_DATA_SCHEMA_VERSION",
    "MORPHEUS_MANIFEST_SCHEMA_VERSION",
    "MORPHEUS_NATIVE_ABI_VERSION",
    "MORPHEUS_NATIVE_REPOSITORY",
    "MORPHEUS_NATIVE_SCHEMA_VERSION",
    "MORPHEUS_NATIVE_VERSION",
    "NATIVE_RECEIPT_FILE",
    "NATIVE_TARGETS",
    "NativeTarget",
    "is_runtime_file",
    "select_languages",
    "select_native_target",
]
