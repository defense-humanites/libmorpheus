<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Open decisions on the Latin verbal candidate

After the [eleven-stage combination](latin-combined-candidate.md) the
controlled rebuilt baseline still recognizes **5,413 LISTALL forms** that
the candidate does not, and the
[residual loss attribution](latin-residual-loss-attribution.md) sizes each
of the open questions. None of them is a recipe in the sense used so far: a
rule proven from the source header and the historical lexer, applied to
blocks whose records are the lexer's own output. Each needs a choice about
what the candidate is allowed to contain. This page states the choices,
what each would cost or recover, and what a bounded tool could still do
within each once the choice is made. Lemma names appear only as examples.

## 1. Changed-definition dossiers — 2,249 lost forms, 39 lemmas

These are the 59 lemmas whose candidate block differs from the witness
block and whose source header the
[source review](latin-loss-source-review.md) read without finding a
recipe; the attachment repairs recovered 318 of their lost forms between the
six-stage and the eleven-stage combinations, and 2,327 of their removed
readings on recognized forms stay unmatched (1,396 duplicates). What
remains is the set of records the witness carries and the source does not
support as written: hand-corrected principal parts, alternates the article
mentions in prose, compounds the lexer cannot derive.

The choice: admit the witness records of a dossier when the article's prose
supports them (a per-dossier reading, 39 lemmas), admit none (the current
state), or admit all (the witness wins). A bounded tool can carry the first
option only lemma by lemma, with the quoted article passage as the proof,
along the lines of the quotation proof of the
[backlinked presents](latin-backlinked-present-classes.md).

## 2. Native preverb compositions — 1,553 lost forms, 40 lemmas

The engine composes any preverb of its table with any indexed stem and
reports the lemma as `preverb-lemma`; `vbs.cmp.ml` maps some of those
names to articles. The baseline recognized 1,137 forms through compositions
(33 lemma names) and 416 through mapped compositions (7 names) that the
candidate's stems no longer support — including compositions on stems the
repairs withdrew because they were wrong (the 14 forms lost between nine
and eleven stages, *coetus* read as a supine of `co-` with a defective stem
of *expleo*). The readings are compositions, not articles: no source header
describes them.

The choice is a policy on composition, not a lexical one: whether the
candidate should carry explicit blocks for compositions the witness
recognized (which would mean inventing headers), whether `vbs.cmp.ml`
should keep mapping names whose base article the candidate lacks, and
whether a form recognized only through a composition on a withdrawn stem
counts as a loss at all. The attribution tool already separates the three
cases by count.

## 3. Vowel-initial principal parts — 591 lost forms, 8 lemmas (7 with losses)

`is_spectype()` refuses any written part that begins with a vowel, so the
lexer emits no block at all for these headers; the witness wrote the blocks
by hand. The eight headers have four shapes:

| Shape | Lemmas | What the witness did | A bounded rule? |
| --- | ---: | --- | --- |
| Vowel-initial perfect or supine on a consonant root (`i^di, i^tum, 3` for *abdo*; `eptus, 3` for *adipiscor*; `i_tum, 3` for *ascisco*; `ole_vi, e_tum, 3` for *exolesco*) | 4 | appended the part to the stem (*abdo*), or replaced the root from its vowel (*adept*); one block is itself defective (`a-scisps`, `a-scispt`) | yes: the historical anchor rule applied to the vowel inside the root (last occurrence of the part's vowel in the root, else the root's first vowel, else the whole stem) reproduces the three correct witness blocks and the fourth block's intent; the present stem follows the lemma stripping the lexer already applies |
| Regular first conjugation with a spelling or an extra infinitive field (`a^vi, a_tum, 1`; `a_vi, a_tum, a_re, 1`) | 2 | `are_vb` | yes: the `conj1` filter's own regular shape, with the breve or the infinitive field disregarded |
| `-icio` compound written with an infinitive field first (`e^re, je_ci, jectum, 3`) | 1 | `abje_c`, `abject` | yes, with the `-jicio` rule already used for duplicate components |
| Alternative perfects joined by `and` (`i_vi, and ii, i_tum, 4`) | 1 | `ire_vb` derivative | the `or` alternative the lexer reads, with `and` accepted as its synonym |

A recipe here creates whole blocks from headers the lexer refused rather
than repairing blocks it produced. That is the decision: whether the
candidate may contain blocks the historical filter never emitted, provided
each comes from a header shape named in advance and from the lexer's own
stem derivation. If yes, one tool covers the four shapes (eight lemmas).

## 4. Curated lemmas without definition — 1,168 lost forms, 23 lemmas

| Category | Lost forms | Lemmas | Source situation | Choice |
| --- | ---: | ---: | --- | --- |
| Deponent article for an active lemma | 403 | 9 | the article is deponent (*hortor*), the witness also lists the active lemma (*horto*) | lemma identity: whether active forms of a deponent article deserve a lemma of their own; every form is recognized under the deponent article, with a passive voice |
| No inflection field | 288 | 4 of 7 | the article gives no principal parts | admission without source support, or an infinitive/part the sense text quotes (a quotation proof) |
| Other grammar string | 247 | 3 of 8 | digit-less strings the lexer skips (`se^cu_tus`, `na_tus, nasci`, `a_tus sum`, `a_ri, a_tus`, `la_bi`) | a bounded rule is possible: the class from the headword ending and the infinitive or supine written, as the lexer does for `a_re`/`a_ri`; it needs the decision of question 3 |
| Several inflection fields, not consecutive | 170 | 2 of 4 | editorial notes between fields (`others except Halm`), split parts (`i^lu^i` then `ultum, 4`) | per-header reading; two lemmas |
| No projected header | 31 | 3 of 15 | the witness lemma has no article at all (variant spellings, late forms) | admission without source support |
| Bare infinitive | 29 | 2 | `ecferre`, `are` | the second is the regular `are` derivative; the first an irregular compound |

Three of these categories (voice variants, lemmas without article, lemmas
without parts) are the lemma-identity and admission policies the
[witness backlog screen](latin-witness-backlog-screen.md) isolated; the
other three can be reached by bounded rules once the policy of question 3
is settled. The alternate spellings and homograph numberings of the same
screen cost no form.

## 5. Beyond the verbal candidate

The remaining 73 unmatched readings on recognized forms are non-verbal
(participles and nouns of verbal blocks, 68) or belong to lemmas none of the
four verbal inputs nor `vbs.cmp.ml` carries (5). The nominal side of the
reconstruction, `vtags`, the irregular paradigms (*subsum* without a
subjunctive) and the Hopper oracles have not been started, and no
production promotion is proposed until the questions above are settled.

## What a decision would start

| Decision | Tool to write | Expected effect |
| --- | --- | --- |
| 3 (blocks from refused headers), yes | one recipe for the four vowel-initial shapes | up to 591 forms, 8 lemmas, one LISTALL run |
| 4, digit-less grammars and split fields, yes | one recipe for the eight digit-less strings and the two split headers | up to 417 forms, 5 lemmas, one run |
| 1, per-dossier quotation proofs | a quotation-proof tool over the 39 dossiers | per lemma, measured on each |
| 4, voice variants | a policy in `vbs.cmp.ml` or a lemma-identity rule | 403 forms become recognized under their own lemma, or stay under the article |
| 2, compositions | a policy on `vbs.cmp.ml` and on losses through withdrawn stems | redefines what the 1,553 forms count as |
