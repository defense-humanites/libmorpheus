# SPDX-License-Identifier: AGPL-3.0-or-later
"""Private ctypes declarations for libmorpheus ABI version 2."""

from __future__ import annotations

import ctypes
from os import PathLike, fspath

from ._version import MORPHEUS_NATIVE_ABI_VERSION

ABI_VERSION = MORPHEUS_NATIVE_ABI_VERSION
TEXT_CAPACITY = 64
DOMAIN_CAPACITY = 24
MORPH_FLAG_CAPACITY = 11
GENERATION_OPTIONS_VERSION = 1


class AnalysisRecord(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("part_of_speech", ctypes.c_uint32),
        ("dialect", ctypes.c_uint32),
        ("geographic_region", ctypes.c_uint32),
        ("person", ctypes.c_uint32),
        ("number", ctypes.c_uint32),
        ("gender", ctypes.c_uint32),
        ("grammatical_case", ctypes.c_uint32),
        ("tense", ctypes.c_uint32),
        ("mood", ctypes.c_uint32),
        ("voice", ctypes.c_uint32),
        ("degree", ctypes.c_uint32),
        ("raw", ctypes.c_char * TEXT_CAPACITY),
        ("workword", ctypes.c_char * TEXT_CAPACITY),
        ("lemma", ctypes.c_char * TEXT_CAPACITY),
        ("preverb", ctypes.c_char * TEXT_CAPACITY),
        ("augment", ctypes.c_char * TEXT_CAPACITY),
        ("stem", ctypes.c_char * TEXT_CAPACITY),
        ("suffix", ctypes.c_char * TEXT_CAPACITY),
        ("ending", ctypes.c_char * TEXT_CAPACITY),
        ("crasis", ctypes.c_char * TEXT_CAPACITY),
        ("dictionary_form", ctypes.c_char * TEXT_CAPACITY),
        ("english_form", ctypes.c_char * TEXT_CAPACITY),
        ("raw_preverb", ctypes.c_char * TEXT_CAPACITY),
        ("domains", ctypes.c_char * DOMAIN_CAPACITY),
        ("morph_flags", ctypes.c_uint8 * MORPH_FLAG_CAPACITY),
    ]


class GenerationRecord(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("part_of_speech", ctypes.c_uint32),
        ("dialect", ctypes.c_uint32),
        ("geographic_region", ctypes.c_uint32),
        ("person", ctypes.c_uint32),
        ("number", ctypes.c_uint32),
        ("gender", ctypes.c_uint32),
        ("grammatical_case", ctypes.c_uint32),
        ("tense", ctypes.c_uint32),
        ("mood", ctypes.c_uint32),
        ("voice", ctypes.c_uint32),
        ("degree", ctypes.c_uint32),
        ("surface", ctypes.c_char * TEXT_CAPACITY),
        ("lemma", ctypes.c_char * TEXT_CAPACITY),
        ("morph_flags", ctypes.c_uint8 * MORPH_FLAG_CAPACITY),
    ]


class NativeGenerationOptions(ctypes.Structure):
    _fields_ = [
        ("version", ctypes.c_uint32),
        ("struct_size", ctypes.c_uint32),
        ("result_limit", ctypes.c_uint64),
        ("flags", ctypes.c_uint32),
        ("part_of_speech", ctypes.c_uint32),
        ("dialect", ctypes.c_uint32),
        ("geographic_region", ctypes.c_uint32),
        ("person", ctypes.c_uint32),
        ("number", ctypes.c_uint32),
        ("gender", ctypes.c_uint32),
        ("grammatical_case", ctypes.c_uint32),
        ("tense", ctypes.c_uint32),
        ("mood", ctypes.c_uint32),
        ("voice", ctypes.c_uint32),
        ("degree", ctypes.c_uint32),
    ]


