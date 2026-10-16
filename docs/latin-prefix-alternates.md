<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Abbreviated prefix alternates the historical filter discards

The [screen of the 25 third-conjugation headers](latin-third-supine-alternatives.md#remaining-arbitration)
left outside the earlier recipes groups five of them under one defect of the
historical importer rather than a grammar interpretation. Their source
headwords carry a parenthesised abbreviated alternate spelling of the prefix
(`<orth extent="full">` ending in a hyphen), and the historical baseline kept
a parallel stem series under that spelling. The candidate has none of them.

## Lexer limit

`set_orth()` in `src/gkdict/latvb.l` copies the headword stem, then expands
exactly four literal alternates by overwriting the second letter: `adf-`,
`adl-`, `adn-` and `ads-`. Every other `<orth>` of that shape clears the
alternate stem and is discarded; the generic alignment code after that
`return` is unreachable. The historical filter therefore emits `orth`
records for `af-`, `al-`, `an-` and `as-` headwords only. This is a measured
property of the pinned lexer source, not an inference about the dictionary.

## Bounded recipe

`tools/recover-latin-prefix-alternates.py` stages the discarded alternates
without reading either curated witness. For each projected header joined to
its exact source article, an alternate qualifies only when:

- it is a full-extent `<orth>` of ASCII lowercase letters ending in a hyphen,
  and it is not one of the four literals the lexer already handles;
- compared with the headword letters (notation and hyphen removed), it
  substitutes exactly one letter and ends with at least one shared anchor
  letter; a longer or shorter alternate, a second difference or an alternate
  identical to the headword is withheld;
- the headword prefix through the substituted letter and the alternate
  prefix are both entries of the engine's own
  `stemlib/Latin/rule_files/raw_preverbs.table`; the table is the sole prefix
  oracle, so `adr-` beside an `ar-` headword is withheld because `ar` is not
  listed;
- when the headword has an explicit hyphen, the hyphen stands exactly after
  that prefix, so a substitution inside the base (`advor-` beside
  `ad-verto`) is withheld.

The alternate is then applied to every `:vs:` and `:de:` record of the
unique candidate block whose stem begins with the same prefix letters,
keeping notation, hyphenation, flags and homograph identity, and appending
the lexer's own `orth` flag. Stems with any other character (for example an
editor name concatenated by the historical filter), records already flagged
`orth`, records whose stem does not carry the prefix, duplicate blocks and
duplicate alternates are withheld or skipped and counted. Unlike the lexer,
which omits the supine, the recipe applies the spelling to every stem class
of the block. Ten synthetic tests cover the alignment bounds, the preverb
table, hyphenated and unhyphenated headwords, derivative records, idempotence,
withheld blocks, private output and no overwrite.

## Trial on the full source candidate

Over the unchanged qualified candidate
`6caf089d03e62d745aebc94d1b1cc5cf06938626db4af8c794a2326ca7a94cd9`, the
pinned source offers 1,176 accepted alternates; 277 further alternates are the
lexer-handled literals, 294 are withheld by the preverb table, 488 by the
single-substitution bound, 49 as identical spellings, 3 by an explicit
boundary and 1 as longer than its headword. 802 accepted alternates belong to
entries without a candidate verbal block. The trial changes **366** lemma
blocks and adds **581** records: 167 `are_vb`, 12 deponent `are_vb`,
4 `conj1`, 35 `conj2`, 121 `conj3`, 13 `conj3_io`, 10 `conj4`, 4 `ire_vb`,
116 `perfstem` and 99 `pp4`. Six records with unparsed stems and five
existing `orth` records are left alone. No record is removed. The private
trial source has SHA-256
`f5302726ad3fcfbe53f81139b7839af2601f26d4421544c5cb810d8875c16bef`.

## Native family qualification

`tools/qualify-latin-prefix-alternates.py` rebuilds the original native
candidate, checks its four index receipts, builds the trial and requires
unchanged nominal indexes. Each added record receives the engine's present,
perfect or supine cells under its exact lemma (six per record), giving
**3,486 cells on 3,314 distinct forms**. Before the trial 36 cells are
covered; after it all 3,486 are, with every added record covered. On those
forms the sixteen-field comparison retains 5,361 readings, adds 5,469 and
removes none; 618 forms become recognized. The identical-root control on the
same forms changes nothing.

Against the controlled rebuilt baseline, 258 of the additions on these forms
are exact sixteen-field historical readings and 5,211 lie beyond the
historical multiset; the family forms are a small sample of each paradigm,
so these are not the complete-loss recoveries. Seven of the 59
changed-definition loss cases have a changed block: the five third-conjugation
cases screened above and two others. Their complete historical readings are
measured on LISTALL by the dedicated workflow, which also provides the global
recognition and eleven-field comparison; see the aggregate receipt linked
from the pull request once that run is qualified.

## Remaining arbitration

The recipe does not touch the four lexer-handled literals, length-changing
alternates (`hall-`, `adsp-`), alternates with a second difference, stem or
root variants, editor-name `<itype>` fields concatenated into stems, or the
other twenty third-conjugation headers. The `orth` records are spelling
alternates of existing stems, not new lexical identities. No selector,
corpus or production source is promoted; the PR remains a draft.
