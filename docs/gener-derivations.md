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

By default, the preparer completes regular derivations as analysis reads
them. At the end of each lemma block, each of its regular `:de:` groups
receives the record that a bare `;pr`, `;fu`, `;ao`, `;pf`, `;pp`, `;ap` or
`;fp mp` request would produce:

- Only regular derivations receive defaults: the `reg_deriv` class of
  `rule_files/derivtypes.table` (`ew_denom`, `ow_denom`, `aw_denom`, `izw`,
  `ellw`...). A primary conjugation (`reg_conj`, class `prim_deriv`) or a
  verb stem class (`e_suppl`, `skw`, `o_stem`..., class `verbstem`) describes
  a stem whose parts its requests enumerate. Completing it would build
  ἔχω's future stem `e(k` and aorist stem `sx` into presents, or give πάσχω,
  πίπτω and μένω an aorist passive. Such groups keep the historical
  expansion: their requests, or the present alone.
- The lemma's other records do not replace a part. Analysis keeps each
  regular derivation beside them: 9,518 of the corpus's 9,522 regular groups
  have their own entry in `steminds/vbind`, and analysis accepts ἤγγειλα and
  ἠγγέλθην for ἀγγέλλω beside its explicit second aorists ἤγγελον and
  ἠγγέλην. A requested part with a voice (`;fu mid`), a suffix (`;ap,-hq`)
  or a dialect (`;fu epic ionic`) keeps its record, and the group also
  receives the regular one.
- A group whose `:de:` keys fix a tense or mood is confined to its requests:
  `:de:a)rx euw pres` records a verb attested in the present only. So is a
  group with a present formation (`pres_redupl`, `n_infix`), which the
  expansion would otherwise apply to every part it builds.
- A voice on the `:de:` line keeps the parts that can carry it: an active
  group gets no perfect middle-passive, aorist passive or future perfect, a
  middle group no aorist passive, and a passive group no future or aorist
  built on the active stems.
- The future perfect is requested in the middle-passive, where analysis
  accepts it for every regular derivation (πεποιήσομαι, δεδηλώσομαι).
- A part the derivation table does not define for the group's keys yields
  nothing, and a record identical to one of the block's is not repeated.

