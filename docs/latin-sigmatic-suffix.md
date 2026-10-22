<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Sigmatic suffix repair

Not yet qualified on LISTALL: the dedicated workflow runs on the commit that
adds this recipe and this page will carry its receipt.

The [written-part anchor repair](latin-anchor-duplication.md) handled the
parts that repeat the stem's letters. A second defect of the same historical
rule appears in the changed-definition dossiers on the sigmatic perfects
written as bare suffixes — `si`, `psi`, `xi` — which replace the final
consonant of the present stem: *fulcio, si, tum* is *fulsi, fultum*; *nubo,
psi* is *nupsi*; *indulgeo, si, tum* is *indulsi, indultum*.

## Historical defect

`is_spectype()` hands `do_vstems()` the suffix's first letter and
`truncstem()` cuts the present stem from its last occurrence, an `s` also
matching `d` and `q`. Two things go wrong. When the letter is absent from the
stem nothing is cut and the suffix follows the final consonant: `in-fulcs`,
`re^-fercs`, `e_-nu_bps`, `pe^r-haurs`. When the `s` rule finds a `d`, or
an `s` of the root, before the stem's last vowel, the root itself is cut
away: `ins` and `int` for *indulgeo*, `sub-s` for *subsentio*. The curated
witness carries the same stems in all these blocks but one (*refercio*,
corrected by hand).

## Recipe

`tools/repair-latin-sigmatic-suffix.py` reads the projected headers whose
single `<itype>` field is a sigmatic suffix perfect, optionally followed by
a short consonant supine (`tum`, `stum`), and a conjugation digit, outside
the lexer's literal table; and the matching candidate block, which must end
in a consonant. It emulates the historical attachment and acts only when the
block's perfect and supine records are exactly that output **and** the
historical anchor lies outside the final consonant cluster (absent, or
before the last vowel). It then attaches the suffix after the stem minus its
final consonant: `in-fuls`/`in-fult`, `re^-fers`/`re^-fert`, `e_-nu_ps`,
`pe^r-haus`/`pe^r-haust`, `induls`/`indult`, `sub-sens`. An anchor inside
the final cluster (*abstergeo, rsi* → `abs-ters`; *ardeo, si* → `ars`
through the `d`) is the historical rule working as intended and is left
alone, as are vowel-final stems.

On the full source candidate it repairs **6 blocks, 10 records** (6
perfects, 4 supines; four blocks for an absent letter, two for an anchor
before the last vowel). Nine attachments have their anchor inside the final
cluster, three stems end in a vowel, one block has another shape and one
lemma several blocks; all are left alone. The private trial source has
SHA-256 `a53cceaff7d2dd9a995b09c2d1d4174b147a2b2dc759bc414ed9edcf6af66e34`.

## Native qualification on family cells

`tools/qualify-latin-sigmatic-suffix.py` rebuilds the original native
candidate, checks its index receipts, builds the trial, requires unchanged
nominal indexes and pairs every replacement with its defective record (the
two stems differ by one contiguous run of letters). The 10 reattached
records generate 60 perfect and supine cells on 56 forms: none is covered
before the repair and all 60 after. The 10 defective stems generated 60
cells on 56 forms, all covered before and none after. On the 112 forms
together the sixteen-field comparison retains 91 readings, adds 92 and
removes 92; 25 forms become recognized and 46 defective forms cease to be.
Against the controlled rebuilt baseline 26 of the additions are exact
historical readings and 66 go beyond it. Two of the 59 changed-definition
loss cases have a repaired block. The identical-root control changes
nothing.

## Full LISTALL diagnostic

Pending the dedicated run. The first run on `8c26632` failed its global
check: a LISTALL form stopped being recognized. The qualification tool now
distinguishes a form whose **every** former reading was a perfect-system
reading of a repaired block — recognized by a wrong reading alone, as
*subsit* was as a perfect of *subsentio*, the irregular *subsum* of the
candidate (and of the controlled baseline) generating neither *subsit* nor
*subsunt* — which it counts and publishes, from any other lost form, which
still fails the run.

## Remaining arbitration

The recipe repairs only sigmatic suffixes whose anchor demonstrably missed
the final cluster. Suffix supines written alone for deponents (`psus`,
`ctus`, `tuus`), the `-icio` compounds, and parts whose attachment the
literal table or `spectypes[]` fixes are outside it. No selector, corpus or
production source is promoted; the PR remains a draft.
