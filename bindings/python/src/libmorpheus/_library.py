# SPDX-License-Identifier: AGPL-3.0-or-later
"""Resource-owning Python facade for the libmorpheus ABI."""

from __future__ import annotations

import ctypes
from os import PathLike, fspath
from threading import RLock
from typing import Callable, Self

from ._abi import (
    ABI_VERSION,
    GENERATION_OPTIONS_VERSION,
    AnalysisRecord,
    GenerationRecord,
    NativeGenerationOptions,
    NativeLibrary,
    encoded_buffer,
)
from ._types import (
    Analysis,
    Generation,
    GenerationOptions,
    Language,
    Option,
    RawAnalysis,
    RawGeneration,
    Status,
    normalize_analysis,
    normalize_generation,
)


class MorpheusError(RuntimeError):
    """Error reported by the native ABI, including its numeric status."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def _message(native: NativeLibrary, status: int) -> str:
    message = native.status_message(status)
    return message.decode("utf-8") if message else f"Morpheus status {status}"


def _language_name(language: int) -> str:
    try:
        return Language(int(language)).name.capitalize()
    except ValueError:
        return f"language {int(language)}"


def _check(native: NativeLibrary, status: int) -> None:
    if status != Status.OK:
        raise MorpheusError(status, _message(native, status))


def _text(value: bytes) -> str:
    return value.split(b"\0", 1)[0].decode("utf-8")


def _raw_analysis(record: AnalysisRecord, truncated_fields: int) -> RawAnalysis:
    return RawAnalysis(
        struct_size=record.struct_size,
        part_of_speech=record.part_of_speech,
        dialect=record.dialect,
        geographic_region=record.geographic_region,
        person=record.person,
        number=record.number,
        gender=record.gender,
        grammatical_case=record.grammatical_case,
        tense=record.tense,
        mood=record.mood,
        voice=record.voice,
        degree=record.degree,
        raw=_text(record.raw),
        workword=_text(record.workword),
        lemma=_text(record.lemma),
        preverb=_text(record.preverb),
        augment=_text(record.augment),
        stem=_text(record.stem),
        suffix=_text(record.suffix),
        ending=_text(record.ending),
        crasis=_text(record.crasis),
        dictionary_form=_text(record.dictionary_form),
        english_form=_text(record.english_form),
        raw_preverb=_text(record.raw_preverb),
        domains=_text(record.domains),
        morph_flags=bytes(record.morph_flags),
        truncated_fields=truncated_fields,
    )


def _raw_generation(
    record: GenerationRecord, truncated_fields: int
) -> RawGeneration:
    return RawGeneration(
        struct_size=record.struct_size,
        part_of_speech=record.part_of_speech,
        dialect=record.dialect,
        geographic_region=record.geographic_region,
        person=record.person,
        number=record.number,
        gender=record.gender,
        grammatical_case=record.grammatical_case,
        tense=record.tense,
        mood=record.mood,
        voice=record.voice,
        degree=record.degree,
        surface=_text(record.surface),
        lemma=_text(record.lemma),
        morph_flags=bytes(record.morph_flags),
        truncated_fields=truncated_fields,
    )


def _generation_options(options: GenerationOptions) -> NativeGenerationOptions:
    if not isinstance(options.result_limit, int) or isinstance(
        options.result_limit, bool
    ) or not 0 <= options.result_limit <= 65_536:
        raise ValueError("result_limit must be an integer from 0 to 65536")
    return NativeGenerationOptions(
        version=GENERATION_OPTIONS_VERSION,
        struct_size=ctypes.sizeof(NativeGenerationOptions),
        result_limit=options.result_limit,
        flags=1 if options.exclude_duals else 0,
        part_of_speech=int(options.part_of_speech),
        dialect=int(options.dialect),
        geographic_region=int(options.geographic_region),
        person=int(options.person),
        number=int(options.number),
        gender=int(options.gender),
        grammatical_case=int(options.grammatical_case),
        tense=int(options.tense),
        mood=int(options.mood),
        voice=int(options.voice),
        degree=int(options.degree),
    )


class Library:
    """Owns one validated native library and creates stateful contexts."""

    def __init__(self, path: str | PathLike[str]) -> None:
        self._native: NativeLibrary | None = NativeLibrary(path)
        self._contexts = 0
        self._lock = RLock()

    def context(
        self, stemlib_path: str | PathLike[str], language: Language
    ) -> Context:
        with self._lock:
            native = self._require_open()
            path = fspath(stemlib_path)
            if not isinstance(path, str):
                raise TypeError("stemlib path must resolve to a string")
            encoded, buffer = encoded_buffer(path, "stemlib path")
            pointer = ctypes.c_void_p()
            status = native.open_path(
                ABI_VERSION,
                buffer,
                len(encoded),
                int(language),
                ctypes.byref(pointer),
            )
            if status != Status.OK:
                # Name the stemlib and the language: an incomplete stemlib is
                # the usual cause, such as a Greek-only dataset opened for Latin.
                raise MorpheusError(
                    status,
                    f"opening {path} for {_language_name(language)} failed: "
                    f"{_message(native, status)}",
                )
            if not pointer:
                raise RuntimeError("libmorpheus returned a null context")
            self._contexts += 1
            return Context(native, pointer, self._context_closed)

    def close(self) -> None:
        with self._lock:
            if self._native is None:
                return
            if self._contexts:
                raise RuntimeError("Close all Morpheus contexts before the library")
            self._native = None

    def _require_open(self) -> NativeLibrary:
        if self._native is None:
            raise RuntimeError("Morpheus library is closed")
        return self._native

    def _context_closed(self) -> None:
        with self._lock:
            self._contexts -= 1

    def __enter__(self) -> Self:
        self._require_open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class Context:
    """One language and stemlib context with serialized native operations."""

    def __init__(
        self,
        native: NativeLibrary,
        pointer: ctypes.c_void_p,
        on_close: Callable[[], None],
    ) -> None:
        self._native = native
        self._pointer: ctypes.c_void_p | None = pointer
        self._on_close: Callable[[], None] | None = on_close
        self._lock = RLock()

    def analyze(
        self, beta_code: str, options: Option = Option.NONE
    ) -> tuple[Analysis, ...]:
        return tuple(normalize_analysis(item) for item in self.analyze_raw(beta_code, options))

    def analyze_raw(
        self, beta_code: str, options: Option = Option.NONE
    ) -> tuple[RawAnalysis, ...]:
        encoded, buffer = encoded_buffer(beta_code, "Beta Code input")
        option_value = int(options)
        if option_value < 0 or option_value > (1 << 64) - 1:
            raise ValueError("analysis options exceed uint64")
        with self._lock:
            pointer = self._require_open()
            result = ctypes.c_void_p()
            status = self._native.analyze(
                pointer,
                buffer,
                len(encoded),
                option_value,
                ctypes.byref(result),
            )
            _check(self._native, status)
            try:
                count = self._native.result_count(result)
                analyses = []
                for index in range(count):
                    storage = ctypes.create_string_buffer(
                        self._native.analysis_record_size
                    )
                    _check(
                        self._native,
                        self._native.result_copy(
                            result,
                            index,
                            storage,
                            self._native.analysis_record_size,
                        ),
                    )
                    truncated = ctypes.c_uint32()
                    _check(
                        self._native,
                        self._native.result_truncated_fields(
                            result, index, ctypes.byref(truncated)
                        ),
                    )
                    record = AnalysisRecord.from_buffer_copy(storage)
                    analyses.append(_raw_analysis(record, truncated.value))
                return tuple(analyses)
            finally:
                self._native.result_free(result)

    def generate(
        self, lemma: str, options: GenerationOptions = GenerationOptions()
    ) -> tuple[Generation, ...]:
        """Generate normalized forms through the experimental native API."""
        return tuple(
            normalize_generation(item) for item in self.generate_raw(lemma, options)
        )

    def generate_raw(
        self, lemma: str, options: GenerationOptions = GenerationOptions()
    ) -> tuple[RawGeneration, ...]:
        """Generate lossless ABI records through the experimental native API."""
        encoded, buffer = encoded_buffer(lemma, "Beta Code lemma")
        native_options = _generation_options(options)
        with self._lock:
            pointer = self._require_open()
            result = ctypes.c_void_p()
            status = self._native.generate(
                pointer,
                buffer,
                len(encoded),
                ctypes.byref(native_options),
                ctypes.byref(result),
            )
            _check(self._native, status)
            try:
                count = self._native.generation_result_count(result)
                generations = []
                for index in range(count):
                    storage = ctypes.create_string_buffer(
                        self._native.generation_record_size
                    )
                    _check(
                        self._native,
                        self._native.generation_result_copy(
                            result,
                            index,
                            storage,
                            self._native.generation_record_size,
                        ),
                    )
                    truncated = ctypes.c_uint32()
                    _check(
                        self._native,
                        self._native.generation_result_truncated_fields(
                            result, index, ctypes.byref(truncated)
                        ),
                    )
                    record = GenerationRecord.from_buffer_copy(storage)
                    generations.append(_raw_generation(record, truncated.value))
                return tuple(generations)
            finally:
                self._native.generation_result_free(result)

    def close(self) -> None:
        with self._lock:
            if self._pointer is None:
                return
            self._native.close_context(self._pointer)
            self._pointer = None
            callback = self._on_close
            self._on_close = None
            if callback is not None:
                callback()

    def _require_open(self) -> ctypes.c_void_p:
        if self._pointer is None:
            raise RuntimeError("Morpheus context is closed")
        return self._pointer

    def __enter__(self) -> Self:
        self._require_open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