A first version of this rule added a part only where no record of the lemma
covered it, and left the future perfect out. Its paradigms looked more like a
grammar's, but it missed forms that analysis accepts: ἀγγέλλω kept ἤγγελον
and ἠγγέλην as its only aorists, without the Attic ἤγγειλα and ἠγγέλθην.
Generation now follows its
[contract](public-api.md#greek-lemma-generation): the forms that analysis
accepts.

The rule does not give a voice to a deponent whose `:de:` line names none
(`:de:a)sp azw` under ἀσπάζομαι, `:de:log izw` under λογίζομαι). Such a group
receives active parts: ἀσπάσω, ἐλόγισα, ἠγώνικα. Analysis accepts these
forms, because its derivation entry names no voice either, so generation
returns them too. Correcting them belongs to the data, for analysis and
generation together (#84).

ἔχω's present came from one of the seven invalid derivations above; the data
patches restore it.

### Compound-only records

The default preparation moves the records whose keys include `comp_only` to
a block of their own, under the lemma prefixed with a hyphen: `-dhme/w`
holds the stems of δημέω. Their stem occurs only after a preverb, and
analysis accepts their forms only then (`checkgenwds.c`, `retrends.c`): it
rejects δημήσω, but analyzes ἀποδημήσω under ἀποδημέω. The simple lemma does
not generate them, and no request can name the reserved key, since requests
are canonicalised without hyphens. The runtime reads it only to compose a
[compound verb](public-api.md#compound-verbs): ἀποδημέω and ἐπιδημέω from
`-dhme/w`.

2,883 records move, in 509 lemmas (2,849 in the index, where identical
blocks merge). A type token may join the key with a comma
(`:vs:di^k aor2,comp_only` under δικεῖν), which the preparation of data
0.2.0 missed. Among them are compound stems listed under a simple lemma:
`:aj:a)ndr os_on comp_only` under ἀνήρ, for -ανδρος, or
`:aj:trem hs_es` under τρέμω, for -τρεμής. Generation declined them as forms
of the verb; compounds take only verb records, so they stay unused. 349
lemmas keep no other record, such as δημέω and ἀγγίζω: generating them
returns nothing, as analysis attributes nothing to them.

### Measures

Over the 49 corpus sources, the default preparation gives 177,672 records in
106,080 lemmas, against 129,097 records in 106,422 lemmas for the historical
one, and keeps 2,849 compound-only records under 509 reserved keys: 349 of
these lemmas have no other record, 160 keep their others.

The index of data 0.2.0 (`a2f97677…`), which dropped the compound-only
records, already differed from the historical one as follows. 8,511 lemmas
gained forms; six entered the index, five whose only request is a listed
zero request (ἀγαπάω: `;ao epic unaugmented`) and βεβόλημαι, restored by a
data patch; 347 compound-only lemmas left it, and 105 lemmas lost their
compound-only forms. No added record failed at generation: over the whole
index, `morpheus_generate()` skipped 339 records, the historical 346 less
seven compound-only ones. Generated forms grew from 12.5 to 22.1 million.

Generating compounds then changes 326 lemmas of that index. 311 compounds
that have an entry of their own also receive their simple verb's records,
0.77 million forms (ἀφίημι, ἀναβάλλω, ἀνέχω), and 15 of them inherit 19
skipped records. 13 lemmas lose records that carry a preverb of their own,
which analysis attributes to a compound: ἀμπέσχον leaves ἔχω for ἀμπέχω, and
the `pb:e)pi/` stems of μελέομαι, θηδεύω and κουρέω go to ἐπιμελέομαι,
ἐπιτηδεύω and ἐπικουρέω. δικεῖν and κιάθω each lose two compound-only
records whose key a comma joins to the stem type (`aor2,comp_only`);
κιάθω, left with none, leaves the index. Over the whole index,
`morpheus_generate()` now skips 358 records in 285 lemmas and returns 22.8
million forms; the 19,130 listed compounds that generate return 43.7 million
more. On the 326 changed lemmas, 99.85 % of the 659,984 generated surfaces
analyze back to their lemma with the same tense and mood, against 95.38 % of
their 126,133 surfaces before.

The round trip measures the first property of the generation contract. On
400 lemmas that changed since the historical index (seed 78), 99.99 % of the
added forms analyze back to their lemma with the same tense and mood, and
99.8 % of the forms these lemmas generated before. On 300 of the 6,543
lemmas that completing derivations and adding the future perfect enrich
(seed 78), 99.5 % of the added forms do. Samples of this size are stable:
with 120 lemmas, the share varied from 86 % to 93 % with the draw, because
of compound-only lemmas and the stem alterations corrected below. The 99th
percentile of a `morpheus_generate()` request is 9 to 10 ms, against 5.2 ms
with the historical index, and the median 0.13 ms, against 0.12 ms; the
first request of a context takes 31 to 44 ms with either index (2-vCPU Linux
sandbox, indicative). Generating compounds leaves these figures within noise
for the index's own lemmas (median 0.11 ms, 99th percentile 10 to 12 ms on
5,000 lemmas), but adds 10 to 25 ms to the first request of a context, which
loads the compound list. A listed compound takes 12 ms at the median and 52
to 64 ms at the 99th percentile (1,000 compounds, seed 78): it is a whole
verb paradigm. Its preverb variants bring the listed compounds from 43.7 to
58.3 million forms; the skipped records are unchanged, since the variants
reuse the records of the plain forms. The largest, ὑποβοηθέω, returned
31,526 records, and 3,593 compounds exceeded the 4,096 records that were the
default limit before 0.6.0 (2,950 once dialects are intersected, below).
Each variant generates the simple verb's records again: measured in one
session, a compound takes 17 ms at the median and 89 to 95 ms at the 99th
percentile, against 8 ms and 33 to 40 ms with
`MORPHEUS_GENERATION_EXCLUDE_PREVERB_VARIANTS`. The first compound of a
context also reads `rule_files/raw_preverbs.table`.

A form takes the dialects that its preverb, augment, stem and ending all
allow, and a form whose parts share none is left out unless its record
forces the ending ([public-api.md](public-api.md#greek-lemma-generation)).
This takes the whole index from 23.1 to 22.3 million forms (−3.4 %): 4,550
lemmas lose forms and 16,011 change, most in their labels only; none is
emptied. The listed compounds go from 58.3 to 53.8 million forms (−7.6 %,
10,882 compounds lose forms, none is emptied); the largest is now
προσκρεμάννυμι, with 26,774 records, and ὑποβοηθέω returns 23,226. On the
treebank, 0.24 % of the noun, adjective, pronoun and verb tokens lose a
reading, nearly all misreadings of analysis; a few are real forms, such as
the lyric ἁλίοιο (a Doric stem with an epic ending). On 2,787 lemmas (the
800 most frequent in the treebank and 2,000 drawn with seed 78), the forms
labelled with a dialect that analysis does not give them fall from 1.5 % to
1.0 %.

The unaugmented indicatives that analysis accepts for every verb
([public-api.md](public-api.md#greek-lemma-generation)) come from a last
pass over the verb stems, alone and with each preverb variant. They take the
whole index from 22.3 to 23.1 million forms (+3.5 %, 9,390 lemmas) and the
listed compounds from 53.8 to 56.4 million (+4.8 %); 3,185 compounds then
exceed 4,096 records, and προσκρεμάννυμι returns 28,200. The forms are
labelled as analysis labels them, so that on the 2,787 lemmas above, the
records labelled with a dialect that analysis does not give them stay at
1.0 % (1,006,223 records). On 246 frequent verbs, 99.52 % of the 13,902
surfaces they add analyze back with the same tense and mood, and 99.89 % of
the 22,118 they add to the 300 compounds of the round trip above. The pass
generates each verb stem again: measured in one session, the 99th percentile
of an index lemma goes from 9.5 to 19 ms, and a compound takes 39 ms at the
median and 218 ms at the 99th percentile, against 23 ms and 124 ms before.

`tools/gener-default-parts-report.py` measures the effect of the defaults
on two indices built from the same sources: lemmas, forms, skipped records
and latency of each index, lemmas that change, lose forms or gain skipped
records, a round trip of a seeded sample of changed lemmas through analysis,
and the forms added or removed for a list of frequent verbs. The round trip
measures the first property of the generation contract; it does not tell
whether a text attests a form. The reviewed verbs are also checked in CI:
the corpus test requires that πάσχω, πίπτω, ὁράω, μένω, βούλομαι, λύω and
ἀκούω keep their historical blocks less their compound-only records, that
ποιέω, δηλόω, ἀγγέλλω, ἀγαπάω and ἵστημι (through its regular group ἱστάω)
receive exactly their reviewed records, and that ἔχω receives exactly the
four records of its patched present.

`--historical` reproduces the historical preparation: no default principal
parts, the compound-only records, the
[stem alterations](#corrected-stem-alterations) of the historical expansion,
and no [data patches](gener-data-patches.md). It is an option of
the preparer, used by the oracle comparison and by the benchmark; the data
package and `tools/prepare-runtime-data.sh` always prepare the default index.
The corpus test checks that the option still reproduces the index of data
0.1.0 and native 0.4.6 (`5aa76d8c…`). `test/gener-derivation-defaults.txt`
and its expected records exercise each rule above.

## Corrected stem alterations

The historical expansion alters some stems in two ways, and the default
principal parts would have extended both to many more lemmas. The default
expansion corrects them, in explicit requests as in defaults; the historical
one (`--historical`) keeps them, so that it still reproduces `5aa76d8c…`.

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

The correction follows the derivation class, not the history of each root,
which the tables do not record. A few regular verbs in `ptw` and `ss` have
two aspirates in the root itself, whose perfect active the historical rule
dissimilated as the root requires: θάπτω (θαφ-), θρύπτω (θρυφ-) and θράσσω
(θραχ-) now get τέθαφα, τέθρυφα and τέθραχα instead of τέταφα, τέτρυφα and
τέτραχα (Homer's τετρήχει, under ταράσσω). These perfects are added by
default, and the Cambridge Greek Lexicon gives θάπτω none. The historical
rule gave the wrong form wherever the table's aspirate is only that of the
perfect, which the correction now gets right: φράσσω πέφραχα, φρύγω
πέφρυχα, ἀφάσσω ἤφαχα, θώπτω τέθωφα, not πέπραχα, πέπρυχα, ἤπαχα, τέτωφα.

Over the Alpheios index, the correction changes the forms of 1,249 lemmas
and adds or removes none. On 300 of these lemmas (seed 78), the share of
added forms that analyze back to their lemma with the same tense and mood
rises from 69.3 % to 96.2 %.
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
