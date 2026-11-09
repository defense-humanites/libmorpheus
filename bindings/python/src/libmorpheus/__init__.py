# SPDX-License-Identifier: AGPL-3.0-or-later
"""Typed Python binding for the libmorpheus native runtime."""

from ._acquisition import (
    AcquisitionError,
    acquire_data,
    acquire_native,
    setup_morpheus,
    verify_gener_index,
)
from ._library import Context, Library, MorpheusError
from ._types import (
    Analysis,
    Case,
    Degree,
    Dialect,
    Gender,
    Generation,
    GenerationOptions,
    GeographicRegion,
    Language,
    Mood,
    Number,
    Option,
    PartOfSpeech,
    Person,
    RawAnalysis,
    RawGeneration,
    Status,
    Tense,
    TruncatedField,
    Voice,
    has_morph_flag,
)
from ._version import (
    MORPHEUS_NATIVE_ABI_VERSION,
    MORPHEUS_NATIVE_VERSION,
    MORPHEUS_PYTHON_VERSION,
)

__version__ = MORPHEUS_PYTHON_VERSION

__all__ = [
    "AcquisitionError",
    "Analysis",
    "Case",
    "Context",
    "Degree",
    "Dialect",
    "Gender",
    "Generation",
    "GenerationOptions",
    "GeographicRegion",
    "Language",
    "Library",
    "Mood",
    "MORPHEUS_NATIVE_ABI_VERSION",
    "MORPHEUS_NATIVE_VERSION",
    "MORPHEUS_PYTHON_VERSION",
    "MorpheusError",
    "Number",
    "Option",
    "PartOfSpeech",
    "Person",
    "RawAnalysis",
    "RawGeneration",
    "Status",
    "Tense",
    "TruncatedField",
    "Voice",
    "__version__",
    "acquire_data",
    "acquire_native",
    "has_morph_flag",
    "setup_morpheus",
    "verify_gener_index",
]
