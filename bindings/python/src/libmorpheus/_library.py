# SPDX-License-Identifier: AGPL-3.0-or-later
"""Resource-owning Python facade for the libmorpheus ABI."""

from __future__ import annotations

import ctypes
import struct
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
    _case_names,
    _dialect_names,
    _exact,
    _gender_names,
    _generation_truncated_names,
    _morph_flag_names,
    _region_names,
    _truncated_names,
    _voice_names,
    DEGREE_NAMES,
    MOOD_NAMES,
    NUMBER_NAMES,
    PART_OF_SPEECH_NAMES,
    PERSON_NAMES,
    TENSE_NAMES,
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


# analyze() and generate() decode each copied record straight into the
# named object, from the record bytes, instead of building the raw record
# first: the twelve numeric fields through one struct, each text field up to
# its first NUL. Offsets come from the ctypes layouts of the C ABI.
_NUMBERS = struct.Struct("<12I")
assert AnalysisRecord.part_of_speech.offset == 4
assert GenerationRecord.part_of_speech.offset == 4


def _field(record_type: type[ctypes.Structure], name: str) -> tuple[int, int]:
    descriptor = getattr(record_type, name)
    return descriptor.offset, descriptor.offset + descriptor.size


_ANALYSIS_TEXTS = tuple(
    _field(AnalysisRecord, name)
    for name in (
        "raw", "workword", "lemma", "preverb", "augment", "stem", "suffix",
        "ending", "crasis", "dictionary_form", "english_form", "raw_preverb",
        "domains",
    )
)
_ANALYSIS_FLAGS = _field(AnalysisRecord, "morph_flags")
_GENERATION_SURFACE = _field(GenerationRecord, "surface")
_GENERATION_LEMMA = _field(GenerationRecord, "lemma")
_GENERATION_FLAGS = _field(GenerationRecord, "morph_flags")


def _cut(data: bytes, field: tuple[int, int]) -> str:
    start, end = field
    stop = data.find(b"\0", start, end)
    return data[start:end if stop < 0 else stop].decode("utf-8")


def _named_analysis(data: bytes, truncated_fields: int) -> Analysis:
    numbers = _NUMBERS.unpack_from(data)
    texts = [_cut(data, field) for field in _ANALYSIS_TEXTS]
    start, end = _ANALYSIS_FLAGS
    return Analysis(
        part_of_speech=_exact(numbers[1], PART_OF_SPEECH_NAMES) or "unknown",
        dialects=_dialect_names(numbers[2]),
        geographic_regions=_region_names(numbers[3]),
        person=_exact(numbers[4], PERSON_NAMES),
        grammatical_number=_exact(numbers[5], NUMBER_NAMES),
        genders=_gender_names(numbers[6]),
        grammatical_cases=_case_names(numbers[7]),
        tense=_exact(numbers[8], TENSE_NAMES),
        mood=_exact(numbers[9], MOOD_NAMES),
        voices=_voice_names(numbers[10]),
        degree=_exact(numbers[11], DEGREE_NAMES),
        raw=texts[0],
        workword=texts[1],
        lemma=texts[2],
        preverb=texts[3],
        augment=texts[4],
        stem=texts[5],
        suffix=texts[6],
        ending=texts[7],
        crasis=texts[8],
        dictionary_form=texts[9],
        english_form=texts[10],
        raw_preverb=texts[11],
        domains=texts[12],
        morph_flags=_morph_flag_names(data[start:end]),
        truncated_fields=_truncated_names(truncated_fields),
    )


def _named_generation(data: bytes, truncated_fields: int) -> Generation:
    numbers = _NUMBERS.unpack_from(data)
    start, end = _GENERATION_FLAGS
    return Generation(
        part_of_speech=_exact(numbers[1], PART_OF_SPEECH_NAMES) or "unknown",
        dialects=_dialect_names(numbers[2]),
        geographic_regions=_region_names(numbers[3]),
        person=_exact(numbers[4], PERSON_NAMES),
        grammatical_number=_exact(numbers[5], NUMBER_NAMES),
        genders=_gender_names(numbers[6]),
        grammatical_cases=_case_names(numbers[7]),
        tense=_exact(numbers[8], TENSE_NAMES),
        mood=_exact(numbers[9], MOOD_NAMES),
        voices=_voice_names(numbers[10]),
        degree=_exact(numbers[11], DEGREE_NAMES),
        surface=_cut(data, _GENERATION_SURFACE),
        lemma=_cut(data, _GENERATION_LEMMA),
        morph_flags=_morph_flag_names(data[start:end]),
        truncated_fields=_generation_truncated_names(truncated_fields),
    )


def _copy_records(
    native: NativeLibrary,
    result: ctypes.c_void_p,
    count: int,
    record_size: int,
    copy: Callable,
    truncated: Callable,
    build: Callable,
) -> tuple:
    """Copy every record of a result through one reused buffer."""
    storage = ctypes.create_string_buffer(record_size)
    mask = ctypes.c_uint32()
    mask_pointer = ctypes.byref(mask)
    records = []
    for index in range(count):
        _check(native, copy(result, index, storage, record_size))
        _check(native, truncated(result, index, mask_pointer))
        records.append(build(storage.raw, mask.value))
    return tuple(records)


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


def _raw_analysis_from(data: bytes, truncated_fields: int) -> RawAnalysis:
    return _raw_analysis(AnalysisRecord.from_buffer_copy(data), truncated_fields)


def _raw_generation_from(data: bytes, truncated_fields: int) -> RawGeneration:
    return _raw_generation(GenerationRecord.from_buffer_copy(data), truncated_fields)


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
        return self._analyze(beta_code, options, _named_analysis)

    def analyze_raw(
        self, beta_code: str, options: Option = Option.NONE
    ) -> tuple[RawAnalysis, ...]:
        return self._analyze(beta_code, options, _raw_analysis_from)

    def _analyze(self, beta_code: str, options: Option, build: Callable) -> tuple:
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
                return _copy_records(
                    self._native,
                    result,
                    self._native.result_count(result),
                    self._native.analysis_record_size,
                    self._native.result_copy,
                    self._native.result_truncated_fields,
                    build,
                )
            finally:
                self._native.result_free(result)

    def generate(
        self, lemma: str, options: GenerationOptions = GenerationOptions()
    ) -> tuple[Generation, ...]:
        """Generate normalized forms through the experimental native API."""
        return self._generate(lemma, options, _named_generation)

    def generate_raw(
        self, lemma: str, options: GenerationOptions = GenerationOptions()
    ) -> tuple[RawGeneration, ...]:
        """Generate lossless ABI records through the experimental native API."""
        return self._generate(lemma, options, _raw_generation_from)

    def _generate(self, lemma: str, options: GenerationOptions, build: Callable) -> tuple:
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
                return _copy_records(
                    self._native,
                    result,
                    self._native.generation_result_count(result),
                    self._native.generation_record_size,
                    self._native.generation_result_copy,
                    self._native.generation_result_truncated_fields,
                    build,
                )
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
