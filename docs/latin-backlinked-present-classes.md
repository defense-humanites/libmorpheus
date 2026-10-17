<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Backlinked complete present alternates of every verbal class

The [earlier backlinked-present recipe](latin-backlinked-present-qualification.md)
admits a complete same-article alternate only when the source also holds a
standalone entry for that spelling whose whole text is a bare `v. TARGET.`
reference. It is bounded to class-three active headers with explicit
principal parts. An inventory of the complete alternates still absent from
the full candidate shows the same proof available outside that selector:
second- and fourth-conjugation headers, regular first-conjugation and `-ire`
derivatives, deponents and headers whose only inflection field is an
infinitive.

## Bounded recipe

`tools/recover-latin-backlinked-present-classes.py` reuses the projection's
complete same-article alternates and stages one present record per
admitted alternate. It requires:

- a unique candidate block with exactly one unflagged present record, whose
  class tag (`conj2`, `conj3`, `conj3_io`, `conj4`, `ire_vb`, `are_vb`,
  `conj1`, with or without `dep`) decides the present ending to recognise;
  the headword must carry that ending and its root must equal the record's
  stem letter for letter, so the block's class is attributable to the header;
- an alternate carrying the same ending (hence the same voice and class),
  complete, without a leading or trailing dash, and differing from the
  headword by more than notation;
- a unique standalone source entry whose sole full orthography is the
  alternate, whose fields are at most `orth`, `itype` and a verbal `pos`,
  whose text is exactly `v. TARGET.` naming the main article's key, and
  whose inflection fields, if any, are compatible with the block's class
  (`e_re` or `2` for `conj2`, `i_re` or `4` for `conj4`, and so on).

The record is the alternate root under the block's tag and flags plus the
lexer's `orth` flag. No perfect or supine is supplied: the standalone entry
attests the present spelling only. An alternate whose ending differs from the
headword's (`claudeo` beside `claudo`, `cieo` beside `cio`, an active beside
a deponent) is withheld as another class, as are alternates without a unique
standalone entry, entries with other text, and blocks with several presents.
Six synthetic tests cover the class roots, the reference proof, insertion in
active and deponent blocks, idempotence, every withholding reason, private
output and no overwrite.

## Trial on the full source candidate

Over the unchanged qualified candidate
`6caf089d03e62d745aebc94d1b1cc5cf06938626db4af8c794a2326ca7a94cd9`, 83
backlinked alternates are already present (the earlier class-three recipe),
136 complete alternates have no unique standalone entry, 22 have an entry
with other text, 758 carry another ending than their headword, 88 headwords
fall outside their block's class and one reference carries another class.
The trial adds **19 present records in 19 blocks**: one `conj1`, four
`conj2`, eight `conj3`, three `conj3_io`, one `conj4` and two `ire_vb`. The
private trial source has SHA-256
`636f2ef1a937b3e5e263191e2a544dc7f9d7d4205cc0c5626d5d0dc1872e27a7`.

## Native family qualification

`tools/qualify-latin-backlinked-present-classes.py` rebuilds the original
native candidate, checks its index receipts, builds the trial and requires
unchanged nominal indexes. The 19 records receive the engine's present cells,
114 cells on 114 forms: six are covered before the trial and all 114 after,
every record covered. On those forms the sixteen-field comparison retains 124
readings, adds 120 and removes none; 57 forms become recognized. The
identical-root control changes nothing.

Against the controlled rebuilt baseline, six of the additions are exact
historical readings and 114 lie beyond the historical multiset: these
spellings were not in the curated witness, and the present record is the
only reading each standalone entry attests. One of the 59 changed-definition
loss cases has a changed block. The global LISTALL comparison is measured by
the dedicated workflow.

## Remaining arbitration

Alternates of another class or voice, alternates with an embedded or
annotated reference, and the perfect and supine systems of the added
spellings remain open. No selector, corpus or production source is promoted;
the PR remains a draft.
