<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Greek generation derivations

This document fixes the inputs and reference behavior for expanding `:de:`,
`;`, and their `@` continuations before construction of the generation index.
The runtime library will consume only the resulting explicit `:vs:`, `:aj:`,
and `:no:` records.

## Pinned rule corpus

The rule corpus comes from Alpheios commit
`4632415fe93c85e9fdca47a0c5a13f31385f0023`. Its checksummed manifest is
`tools/gener-derivation-manifest.tsv` and contains:

- the ordered `rule_files/derivtypes.table` registry;
- 38 unique rule files referenced by its 39 entries;
- five source rule files present on disk but absent from the registry:
  `cw`, `es_denom`, `ow_fact`, `ow_instr`, and `ww`.

The difference is historical, not an inference by this project. The registry
declares `illw` twice, with numeric values `037` and `041`. CI preserves both
the duplicate declaration and the complete set of unreferenced files so that a
future upstream correction cannot silently change generation behavior.

## Differential oracle

`test/gener-derivation-source.txt` exercises:

- explicit present, future, and aorist principal-part requests;
- a continuation of a principal-part request;
- a regular derivation with no explicit principal part;
- an attached suffix request;
- a preverb;
- present reduplication.

It was passed to the pinned Alpheios `do_conj` executable in `full` mode after
building the pinned derivation tables. Control lines were then removed, leaving
only lemma and active generation records in
`test/gener-derivation-oracle.expected`.

`full` mode is the relevant oracle for generation. The historical short mode
is an analysis-index optimization: it suppresses records considered redundant
and can leave regular `:de:` controls active for later analysis tooling. Such
controls are not accepted by the generation index.

The supported preparer matches the oracle's record semantics and stable order;
it does not reproduce diagnostic text, disabled `-` control lines, blank-line
placement, or file-scope state.

## Invalid source records

Seven `:de:` records in the frozen generation corpus do not name one of the 38
active derivation types under the historical parser:

| Source | Line | Parsed derivation type | Problem |
| --- | ---: | --- | --- |
| `stemsrc/nom.proper` | 7,941 | `as_a` | No registered rule. |
| `stemsrc/vbs.simp.ml` | 3,928 | `e_stem,epic` | Comma is attached to the type token. |
| `stemsrc/vbs.simp.ml` | 6,272 | `ew` | No registered rule. |
| `stemsrc/vbs.simp.ml` | 9,214 | `reg_conj,syll_aug` | Comma is attached to the type token. |
| `stemsrc/vbs.simp.ml` | 15,142 | `melitt` | Space after `:de:` leaves the stem empty and shifts the tokens. |
| `stemsrc/vbs.simp.ml` | 22,130 | `w_stem` | Stem type used where a derivation type is required. |
| `stemsrc/vbs.simp.ml` | 25,428 | `numi,poetic` | Comma is attached to the type token. |

The historical program reports missing rule files for these records. The
supported preparer must likewise reject them with source locations. It must not
silently split commas, substitute similarly named types, or reinterpret an
unreferenced rule file. Any correction belongs in a separately reviewed data
patch with its own provenance and differential evidence.

## Default principal parts

