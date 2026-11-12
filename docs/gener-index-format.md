<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Generation index format

This document specifies version 1 of the deterministic offline index used to
map a Greek lemma to the source records consumed by the inherited generation
core. The index is a build artifact, not a public ABI structure. Readers must
validate every count, offset, reserved field, and checksum before exposing any
entry to the runtime.

## Input contract

`morpheus_gener_index_builder OUTPUT INPUT...` reads stem-source files in the
order supplied on the command line. It recognizes lemma blocks beginning with
`:le:` and retains these generation records:

| Tag | Record kind |
| --- | ---: |
| `:no:` | 1 |
| `:aj:` | 2 |
| `:vs:` | 3 |
| `:wd:` | 4 |
| `:vb:` | 5 |

Inputs must already have passed the offline source-preparation stage. The
preparer expands `@` continuations attached to active explicit records using
the historical base-record rule. Derivation-associated continuations are not
accepted until their enclosing `:de:`/`;` sequence has been expanded to
explicit `:vs:` records. The builder therefore continues to reject `:de:`,
`;`, and `@` records rather than producing a partial index. Comments,
definitions, cross-references, and other
non-generation metadata are ignored. A generation record before its lemma and
a record without both a stem and an ASCII-key string are errors.

The version 1 key is the first whitespace-delimited token after `:le:`. It
follows the historical `gener` canonicalization by removing an initial `!`,
hyphens, hard quantity markers (`_` and `^`), and diaeresis markers (`+`).
Accents, breathings, case, and homonym digits are otherwise preserved.

A leading hyphen is kept: it marks a reserved key, the lemma's stems that
occur only in compounds (`-dhme/w` holds the `comp_only` records of
δημέω). The preparer writes these blocks
([gener-derivations.md](gener-derivations.md#compound-only-records)). Public
requests are canonicalised without hyphens and so never name a reserved key;
the runtime reads it only to compose a compound verb. Readers since version 1
accept such keys: they are ordinary keys that sort before letters.

Empty lemma blocks are omitted. After canonicalisation, blocks with identical
ordered records are deduplicated while retaining their first command-line
occurrence. All distinct blocks with the same canonical key remain separate
and retain command-line input order. Lemma groups are sorted by their unsigned
byte representation; records retain source order within each block.

## Integer and offset rules

All integers are unsigned little-endian values. All offsets in lemma and record
entries are relative to the beginning of the string table. Strings are
NUL-terminated byte strings. Version 1 uses Greek Beta Code and does not permit
embedded NUL bytes.

The file consists of a 64-byte header followed by four contiguous payload
sections:

1. lemma entries;
2. block entries;
3. record entries;
4. string bytes.

### Header

| Offset | Size | Meaning |
| ---: | ---: | --- |
| 0 | 8 | ASCII magic `MORPHGEN`. |
| 8 | 4 | Format version, currently 1. |
| 12 | 4 | Language identifier, 1 for Greek. |
| 16 | 8 | Lemma-entry count. |
| 24 | 8 | Block-entry count. |
| 32 | 8 | Record-entry count. |
| 40 | 8 | String-table byte count. |
| 48 | 8 | FNV-1a 64-bit checksum of the complete payload. |
| 56 | 8 | Reserved; must be zero. |

The expected file size is exactly:

```text
64 + lemma_count * 24 + block_count * 16 + record_count * 24 + string_bytes
```

### Lemma entry

Each 24-byte lemma entry contains:

| Offset | Size | Meaning |
| ---: | ---: | --- |
| 0 | 8 | Canonical-key string offset. |
| 8 | 8 | Index of the first block. |
| 16 | 4 | Number of blocks. |
| 20 | 4 | Reserved; must be zero. |

### Block entry

Each 16-byte block entry preserves one non-empty source block:

| Offset | Size | Meaning |
| ---: | ---: | --- |
| 0 | 8 | Index of the first record. |
| 8 | 4 | Number of records. |
| 12 | 4 | Reserved; must be zero. |

### Record entry

Each 24-byte record entry contains:

| Offset | Size | Meaning |
| ---: | ---: | --- |
| 0 | 4 | Record kind from the input table above. |
| 4 | 4 | Reserved; must be zero. |
| 8 | 8 | Stem string offset. |
| 16 | 8 | ASCII-key string offset. |

## Determinism and integrity

For identical ordered input bytes, the builder must emit identical output
bytes. It writes no host-sized integers, timestamps, paths, padding bytes, or
locale-dependent collation results. The checksum uses the standard FNV-1a
offset basis `14695981039346656037` and prime `1099511628211`.

FNV-1a detects accidental corruption but is not a cryptographic authenticity
mechanism. Release tooling must additionally publish the existing SHA-256
checksums for distributed artifacts.

## Runtime reader

The internal `morpheus_gener_index` reader loads one file into immutable owned
memory and validates it completely before returning a handle. Validation covers
the magic, version, language, exact section sizes, checksum, reserved fields,
all string offsets and terminators, contiguous block and record ranges, record
kinds, and strict byte ordering of canonical lemma keys. A failed validation
never exposes a partial handle.

Lookup is a binary search over canonical keys. Successful lookups return
zero-copy block and record views whose strings remain valid until the reader is
closed. The reader has no mutable lookup state, so one validated handle can be
shared by concurrent read-only callers. Lemma canonicalisation and public
generation results deliberately remain outside this format-level component.

## Licensing boundary

The builder and this format specification are independently written project
infrastructure under AGPL-3.0-or-later. An emitted index is derived from its
ordered stem-source inputs and retains their applicable data licensing and
provenance; running the AGPL builder does not relicense that data.
