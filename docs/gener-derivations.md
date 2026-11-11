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
supported preparer likewise rejects them with source locations. It does not
silently split commas, substitute similarly named types, or reinterpret an
unreferenced rule file. All seven are now corrected by reviewed data patches,
one line each, with their evidence and an upstream report:
[gener-data-patches.md](gener-data-patches.md).

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
  block (ποιέω: poetic `po-` and `poi-`) both receive them. The present a
  group receives because it requests nothing is such a default too: it covers
  nothing, and another group of the lemma still gets its own present
  (μελιτόομαι keeps `meli^t-` beside `melitt-`).
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

Over the 49 corpus sources, the defaults grow the index from 129,097 to
172,750 records: 8,786 lemmas gain forms, and five lemmas whose only request
is a listed zero request (ἀγαπάω: `;ao epic unaugmented`) enter the index.
The other lemmas are unchanged, no form is removed, and no added record fails
at generation: over the whole index, `morpheus_generate()` skips the same 346
records as before. Generated forms grow from 12.5 to 22.1 million.

Measured on the final index (`e04d4a7d…`, with the data patches and the
[corrected stem alterations](#corrected-stem-alterations)), the 99th
percentile of a `morpheus_generate()` request is 9.1 to 9.6 ms across runs,
against 5.2 ms with the historical index, and the median 0.13 to 0.14 ms,
against 0.12 ms; the first request of a context takes 31 to 43 ms with either
index (2-vCPU Linux sandbox, indicative). The round trip depends on the
sample: 120 changed lemmas drawn with seed 78 gave from 86.3 % to 93.2 % of
added forms recognized, depending on which lemmas the seed drew. On 400
changed lemmas (seed 78), 97.3 % of the added forms analyze back to their
lemma with the same tense and mood, against 98.1 % of the forms these lemmas
generated before; without the stem corrections, the same lemmas give 93.6 %.
The rest includes compound-only verbs (`comp_only`: δημέω, μηλόω,
κιδαρόω…), which analysis rejects as simple words, their historical forms
included.

The rule follows the sources and does not correct them. ἀγγέλλω has
explicit, unrestricted `:vs:a)ggel aor2` and `aor2_pass` records, so it
keeps ἤγγελον and ἠγγέλην as its only aorists and does not receive ἤγγειλα
or ἠγγέλθην. ἔχω's present came from one of the seven invalid derivations
above; the data patches now restore it.

`tools/gener-default-parts-report.py` measures the effect of the defaults
on two indices built from the same sources: lemmas, forms, skipped records
and latency of each index, lemmas that change, lose forms or gain skipped
records, a round trip of a seeded sample of changed lemmas through analysis,
and the forms added or removed for a list of frequent verbs. A round trip
measures parity with analysis, which accepts more than a paradigm should
show; it does not prove that an added form exists. The reviewed verbs are
therefore checked in CI: the corpus test requires that πάσχω, πίπτω, ὁράω,
μένω, ἵστημι, βούλομαι, λύω and ἀκούω keep their historical blocks, that
ποιέω, δηλόω, ἀγγέλλω and ἀγαπάω receive exactly their reviewed records, and
that ἔχω receives exactly the four records of its patched present.

`--requested-parts-only` keeps the historical behavior. It is an option of
the preparer, used by the oracle comparison and by the benchmark; the data
package and `tools/prepare-runtime-data.sh` always prepare the default index.
The corpus test checks that the option still reproduces the index of data
0.1.0 and native 0.4.6 (`5aa76d8c…`). `test/gener-derivation-defaults.txt`
and its expected records exercise each rule above.

## Corrected stem alterations

The historical expansion alters some stems in two ways, and the default
principal parts would have extended both to many more lemmas. The default
expansion corrects them, in explicit requests as in defaults; the historical
one (`--requested-parts-only`) keeps them, so that it still reproduces
`5aa76d8c…`.

- **Aspirate dissimilation** (`do_dissim`) turns an aspirate into the plain
  stop when the next syllable begins with another aspirate. That is right
  for a primary root such as θρεφ- (τρέφω, θρέψω), which the default
  expansion still dissimilates. It is wrong in two cases, which the default
  expansion leaves alone:
  - a regular (`reg_deriv`) derivation, whose stem is the stem of a noun or
    adjective with its aspirates: ἰχθυοφορέω, θεοφορέω, ψηφοφορέω, which the
    historical expansion gave as ἰκθυοφορ-, τεοφορ-, ψηποφορ-;
  - an aorist passive stem ending in its own aspirate. `do_dissim` has an
    exception for it, added in 1989 (`a)riqmh/qhn not a)ritmh/qhn`), but the
    exception compares the principal part through the `VERBSTEM` bit
    instead of `PPARTMASK`, so it never applies: ἀληθεύω gave ἠλητεύθην,
    αἰσθάνομαι ᾐστήθην, ἄχθομαι ἠκθέσθην.

  1,627 records in 1,210 lemmas change, 86 of which were already in the
  historical index. The Alpheios analysis index, built with the same code,
  still holds the dissimilated presents (`i)kquofor`), beside the
  derivation stems it analyzes the other tenses with.
- **Consonant euphony** (`rule_files/conseuph.table`) takes the leftmost
  pattern of the word, so a σσ or νσ inside a stem was simplified as if it
  met the suffix: γλωσσοχαριτέω gave γλωσοχαριτήσω, παλινστατέω
  παλιστατήσω. The default expansion applies only a pattern that reaches the
  junction of the stem and its suffix. 222 records in 46 lemmas change, 8 of
  which were in the historical index. Among them are the ἐκθ- and ἐκσ-
  compounds (ἐκθαμβέω, not ἐχθαμβ-; ἐκσηπόω, not ἐξηπ-) and two lemmas
  whose initial digamma the table dropped (ϝοιζάζω, ϝρητάομαι).

Over the Alpheios index, 1,249 lemmas change forms. None gains or loses a
form: the index keeps 106,428 lemmas and 172,766 records, and generation
22.05 million forms with the same 346 skipped records. On 300 of the changed
lemmas (seed 78), the share of added forms that analyze back to their lemma
with the same tense and mood rises from 69.3 % to 96.2 %.
`test/gener-derivation-defaults.txt` holds a case for each correction, and
the preparer's test checks that the historical expansion keeps both
alterations.

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
