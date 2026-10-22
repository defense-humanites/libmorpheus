<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Written-part anchor repair

Not yet qualified on LISTALL: the dedicated workflow runs on the commit that
adds this recipe and this page will carry its receipt.

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

## Native qualification (family cells, local)

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

Pending the dedicated run. The global comparison must show no recognized
LISTALL form lost: the withdrawn doubled forms are not Latin words and are
not expected in LISTALL, and the run fails if one is.

## Remaining arbitration

The recipe repairs the anchor only where it demonstrably doubled letters. The
other defects of the generic attachment seen in the dossiers — a part whose
letter is absent from the stem and is appended without a trim
(`re^-fercs`), a trim that overshoots (`ins` for *indulgeo*, `e_v` for
*expleo*), vowel-initial parts the rule refuses — are left to their own
measurements. No selector, corpus or production source is promoted; the PR
remains a draft.
