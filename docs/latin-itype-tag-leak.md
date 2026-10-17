<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Supine records that contain the leaked `</itype>` tag

Thirteen blocks of the full source candidate hold a `pp4` record whose stem
ends in `/ityp`. Three of them are also in the curated witness, so the defect
predates this reconstruction. One of the thirteen is among the six
complete-loss cases without a terminal conjugation digit.

## Historical defect

`do_vstems()` in `src/gkdict/latvb.l` copies the text after the perfect into
the supine buffer whenever that text is neither a digit nor exactly
`</itype>`. A bare one-token perfect such as `u^i` or `mpsi` with no supine
and no conjugation digit leaves `</itype>` after the first space-free token
has been cut at its final `i`; the filter then strips two characters from
that tail and emits `…/ityp pp4`. The engine accepts the record: it generates
readings for inputs that contain the slash, which are not Latin surface forms.

## Bounded recipe

`tools/repair-latin-itype-tag-leak.py` deletes a `pp4` record ending in
`/ityp` only when its lemma joins exactly one source article whose single
`<itype>` is a one-token field ending in `i` in both the source projection
and the trial row, and when the block and the leaked record are unique.
Nothing is added, no other record is touched, and leaks without that source
shape are withheld and counted. Four synthetic tests cover the source shape,
the deletion, withheld blocks, private output and no overwrite.

## Trial and native qualification

Over the unchanged qualified candidate
`6caf089d03e62d745aebc94d1b1cc5cf06938626db4af8c794a2326ca7a94cd9`, 1,800
headers carry a bare one-token perfect; 13 produce a leaked record and all
13 are deleted. The private trial source has SHA-256
`d14b080c315514bf9688e4c8a3003dc6d9e3ca8fd488a106eef5ac5293d84b32`.

`tools/qualify-latin-itype-tag-leak.py` rebuilds the original native
candidate, checks its index receipts, builds the trial and requires unchanged
nominal indexes. The 13 deleted stems generate 78 supine cells on 65 inputs,
every one containing the slash: all are covered before the deletion and none
after, 224 readings disappear on those inputs and none is added. The dedicated
workflow requires that the full LISTALL comparison removes and adds no
reading and loses no recognized form, and that the identical-root control
changes nothing.

## Remaining arbitration

The deletion supplies no supine: whether the source elsewhere attests one is
not examined. The class of a present kept as `conj3` under an `-eo` headword
without a digit is a separate question. No selector, corpus or production
source is promoted; the PR remains a draft.