The `full` oracle emits only the principal parts that a `:de:` group requests
with `;`, or the present alone when it requests none. Analysis does not read
the sources that way: its index keeps a regular derivation as a whole
(`steminds/vbind` stores `:dhlo/w:ow_denom` for δηλόω), so it accepts every
principal part the derivation type defines, and the `;` requests only add
variants. Generation therefore missed forms that analysis recognizes (#78):
ποιέω had no active or middle aorist, δηλόω no aorist, perfect or aorist
passive, ἀγγέλλω no regular future, and 3,423 of the 5,335 valid groups of
`vbs.simp.ml` generated their present only.

By default, the preparer now completes regular derivations. At the end of
each lemma block, each of its regular `:de:` groups receives the record that
a bare `;pr`, `;fu`, `;ao`, `;pf`, `;pp` or `;ap` request would produce, for
every principal part that the lemma does not already cover:

- Only regular derivations receive defaults: the `reg_deriv` class of
  `rule_files/derivtypes.table` (`ew_denom`, `ow_denom`, `aw_denom`, `izw`,
  `ellw`...). A primary conjugation (`reg_conj`, class `prim_deriv`) or a
  verb stem class (`e_suppl`, `skw`, `o_stem`..., class `verbstem`) describes
  a stem whose parts its requests enumerate. Completing it would build
  ἔχω's future stem `e(k` and aorist stem `sx` into presents, or give πάσχω,
  πίπτω and μένω an aorist passive. Such groups keep the historical
  expansion: their requests, or the present alone.
- A part is covered by any `:vs:` record of the lemma, explicit or derived,
  whose keys fix no dialect, tense or mood. A voice, a suffix or a stem type
  does not lift the coverage: `;fu mid` says that a future exists in the
  middle only, `;ap,-hq` chooses a suffix, and an explicit `:vs:` perfect
  supplies its perfect. Flags such as `poetic`, `late` or `rare` are not
  dialects: a record carrying them covers its part too. A request limited to
  a dialect (`;fu epic ionic` for ἀγγέλλω) or to a tense (`;ap fut`, a future
  passive) does not cover its part, and the regular form is added beside it.
- Coverage is gathered over every block of a lemma key, whichever source
  file holds it: the preparer reads the sources twice, first to record
  which parts each block covers, then to add the defaults. A part one block
  covers is not added to another block of the same lemma. The parts covered
  are those of the sources, before any default is added, so two groups of one
  block (ποιέω: poetic `po-` and `poi-`) both receive them.
- A group whose `:de:` keys fix a tense or mood is confined to its requests:
  `:de:a)rx euw pres` records a verb attested in the present only. So is a
  group with a present formation (`pres_redupl`, `n_infix`), which the
  expansion would otherwise apply to every part it builds.
- A voice on the `:de:` line keeps the parts that can carry it: an active
  group gets no perfect middle-passive or aorist passive, a middle group no
  aorist passive, and a passive group no future or aorist built on the
  active stems.
- The future perfect is not added: it is rare and lexically restricted, and
  the sources request it where it exists (λύω: `;fp mid`).
- A part the derivation table does not define for the group's keys yields
  nothing, and a record identical to one of the block's is not repeated.

Over the 49 corpus sources, the index grows from 129,097 to 172,741 records:
8,786 lemmas gain forms, and five lemmas whose only request is a listed
zero request (ἀγαπάω: `;ao epic unaugmented`) enter the index. The other
lemmas are unchanged, no form is removed, and no added record fails at
generation: over the whole index, `morpheus_generate()` skips the same 346
records as before. Generated forms grow from 12.5 to 22.0 million.

The rule follows the sources and does not correct them. ἀγγέλλω has
explicit, unrestricted `:vs:a)ggel aor2` and `aor2_pass` records, so it
keeps ἤγγελον and ἠγγέλην as its only aorists and does not receive ἤγγειλα
or ἠγγέλθην. The seven invalid derivations above, ἔχω's present among them,
stay rejected until a reviewed data patch corrects them.

`tools/gener-default-parts-report.py` measures the effect of the defaults
on two indices built from the same sources: lemmas, forms, skipped records
and latency of each index, lemmas that change, lose forms or gain skipped
records, a round trip of a seeded sample of changed lemmas through analysis,
and the forms added or removed for a list of frequent verbs. A round trip
measures parity with analysis, which accepts more than a paradigm should
show; it does not prove that an added form exists. The reviewed verbs are
therefore checked in CI: the corpus test requires that ἔχω, πάσχω, πίπτω,
ὁράω, μένω, ἵστημι, βούλομαι, λύω and ἀκούω keep their historical blocks, and
that ποιέω, δηλόω, ἀγγέλλω and ἀγαπάω receive exactly their reviewed records.

`--requested-parts-only` keeps the historical behavior. It is an option of
the preparer, used by the oracle comparison and by the benchmark; the data
package and `tools/prepare-runtime-data.sh` always prepare the default index.
The corpus test checks that the option still reproduces the index of data
0.1.0 and native 0.4.6 (`5aa76d8c…`). `test/gener-derivation-defaults.txt`
and its expected records exercise each rule above.

## Implementation boundary

The legacy `conjsys.c` and `combconj.c` front ends use file-scope mutable
buffers and can create diagnostic side files. They remain provenance and oracle
code, not runtime dependencies. `src/gener/derivation.c` provides the internal
MPL boundary used by the offline preparer: its request state is call-local, its
storage is bounded and owned, and it reads the normalized ASCII rule tables
already distributed in `stemlib/Greek/derivs/ascii`. The preparer emits only
explicit generation records; the runtime library does not load derivation
rules.

`test/gener-source-preparer.cmake` compares the supported output byte for byte
with the frozen `full` oracle. It also requires an unknown derivation type to
fail without leaving a partial output file.
