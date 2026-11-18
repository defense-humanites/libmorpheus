<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Written-part anchor repair

Qualified code: `e4fc8b126b061a0a2145143e3857a3005848b73a`. The
[dedicated workflow run](https://github.com/defense-humanites/libmorpheus/actions/runs/39752098078)
succeeds with the full LISTALL diagnostic; the
[aggregate receipt](qualification/latin-anchor-duplication-e4fc8b1.json)
records counts, categories and SHA-256 values only.

The [residual loss attribution](latin-residual-loss-attribution.md) left the
changed-definition dossiers as the largest residue. Read one by one (in
private), several of them do not come from the witness's curated additions
but from a defect of the historical filter that the witness itself inherited:
the perfect and supine stems of *voveo*, *volvo*, *vivo*, *bibo*, *scisco*,
*mansuesco* and their compounds double the letters of the stem (`vo^vo_v`,
`volvolv`, `vi_vix`, `bi^bi^b`, `scisci_v`, `mansu^esu^e_v`). The curated
witness carries the same stems in all but two of these blocks, so the LISTALL
comparison against the controlled baseline never counted them as losses:
they are a defect of the historical data, not of the reconstruction.

## Historical defect

For a consonant-initial principal-part string ending in a conjugation digit
that the explicit table of `src/gkdict/latvb.l` does not list,
`is_spectype()` returns the digit and `do_vstems()` receives the written
perfect's first letter as the trim. `truncstem()` cuts the present stem from
the **last** occurrence of that letter (an `s` also matching `d` and `q`) and
the written part is appended. When the part repeats the stem's own letters —
`volvo, volvi`: the last `v` of `volv` is the final one — the anchor falls
inside the letters the part already contains and the attachment doubles
them: `vol` + `volv`. The supine is attached at the same anchor, so
`vo^lu_tum` becomes `volvo^lu_t`.

## Recipe

`tools/repair-latin-anchor-duplication.py` reads the projected headers whose
single `<itype>` field is one consonant-initial, digit-terminated string of
one or two written parts outside the lexer's literal table, and the matching
candidate block. It emulates the historical attachment on the block's present
stem and acts only when the block's perfect and supine records are exactly
that output **and** the trimmed prefix ends with two or more of the part's
leading letters. It then anchors the part at the **earliest** occurrence of
its first two letters in the present stem (notation disregarded) and replaces
the two records: `volv` and `vo^lu_t` for *volvo*, `con-vo_v` and `con-vo_t`
for *convoveo*, `mansu^e_v` and `mansu^e_t` for *mansuesco*. It reads no
other header, infers no part, keeps blocks whose records are not the
historical output or whose shape differs, and leaves the lexer unchanged.

On the full source candidate it repairs **25 blocks, 44 records** (25
perfects, 19 supines; 11 blocks doubled two letters, 13 three, one four).
Seven blocks already hold the re-anchored stems, 842 attachments show no
duplication, 43 blocks have another shape (several presents, flagged
records), three hold records that are not the historical output and two
lemmas have several blocks or headers; all of these are left alone. The
private trial source has SHA-256
`93368df83cbbf977ee1b394042501dd270acf4dabe8396e5d92e9a49a22711a6`.

## Native qualification on family cells

`tools/qualify-latin-anchor-duplication.py` rebuilds the original native
candidate, checks its index receipts, builds the trial, requires unchanged
nominal indexes and pairs every replacement with its defective record (the
new stem is the old one with one contiguous run of letters removed). The 44
re-anchored records generate 264 perfect and supine cells: 18 are covered
before the repair (forms that another reading already recognized, such as a
present homograph) and all 264 after. The 44 defective stems generated 264
cells on 245 forms, all covered before and none after: the repair withdraws
the doubled forms (`volvolvit`, `vivixit`) as it adds the written ones. On
the 490 forms together the sixteen-field comparison retains 441 readings,
adds 576 and removes 602; 74 forms become recognized and 203 doubled forms
cease to be. Against the controlled rebuilt baseline 80 of the additions are
exact historical readings (the two blocks the witness had corrected by hand)
and 496 go beyond it. Three of the 59 changed-definition loss cases have a
repaired block. The identical-root control changes nothing.

## Full LISTALL diagnostic

| Metric | Original candidate | Anchor repair trial |
| --- | ---: | ---: |
| Recognized literal forms | 847,750 | 848,252 |
| Native analysis rows | 2,100,530 | 2,104,349 |
| Lost recognized forms | — | 0 |
| Removed eleven-field readings | — | 120 |
| Added eleven-field readings | — | 3,939 |
| Changed grammatical multisets | — | 1,930 |
| Equal-count multiset changes | — | 0 |

No recognized LISTALL form is lost: none of the 245 doubled forms the
defective stems generated is a LISTALL word. **502 forms become
recognized**, among them the perfects of *voveo* and *mansuesco*, which no
reading reached before. Of the 3,939 additions, 1,550 are direct, 1,985 carry
native preverbs and 404 occur on forms with both; by API tense they are 69
without tense, 1,089 future, 1,922 perfect, 563 pluperfect and 296 future
perfect. The 120 removed readings lie on 50 forms that stay recognized: they
are readings of the doubled stems, 16 direct and 104 through native preverb
composition, on forms another block still analyzes — *vivixit*, for example,
loses its reading under *vivo* and keeps the one under *vivesco*, whose own
block the recipe withheld. None is an enclitic displacement. The
identical-root control changes nothing.

## Remaining arbitration

The recipe repairs the anchor only where it demonstrably doubled letters. The
other defects of the generic attachment seen in the dossiers — a part whose
letter is absent from the stem and is appended without a trim
(`re^-fercs`), a trim that overshoots (`ins` for *indulgeo*, `e_v` for
*expleo*), vowel-initial parts the rule refuses — are left to their own
measurements. No selector, corpus or production source is promoted; the PR
remains a draft.
