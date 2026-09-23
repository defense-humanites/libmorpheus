<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Runtime stemlib binary contract

The runtime reads the precompiled Alpheios stemlib as a historical
little-endian format. It does not serialize native pointers, `long`, or whole
runtime structures.

## Ending tables

An ending-table file begins with two unsigned 32-bit little-endian words:

1. format version (`44440001`);
2. fixed ending-string width.

Each following record contains, in order:

| Field | Bytes | Encoding |
|---|---:|---|
| ending | header-defined | raw bytes, NUL padded |
| word form | 4 | explicitly packed bit fields |
| dialect | 2 | unsigned little-endian |
| geographic region | 4 | unsigned little-endian |
| stem type | 4 | unsigned little-endian |
| derivation type | 4 | unsigned little-endian |
| morphology flags | 12 | raw 96-bit compatibility field |
| domains | 21 | NUL-terminated legacy byte field |

The word-form bits are voice 0–2, mood 3–6, tense 7–10, person 11–13,
number 14–16, case 17–22, degree 23–24, and gender 25–28. Packing and
unpacking are explicit; the file no longer depends on the compiler's native C
bit-field order.

Internal morphology flags occupy 14 bytes, but the ending-table disk field
remains 12 bytes to preserve existing stemlibs. An `is_group` ending record
encodes flag 110 as bit `040` in domain byte 1 while domain byte 0 is NUL. The
reader converts that marker to the in-memory flag and clears it from the domain
field. The writer performs the inverse conversion and rejects a group record
that also contains domains because that combination has no unambiguous legacy
encoding.

The Alpheios `stemsrc` files also contain `is_group` stem annotations. Its
distributed precompiled text indexes omit those annotations, so the runtime
cannot recover them from `steminds/nomind`. Preserving that classification in
public analyses requires rebuilding the stem indexes with an extended format;
it must not be inferred from lemma spelling or plurality.

## Portability guards

The `stemlib_abi` test requires 8-bit bytes and the exact widths of every
remaining scalar disk field. `stemlib_io` verifies the header, explicit
word-form bytes, normal and group-record round trips, truncated reads, and
record-size calculations. These tests run on native Linux, Alpine/musl and
Apple Silicon CI targets.

The complete production qualification additionally decodes all 229 regenerated
`.out` files whose bytes differ from the checked-in Perseids snapshots. It
compares every semantic field of every record and emits a deterministic report.
There are 228 semantically identical files. Morphology keys with duplicate rule
registry names resolve deterministically to the last registered definition,
which matches the checked-in `illw.out` value. The remaining twelve
`er_eris.out` records use the same duplicated symbolic name and class but a
different numeric ID; this single historical exception is pinned separately.
Any other semantic change fails qualification.
