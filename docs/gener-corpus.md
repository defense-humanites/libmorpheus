<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Greek generation corpus

This document freezes the source universe from which the first complete Greek
generation index will be prepared. It records selection and provenance; it does
not make the raw stem sources a runtime dependency.

## Pinned source

The manifest targets the Alpheios submodule commit
`4632415fe93c85e9fdca47a0c5a13f31385f0023`. Every selected path and its
SHA-256 digest is recorded in `tools/gener-corpus-manifest.tsv`. CI recomputes
all digests against `vendor/alpheios-morpheus/dist/stemlib/Greek` and rejects a
missing, additional, reordered, or modified historical build input.

The manifest contains 49 files in two provenance groups:

- 45 nominal-build inputs: the six `stemsrc/nom.*` files, the 37
  `stemsrc/nom[0-9]*` files, `stemsrc/lsj.nom`, and
  `stemsrc/lsj.byhand`;
- four verb-build inputs, in historical concatenation order:
  `stemsrc/vbs.irreg`, `stemsrc/vbs.simp.ml`,
  `stemsrc/vbs.simp.02.new`, and `stemsrc/lsj.vbs`.

The group labels describe the old Makefile paths, not the actual part of
speech. Three `:de:` verb derivations occur in nominal-build inputs, while the
verb-build inputs contain a small number of noun and adjective records. The
preparer must therefore process the ordered manifest as one heterogeneous
source universe.

## Transformation inventory

Before expansion, the pinned files contain:

| Source group | Lemma blocks | `:no:` | `:aj:` | `:vs:` | `:wd:` | `:vb:` | `:de:` | `;` | `@` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Nominal build | 98,651 | 74,875 | 26,178 | 1 | 6,487 | 0 | 3 | 0 | 1,109 |
| Verb build | 10,051 | 1 | 13 | 1,512 | 0 | 1,728 | 10,596 | 6,776 | 2,344 |

There are consequently two distinct offline transformations:

1. continuation expansion, which combines `@` constraints with the preceding
   regular or irregular base record;
2. derivation expansion, which resolves `:de:` plus its `;` and `@` requests
   through the pinned derivation tables and emits explicit `:vs:` records.

The first transformation is now implemented by the bounded offline source
preparer for active `:no:`, `:aj:`, `:vs:`, `:wd:`, and `:vb:` records. It
reproduces the historical rule precisely: retain the record tag, stem, and
first ASCII-key token, then append the text following `@`. Every continuation
is based on the preceding explicit record rather than on the preceding
continuation. State is reset at each lemma and input-file boundary, so malformed
input cannot inherit the old front end's file-scope buffer.

Of the 3,453 continuations in the pinned corpus, 2,011 follow an active explicit
generation record and 1,441 belong to a `:de:`/`;` derivation sequence. The one
remaining occurrence follows disabled `-:vs:` and `#:vs:` lines in the
`ghra/skw` block; it is deliberately rejected as orphaned instead of attaching
to an unrelated earlier record. The same preparer now expands the 1,441
derivation-associated continuations together with their `:de:` and `;`
requests.

The rule inputs and reference expansion behavior for that step are frozen in
[Greek generation derivations](gener-derivations.md). The historical registry
contains 39 entries for 38 unique active rule files, declares `illw` twice, and
leaves five rule files unreferenced. Seven source records also fail its own
derivation-type grammar. These cases are explicit validation errors pending a
separately justified data correction; the preparer rejects them and does not
guess repairs.

The historical `do_conj` output is useful as a differential oracle, but it is
not itself the normalized input contract: it preserves control records, marks
some of them with `-`, and uses global mutable buffers. The supported preparer
emits only lemma and explicit generation records accepted by the version 1
index builder.

## Qualified source exceptions

Running the complete ordered corpus through the pinned historical
`do_conj full` program exposes 88 control records for which that program emits no
generation record. Source-state analysis separates those records from the
previously identified grammar failures and disabled base:

| Category | Count | Meaning |
| --- | ---: | --- |
| `invalid_derivation` | 7 | `:de:` cannot name one active derivation rule under the historical grammar. |
| `invalid_record` | 3 | An explicit `:wd:`/`:no:` record has an empty stem because whitespace follows the prefix. |
| `orphan_request` | 15 | `;` follows an explicit record rather than an active `:de:` record. |
| `orphan_continuation` | 1 | `@` follows only disabled/commented base records. |
| `zero_request` | 55 | An attached `;` request makes `do_conj full` emit no record. |
| `zero_continuation` | 18 | An attached `@` request makes `do_conj full` emit no record. |

The 99 locations are frozen in `tools/gener-corpus-exceptions.tsv`. Each entry
records its category, source path, one-based line number, and the SHA-256 of
the trimmed source line. The file-level corpus manifest simultaneously pins
the complete source contents, so a line insertion, removal, or replacement
cannot silently preserve an exception at a stale location. CI enforces the
category counts, source order, selected paths, and uniqueness of locations.

These entries are observations, not corrections. The seven
`invalid_derivation` entries are corrected by the reviewed patches of
[gener-data-patches.md](gener-data-patches.md), which supersede them when the
preparer runs with `--patches`. The corpus preparer's explicit
exception-aware mode omits them only after verifying every path, line number,
category, and source-line fingerprint; it also rejects every unlisted failure
and any unmatched manifest entry. In particular, it preserves
successful derivations and explicit records in the same lemma block; excluding
an entire lemma because one request fails would discard qualified data.

## Qualified duplicate policy

The historical analysis build concatenates overlapping author files and LSJ
files before sorting and indexing. A generation lookup must avoid multiplying
identical paradigms while retaining genuinely distinct blocks for the same
lemma. Raw source identity is insufficient because continuations and
derivations change the semantic record set. Deduplication therefore occurs only
after expansion and canonicalisation. Two blocks are duplicates only when
their canonical lemma and complete ordered sequences of structured records are
identical. The first occurrence is retained; distinct blocks for the same key
and repeated records within one block are preserved.

The qualified corpus contains 108,785 non-empty blocks before this rule and
108,349 afterward, so 436 redundant blocks are removed. The resulting index
contains 106,589 canonical keys and 180,521 records: 106,080 lemmas with
177,672 records, and 509 reserved keys with the 2,849 records whose stems
occur only in compounds. CI prepares and indexes the 49 sources twice,
requires byte-for-byte reproducibility, and freezes the SHA-256 of both the
290,741-line prepared corpus (`a618d41c…`) and the final index
(`8ba328ca…`).

These figures include the default principal parts described in
[Greek generation derivations](gener-derivations.md#default-principal-parts),
the [compound-only records](gener-derivations.md#compound-only-records) under
their reserved keys, the seven [data patches](gener-data-patches.md) and the
[corrected stem alterations](gener-derivations.md#corrected-stem-alterations).
Prepared with `--historical`, which adds no default, keeps the compound-only
records under their lemma, applies no patch and keeps the historical expansion, the corpus
still gives the historical 238,250-line source (`1c14949b…`) and the index of
data 0.1.0 and native 0.4.6 (106,422 lemmas, 108,215 blocks, 129,097 records,
`5aa76d8c…`); CI checks both.

## Licensing

The manifest and any prepared corpus or index are derived from the pinned stem
sources and retain their applicable licensing and provenance. The independently
written validation and preparation code may be AGPL-3.0-or-later; executing it
does not relicense the data.
