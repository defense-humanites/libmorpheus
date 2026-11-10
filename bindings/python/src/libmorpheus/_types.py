# SPDX-License-Identifier: AGPL-3.0-or-later
"""Public Python values and normalized analysis and generation records."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, IntFlag
from functools import lru_cache
from typing import Sequence, TypeAlias


class Language(IntEnum):
    GREEK = 0
    LATIN = 1
    ITALIAN = 2


class Status(IntEnum):
    OK = 0
    INVALID_ARGUMENT = 1
    ABI_MISMATCH = 2
    NO_MEMORY = 3
    INPUT_TOO_LONG = 4
    OUT_OF_RANGE = 5
    INTERNAL_ERROR = 6
    BUFFER_TOO_SMALL = 7
    STEMLIB_ERROR = 8
    RESULT_LIMIT_EXCEEDED = 9


class Option(IntFlag):
    NONE = 0
    STRICT_CASE = 1 << 0
    IGNORE_ACCENTS = 1 << 1
    VERBS_ONLY = 1 << 2
    NO_CRASIS = 1 << 3
    QUICK = 1 << 4
    HQ_DICTIONARY = 1 << 5
    DIALECT_AEOLIC = 1 << 16
    DIALECT_ATTIC = 2 << 16
    DIALECT_DORIC = 4 << 16
    DIALECT_HOMERIC = 8 << 16
    DIALECT_IONIC = 16 << 16
    DIALECT_LESBIAN = 32 << 16
    DIALECT_NON_HOMERIC_EPIC = 64 << 16
    DIALECT_PARADIGM = 128 << 16
    DIALECT_EPIC = 72 << 16
    DIALECT_PROSE = 256 << 16


class PartOfSpeech(IntEnum):
    UNKNOWN = 0
    NOUN = 1
    VERB = 2
    ADJECTIVE = 3
    ADVERB = 4
    ARTICLE = 5
    PRONOUN = 6
    NUMERAL = 7
    PREPOSITION = 8
    CONJUNCTION = 9
    PARTICLE = 10
    INTERJECTION = 11


class Person(IntEnum):
    NONE = 0
    FIRST = 1
    SECOND = 2
    THIRD = 3


class Number(IntEnum):
    NONE = 0
    SINGULAR = 1
    DUAL = 2
    PLURAL = 3


class Gender(IntFlag):
    NONE = 0
    ADVERBIAL = 1
    FEMININE = 2
    MASCULINE = 4
    NEUTER = 8


class Case(IntFlag):
    NONE = 0
    ABLATIVE = 1
    ACCUSATIVE = 2
    DATIVE = 4
    GENITIVE = 8
    NOMINATIVE = 16
    VOCATIVE = 32


class Tense(IntEnum):
    NONE = 0
    PRESENT = 1
    IMPERFECT = 2
    FUTURE = 3
    AORIST = 4
    PERFECT = 5
    PLUPERFECT = 6
    FUTURE_PERFECT = 7
    PAST_ABSOLUTE = 8


class Mood(IntEnum):
    NONE = 0
    CONDITIONAL = 1
    GERUNDIVE = 2
    IMPERATIVE = 3
    INDICATIVE = 4
    INFINITIVE = 5
    OPTATIVE = 6
    PARTICIPLE = 7
    SUBJUNCTIVE = 8
    SUPINE = 9


class Voice(IntFlag):
    NONE = 0
    ACTIVE = 1
    PASSIVE = 2
    MIDDLE = 4
    DEPONENT = ACTIVE | MIDDLE
    MEDIO_PASSIVE = PASSIVE | MIDDLE


class Degree(IntEnum):
    NONE = 0
    POSITIVE = 1
    COMPARATIVE = 2
    SUPERLATIVE = 3


class Dialect(IntFlag):
    ALL = 0
    AEOLIC = 1
    ATTIC = 2
    DORIC = 4
    HOMERIC = 8
    IONIC = 16
    LESBIAN = 32
    NON_HOMERIC_EPIC = 64
    PARADIGM = 128
    EPIC = HOMERIC | NON_HOMERIC_EPIC
    PROSE = 256


class GeographicRegion(IntFlag):
    NONE = 0
    ARCADIA = 1
    ARGOLID = 2
    BOEOTIA = 4
    COS = 8
    CRETE = 16
    CYPRUS = 32
    CYRENE = 64
    ELIS = 128
    HERACLEA = 256
    LACONIA = 512
    LOCRIS = 1024
    MEGARID = 2048
    PHOCIS = 4096
    RHODES = 8192
    THERA = 16384


class TruncatedField(IntFlag):
    NONE = 0
    RAW = 1 << 0
    WORKWORD = 1 << 1
    LEMMA = 1 << 2
    PREVERB = 1 << 3
    AUGMENT = 1 << 4
    STEM = 1 << 5
    SUFFIX = 1 << 6
    ENDING = 1 << 7
    CRASIS = 1 << 8
    DICTIONARY_FORM = 1 << 9
    ENGLISH_FORM = 1 << 10
    RAW_PREVERB = 1 << 11
    DOMAINS = 1 << 12


MorphFlagName: TypeAlias = str

MORPH_FLAG_NAMES = (
    "accent-optional", "alpha-copulative", "alpha-privative",
    "antepenult-accent", "apocope", "attic-reduplication", "causal",
    "compound-only", "contracted", "delta-preverb", "derivative",
    "desiderative", "diminutive", "dissimilation", "doubled-consonant",
    "double-augment", "double-reduplication", "early", "elided-preverb",
    "enclitic", "ends-in-digamma", "en-to-eni", "frequentative",
    "geographic-name", "group-name", "has-augment", "has-preverb",
    "impersonal", "indeclinable-form", "intervocalic-s-to-h",
    "intransitive", "iota-intensive", "irregular-comparative",
    "irregular-form", "irregular-superlative", "iterative", "late", "later",
    "long-penult", "lost-accent", "metathesis", "meta-to-peda",
    "metrically-long", "needs-accent", "needs-rough-breathing",
    "not-in-composition", "no-circumflex", "no-comparison",
    "no-reduplication", "nu-movable", "n-infix", "para-to-parai",
    "person-name", "poetic", "present-reduplication", "preverb-augment",
    "proclitic", "prodelision", "pros-to-poti", "pros-to-proti",
    "quantity-metathesis", "rare", "raw-preverb", "raw-sonant",
    "recessive-accent", "reduplication", "rho-eta-iota-alpha",
    "root-preverb", "short-eis", "short-penult", "short-subjunctive",
    "sigma-to-ci", "stem-accent", "suffix-accent", "syllabic-augment",
    "syncope", "tau-preverb", "tmesis", "unaspirated-preverb", "unaugmented",
    "uncontracted-ending", "uncontracted-stem", "uper-to-upeir", "upo-to-upai",
)


@dataclass(frozen=True, slots=True)
class RawAnalysis:
    struct_size: int
    part_of_speech: int
    dialect: int
    geographic_region: int
    person: int
    number: int
    gender: int
    grammatical_case: int
    tense: int
    mood: int
    voice: int
    degree: int
    raw: str
    workword: str
    lemma: str
    preverb: str
    augment: str
    stem: str
    suffix: str
    ending: str
    crasis: str
    dictionary_form: str
    english_form: str
    raw_preverb: str
    domains: str
    morph_flags: bytes
    truncated_fields: int


@dataclass(frozen=True, slots=True)
class Analysis:
    part_of_speech: str
    dialects: tuple[str, ...]
    geographic_regions: tuple[str, ...]
    person: str | None
    grammatical_number: str | None
    genders: tuple[str, ...]
    grammatical_cases: tuple[str, ...]
    tense: str | None
    mood: str | None
    voices: tuple[str, ...]
    degree: str | None
    raw: str
    workword: str
    lemma: str
    preverb: str
    augment: str
    stem: str
    suffix: str
    ending: str
    crasis: str
    dictionary_form: str
    english_form: str
    raw_preverb: str
    domains: str
    morph_flags: tuple[MorphFlagName, ...]
    truncated_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GenerationOptions:
    result_limit: int = 0
    exclude_duals: bool = False
    part_of_speech: PartOfSpeech = PartOfSpeech.UNKNOWN
    dialect: Dialect = Dialect.ALL
    geographic_region: GeographicRegion = GeographicRegion.NONE
    person: Person = Person.NONE
    number: Number = Number.NONE
    gender: Gender = Gender.NONE
    grammatical_case: Case = Case.NONE
    tense: Tense = Tense.NONE
    mood: Mood = Mood.NONE
    voice: Voice = Voice.NONE
    degree: Degree = Degree.NONE


@dataclass(frozen=True, slots=True)
class RawGeneration:
    struct_size: int
    part_of_speech: int
    dialect: int
    geographic_region: int
    person: int
    number: int
    gender: int
    grammatical_case: int
    tense: int
    mood: int
    voice: int
    degree: int
    surface: str
    lemma: str
    morph_flags: bytes
    truncated_fields: int


@dataclass(frozen=True, slots=True)
class Generation:
    part_of_speech: str
    dialects: tuple[str, ...]
    geographic_regions: tuple[str, ...]
    person: str | None
    grammatical_number: str | None
    genders: tuple[str, ...]
    grammatical_cases: tuple[str, ...]
    tense: str | None
    mood: str | None
    voices: tuple[str, ...]
    degree: str | None
    surface: str
    lemma: str
    morph_flags: tuple[MorphFlagName, ...]
    truncated_fields: tuple[str, ...]


PART_OF_SPEECH_NAMES = tuple(
    name.lower().replace("_", "-") for name in PartOfSpeech.__members__
)
PERSON_NAMES = (None, "first", "second", "third")
NUMBER_NAMES = (None, "singular", "dual", "plural")
TENSE_NAMES = (
    None, "present", "imperfect", "future", "aorist", "perfect",
    "pluperfect", "future-perfect", "past-absolute",
)
MOOD_NAMES = (
    None, "conditional", "gerundive", "imperative", "indicative",
    "infinitive", "optative", "participle", "subjunctive", "supine",
)
DEGREE_NAMES = (None, "positive", "comparative", "superlative")
GENDER_NAMES = (
    (Gender.ADVERBIAL, "adverbial"), (Gender.FEMININE, "feminine"),
    (Gender.MASCULINE, "masculine"), (Gender.NEUTER, "neuter"),
)
CASE_NAMES = (
    (Case.ABLATIVE, "ablative"), (Case.ACCUSATIVE, "accusative"),
    (Case.DATIVE, "dative"), (Case.GENITIVE, "genitive"),
    (Case.NOMINATIVE, "nominative"), (Case.VOCATIVE, "vocative"),
)
VOICE_NAMES = (
    (Voice.ACTIVE, "active"), (Voice.PASSIVE, "passive"),
    (Voice.MIDDLE, "middle"),
)
DIALECT_NAMES = (
    (Dialect.ATTIC, "attic"), (Dialect.IONIC, "ionic"),
    (Dialect.AEOLIC, "aeolic"), (Dialect.LESBIAN, "lesbian"),
    (Dialect.HOMERIC, "homeric"), (Dialect.DORIC, "doric"),
    (Dialect.PARADIGM, "paradigm"),
    (Dialect.NON_HOMERIC_EPIC, "non-homeric-epic"),
    (Dialect.PROSE, "prose"),
)
REGION_NAMES = tuple(
    (region, region.name.lower().replace("_", "-"))
    for region in GeographicRegion
    if region is not GeographicRegion.NONE
)
TRUNCATED_NAMES = tuple(
    (field, field.name.lower())
    for field in TruncatedField
    if field is not TruncatedField.NONE
)


def _exact(value: int, names: tuple[str | None, ...]) -> str | None:
    return names[value] if 0 <= value < len(names) else None


def _mask(value: int, entries: tuple[tuple[IntFlag, str], ...]) -> tuple[str, ...]:
    return tuple(name for flag, name in entries if value & int(flag) == int(flag))


def _dialects(value: int) -> tuple[str, ...]:
    if value & int(Dialect.EPIC) == int(Dialect.EPIC):
        remaining = value & ~int(Dialect.EPIC)
        selected = {"epic"}
    else:
        remaining = value
        selected = set()
    selected.update(
        name for flag, name in DIALECT_NAMES
        if remaining & int(flag) == int(flag)
    )
    order = tuple(name for _, name in DIALECT_NAMES[:-1]) + ("epic", "prose")
    return tuple(name for name in order if name in selected)


def has_morph_flag(
    analysis: (
        RawAnalysis
        | Analysis
        | RawGeneration
        | Generation
        | Sequence[RawAnalysis | Analysis | RawGeneration | Generation]
    ),
    flag: int | str,
) -> bool:
    if isinstance(analysis, (list, tuple)):
        return any(has_morph_flag(item, flag) for item in analysis)
    if isinstance(analysis, (Analysis, Generation)):
        name = (
            MORPH_FLAG_NAMES[flag]
            if isinstance(flag, int) and 0 <= flag < len(MORPH_FLAG_NAMES)
            else flag
        )
        return isinstance(name, str) and name in analysis.morph_flags
    if isinstance(flag, str):
        try:
            flag = MORPH_FLAG_NAMES.index(flag)
        except ValueError:
            return False
    if flag < 0:
        return False
    index, bit = divmod(flag, 8)
    return index < len(analysis.morph_flags) and bool(analysis.morph_flags[index] & 1 << bit)


# The name tuples of normalized records are cached per code and shared
# between the records that carry it: a paradigm of thousands of forms holds a
# few dozen distinct values, and recomputing them for every form (the morph
# flags by testing each of the 84 known flags) made normalization most of the
# cost of generate() and analyze(). Tuples are immutable, so sharing them is
# invisible to callers. lru_cache is thread-safe and bounds each cache.
_NAME_CACHE_SIZE = 4096
_MEDIO_PASSIVE = int(Voice.MEDIO_PASSIVE)
_DEPONENT = int(Voice.DEPONENT)
_WORKWORD = int(TruncatedField.WORKWORD)
_LEMMA = int(TruncatedField.LEMMA)


@lru_cache(maxsize=_NAME_CACHE_SIZE)
def _morph_flag_names(flags: bytes) -> tuple[str, ...]:
    return tuple(
        name for index, name in enumerate(MORPH_FLAG_NAMES)
        if index >> 3 < len(flags) and flags[index >> 3] & 1 << (index & 7)
    )


@lru_cache(maxsize=_NAME_CACHE_SIZE)
def _voice_names(value: int) -> tuple[str, ...]:
    if value == _MEDIO_PASSIVE:
        return ("medio-passive",)
    if value == _DEPONENT:
        return ("deponent",)
    return _mask(value, VOICE_NAMES)


@lru_cache(maxsize=_NAME_CACHE_SIZE)
def _dialect_names(value: int) -> tuple[str, ...]:
    return _dialects(value)


@lru_cache(maxsize=_NAME_CACHE_SIZE)
def _region_names(value: int) -> tuple[str, ...]:
    return _mask(value, REGION_NAMES)


@lru_cache(maxsize=_NAME_CACHE_SIZE)
def _gender_names(value: int) -> tuple[str, ...]:
    return _mask(value, GENDER_NAMES)


@lru_cache(maxsize=_NAME_CACHE_SIZE)
def _case_names(value: int) -> tuple[str, ...]:
    return _mask(value, CASE_NAMES)


@lru_cache(maxsize=_NAME_CACHE_SIZE)
def _truncated_names(value: int) -> tuple[str, ...]:
    return _mask(value, TRUNCATED_NAMES)


@lru_cache(maxsize=_NAME_CACHE_SIZE)
def _generation_truncated_names(value: int) -> tuple[str, ...]:
    names = []
    if value & _WORKWORD:
        names.append("surface")
    if value & _LEMMA:
        names.append("lemma")
    return tuple(names)


def normalize_analysis(raw: RawAnalysis) -> Analysis:
    return Analysis(
        part_of_speech=_exact(raw.part_of_speech, PART_OF_SPEECH_NAMES) or "unknown",
        dialects=_dialect_names(raw.dialect),
        geographic_regions=_region_names(raw.geographic_region),
        person=_exact(raw.person, PERSON_NAMES),
        grammatical_number=_exact(raw.number, NUMBER_NAMES),
        genders=_gender_names(raw.gender),
        grammatical_cases=_case_names(raw.grammatical_case),
        tense=_exact(raw.tense, TENSE_NAMES),
        mood=_exact(raw.mood, MOOD_NAMES),
        voices=_voice_names(raw.voice),
        degree=_exact(raw.degree, DEGREE_NAMES),
        raw=raw.raw,
        workword=raw.workword,
        lemma=raw.lemma,
        preverb=raw.preverb,
        augment=raw.augment,
        stem=raw.stem,
        suffix=raw.suffix,
        ending=raw.ending,
        crasis=raw.crasis,
        dictionary_form=raw.dictionary_form,
        english_form=raw.english_form,
        raw_preverb=raw.raw_preverb,
        domains=raw.domains,
        morph_flags=_morph_flag_names(raw.morph_flags),
        truncated_fields=_truncated_names(raw.truncated_fields),
    )


def normalize_generation(raw: RawGeneration) -> Generation:
    return Generation(
        part_of_speech=_exact(raw.part_of_speech, PART_OF_SPEECH_NAMES) or "unknown",
        dialects=_dialect_names(raw.dialect),
        geographic_regions=_region_names(raw.geographic_region),
        person=_exact(raw.person, PERSON_NAMES),
        grammatical_number=_exact(raw.number, NUMBER_NAMES),
        genders=_gender_names(raw.gender),
        grammatical_cases=_case_names(raw.grammatical_case),
        tense=_exact(raw.tense, TENSE_NAMES),
        mood=_exact(raw.mood, MOOD_NAMES),
        voices=_voice_names(raw.voice),
        degree=_exact(raw.degree, DEGREE_NAMES),
        surface=raw.surface,
        lemma=raw.lemma,
        morph_flags=_morph_flag_names(raw.morph_flags),
        truncated_fields=_generation_truncated_names(raw.truncated_fields),
    )
