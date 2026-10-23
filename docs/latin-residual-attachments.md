<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Residual attachment repairs

Qualified code: `56da80e`. The
[dedicated workflow run](https://github.com/defense-humanites/libmorpheus/actions/runs/39949297666)
succeeds with the full LISTALL diagnostic; the
[aggregate receipt](qualification/latin-residual-attachments-56da80e.json)
records counts, categories and SHA-256 values only.

After the [written-part anchor](latin-anchor-duplication.md) and
[sigmatic suffix](latin-sigmatic-suffix.md) repairs, a survey of every
single-itype header whose candidate block is exactly the historical output
found four small defect families left, each visible from the source header
and the `latvb` rule alone. One recipe repairs the four together.

## Historical defects and recipe

| Family | Historical rule | Defect | Repair |
| --- | --- | --- | --- |
| Vowel-anchored special parts | `spectypes[]` strings such as `e_mi, emptum, 3`, `exi, ectum, 3`, `e_vi, e_tum, 2` hand `truncstem()` their first letter, a vowel | absent from the root, nothing is cut (`a^d-i^me_m`); found in the preverb, the preverb itself is cut (`ex-i^mo` gives `e_m`, `de_-spi^ci^o` gives `dex`, `ex-ple^o` gives `e_v`) | a `conj2` stem, whose thematic vowel the lemma stripping removed, takes the part whole (`ex-ple_v`); any other class takes it from the root's last vowel (`ex-e_m`, `de_-spex`) |
| Doubled `u` | the literal `u^i` cases attach `u^` without trimming | a stem already ending in `u` is doubled (`congru^u^`, `co^-argu^u^`, `per-tri^bu^u^`) | the perfect stem is the present stem |
| Second conjugation read as third | the class-less `u^i` and `e^re` cases default to `conj3` | a headword in `-eo`, whose ending the lemma stripping removes, is given a third-conjugation present (`si^l conj3`) | `conj2` on the same stem |
| Suffix supine after a final consonant | a bare `psus`/`ctus` deponent supine goes through the generic rule | with its letter absent the suffix follows the final consonant (`illa_bps`, `prae-ve^hct`) | attached after the stem minus its final consonant (`illa_ps`, `prae-ve^ct`) |

`tools/repair-latin-residual-attachments.py` reads the lexer's literal table
and `spectypes[]`, proves each family from the single source `<itype>` and
the headword, requires the block's records to be exactly the historical
output and the present record to be single and unflagged, and leaves every
other shape alone: a vowel anchor found in the root, a `u^i` perfect on a
stem not ending in `u`, a suffix supine on a vowel-final stem (*perfruor*,
`per-fru^ct`, correct as it stands) or with its letter present in the stem,
and a historical attachment that already equals the expected one
(*adimpleo*, *suppleo*: the root has no `e`, so the whole stem was kept).

On the full source candidate it repairs **24 blocks, 32 records**: 8
vowel-anchored blocks (16 records), 11 doubled-`u` perfects, 3 reclassed
presents (*sileo*, *exsorbeo*, *circumjaceo*) and 2 suffix supines. 31
vowel anchors lie in the root, 58 `u^i` perfects sit on consonant stems, 6
historical attachments already match, 2 blocks have another shape and 1
stem ends in a vowel; all are left alone. The curated witness corrected
*adimo*, *eximo*, *expleo*, *congruo*, *ingruo*, *sileo* and *exsorbeo* by
hand and inherited the other 17 defective blocks. The private trial source
has SHA-256
`4f513aa665f4b53142e503a6549999df1addee5f9aecd3efc6e9cbfaedecd8ff`.

## Native qualification on family cells

`tools/qualify-latin-residual-attachments.py` rebuilds the original native
candidate, checks its index receipts, builds the trial, requires unchanged
nominal indexes and pairs every replacement with its defective record: a
perfect or supine stem differing by one contiguous run of letters, or a
present whose class alone changes from `conj3` to `conj2`. The 32 repaired
records generate 192 present, perfect and supine cells on 182 forms: 12 are
covered before the repair and all 192 after. The 32 defective records
generated 192 cells on 182 forms, all covered before and none after. On the
364 forms together the sixteen-field comparison retains 467 readings, adds
258 and removes 347; 15 forms become recognized and 160 defective forms
cease to be. Against the controlled rebuilt baseline 84 of the additions are
exact historical readings and 174 go beyond it. Four of the 59
changed-definition loss cases have a repaired block. The identical-root
control changes nothing.

## Full LISTALL diagnostic

| Metric | Original candidate | Residual attachment trial |
| --- | ---: | ---: |
| Recognized literal forms | 847,750 | 847,748 |
| Native analysis rows | 2,100,530 | 2,100,454 |
| Forms newly recognized | — | 121 |
| Lost recognized forms | — | 123 (see below) |
| Removed eleven-field readings | — | 1,473 |
| Added eleven-field readings | — | 1,397 |
| Changed grammatical multisets | — | 1,506 |
| Equal-count multiset changes | — | 228 |

Of the 1,397 additions, 1,121 are direct, 109 carry native preverbs and
167 both; by API tense they are 24 without tense, 85 present, 42
imperfect, 335 future (the future participle and the reclassed presents'
future), 605 perfect, 204 pluperfect and 102 future perfect. The 228
equal-count changes come from the reclassed presents: a third-conjugation
future such as *silet* becomes the second-conjugation present. Of the 1,473 removed readings, **1,170 carry native preverbs**:
the eight short defective stems of the vowel-anchored family (`e_m`,
`empt`, `e_v`, `e_t`, `de_v`, `de_t`, `dex`, `dect`, `re_m`, `rempt`) were
composed with the whole preverb table, and withdrawing them withdraws every
composition. The identical-root control changes nothing.

The 123 forms no longer recognized pass the qualification's check: every
former reading of each came from a repaired block's defective record
(perfect-system readings of the withdrawn stems, present readings of the
reclassed stems), 76 directly and 125 through native preverb composition,
under 7 lemmas. A local enumeration of the defective stems composed with
the preverb table shows what such forms can be. Most are not words
(*congruuit*, *addevit*, *indexit*), but two real families stand out,
recognized before only by a wrong composition on a wrong stem: the noun
*coetus* (as a supine of `co-` with *expleo*'s defective `e_t`) and the
perfect system of *dirimo* (*diremi*, *diremit*, *diremptum*, as `di-` with
*redimo*'s defective `re_m`). *Dirimo*'s own block is the same historical
defect (`di^ri^me_m`, inherited by the witness), outside this recipe only
because its source header carries the conjugation digit in a second
`<itype>` field that `combitype` joins to the first. Extending the
attachment proofs to joined itype fields is the next recipe.

## Remaining arbitration

The recipe covers the attachment families the survey found; parts whose
attachment the literal table or `spectypes[]` fixes correctly, blocks with
several itypes and the `-icio` headwords spelled without `j` (two blocks,
`je_ci`/`jectum` parts on `a_di^ci^o` stems) are outside it. No selector,
corpus or production source is promoted; the PR remains a draft.