def _function(library: ctypes.CDLL, name: str, restype: object, *argtypes: object):
    try:
        function = getattr(library, name)
    except AttributeError as error:
        raise RuntimeError(f"Missing native symbol: {name}") from error
    function.restype = restype
    function.argtypes = list(argtypes)
    return function


class NativeLibrary:
    """Validated ctypes function table for one native shared library."""

    def __init__(self, path: str | PathLike[str]) -> None:
        self.path = fspath(path)
        self.handle = ctypes.CDLL(self.path)
        # The result accessors (count, copy, truncation mask, free) are short
        # memory operations called once or twice per record. Through CDLL
        # each call released and reacquired the GIL, and with several threads
        # those thousands of reacquisitions per paradigm queued on the GIL,
        # so generation became slower with every thread added. PyDLL keeps
        # the GIL for them; analysis and generation themselves still release
        # it through CDLL.
        self.held = ctypes.PyDLL(self.path)
        self.abi_version = _function(
            self.handle, "morpheus_abi_version", ctypes.c_uint32
        )
        self.analysis_size = _function(
            self.handle, "morpheus_analysis_size", ctypes.c_size_t
        )
        self.generation_size = _function(
            self.handle, "morpheus_generation_size", ctypes.c_size_t
        )
        self.status_message = _function(
            self.handle,
            "morpheus_status_message",
            ctypes.c_char_p,
            ctypes.c_uint32,
        )
        self.open_path = _function(
            self.handle,
            "morpheus_open_path",
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_void_p),
        )
        self.close_context = _function(
            self.handle, "morpheus_close", None, ctypes.c_void_p
        )
        self.analyze = _function(
            self.handle,
            "morpheus_analyze",
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint64,
            ctypes.POINTER(ctypes.c_void_p),
        )
        self.result_count = _function(
            self.held, "morpheus_result_count", ctypes.c_size_t, ctypes.c_void_p
        )
        self.result_copy = _function(
            self.held,
            "morpheus_result_copy",
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_void_p,
            ctypes.c_size_t,
        )
        self.result_truncated_fields = _function(
            self.held,
            "morpheus_result_truncated_fields",
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint32),
        )
        self.result_free = _function(
            self.held, "morpheus_result_free", None, ctypes.c_void_p
        )
        self.generate = _function(
            self.handle,
            "morpheus_generate",
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.POINTER(NativeGenerationOptions),
            ctypes.POINTER(ctypes.c_void_p),
        )
        self.generation_result_count = _function(
            self.held,
            "morpheus_generation_result_count",
            ctypes.c_size_t,
            ctypes.c_void_p,
        )
        self.generation_result_copy = _function(
            self.held,
            "morpheus_generation_result_copy",
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_void_p,
            ctypes.c_size_t,
        )
        self.generation_result_truncated_fields = _function(
            self.held,
            "morpheus_generation_result_truncated_fields",
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint32),
        )
        self.generation_result_free = _function(
            self.held,
            "morpheus_generation_result_free",
            None,
            ctypes.c_void_p,
        )

        if self.abi_version() != ABI_VERSION:
            raise RuntimeError("Unsupported libmorpheus ABI version")
        self.analysis_record_size = self.analysis_size()
        if self.analysis_record_size < ctypes.sizeof(AnalysisRecord):
            raise RuntimeError(
                "libmorpheus analysis record is smaller than ABI version 2"
            )
        self.generation_record_size = self.generation_size()
        if self.generation_record_size < ctypes.sizeof(GenerationRecord):
            raise RuntimeError(
                "libmorpheus generation record is smaller than ABI version 2"
            )


def encoded_buffer(value: str, label: str) -> tuple[bytes, object]:
    encoded = value.encode("utf-8")
    if b"\0" in encoded:
        raise ValueError(f"{label} contains a NUL byte")
    buffer = (ctypes.c_uint8 * max(1, len(encoded)))()
    if encoded:
        buffer[: len(encoded)] = encoded
    return encoded, buffer
