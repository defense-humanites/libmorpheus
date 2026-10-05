<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Present alternates confirmed by standalone reverse references

This opt-in trial follows the internal-vowel stage and the
[remaining-present source review](latin-remaining-present-review.md).
`tools/recover-latin-backlinked-present.py` requires both a complete alternate
in the same canonical article and an independent, unique standalone entry
for that spelling which refers explicitly back to the canonical source key.
The cross-reference confirms an already supplied alternate; it never selects
a missing paradigm from another article.

The original strict class-three grammar, compatible active voice, unique
source/block, source-matched unflagged primary present and conjugation-subclass
checks remain. Reverse entries must have one full primary orthography and a
plain `v. TARGET.` reference. An optional infinitive or explicit third
conjugation and compatible active POS are admitted. One source encodes
`init.` in a separate italic sense child; only that exact qualifier is
accepted. Embedded references, substantial sense text, additional spelling
heads, unsupported grammar/voice, entities, ambiguous entries and unnumbered
references to numbered source keys are withheld.

The source run adds **nine present records under nine existing lemmas** in
each quantity treatment. Every inserted alternate keeps its original source
quantities and delimiters and carries `orth`. All previous bytes remain
unchanged; no perfect or fourth part is added. Source spelling preferences
are preserved as evidence, without declaring every admitted spelling equally
preferred. Five synthetic tests cover the reverse-reference structure,
uniqueness, absent same-article alternates, grammar/voice/subclass, homographs,
unchanged parts, idempotence, private output and source/count/no-overwrite
guards. CI requires nine additions and six remaining strict dossiers.

## Local independent controls

All nine isolated alternate headers reproduce their expected present stem
and conjugation through the historical filters with the original source
grammar. Their private filter-review SHA-256 is
`93843ad58b4de1690700d9f686139ed8db75ba82c6ecb6a1facc0f30b8aaea1a`.

A separate thirteen-cell active-present probe per source lemma covers
**117 expected surface/lemma/grammar pairs**: six indicative persons,
the infinitive and six subjunctive persons. Expected grammar coverage rises
from **0 to 117**, with **117** matching readings after the trial. On the
same probe inputs, the eleven-field multisets retain all **189** previous
rows, add **149** direct source-lemma verb rows and remove none. These fields
are workword, lemma, part of speech, person, number, gender, case, tense,
mood, voice and degree. Other analysis attributes are outside this control.
API options are zero and ABI is two; there is no native API error.

Private before/after probe fingerprints are
`eb8750d83fffe2ec97cb52e98545c4c2e9073a1f12b1790068176cf542684583` and
`3e6fa9120672ea1b2d9aeb04b034ddb2ffbf2738739ba527c3bae1cc8fb07a92`.
The local letter-oriented source hashes are
`6311f8b644aae9dbea71918da8da3e0db252d33cf055fa68c8d80a397037e2bf`
before and `3e11728add43f5c05fc8ccd197cb985fb18b01a5a4d96581291ee987bca8b98a`
after. Both quantity treatments build equal indexes, with verbal index
`cac5ef830afc6dc428a41ab7932bb184007e831b7bf3f227ef51fc56ee7c524f`
and sidecar `0f59ca4dadf345514617b879c7b0ffb37af786b05376990a60547657cacffbe2`.
Nominal witness indexes are unchanged.

These local measurements form a **separate macOS series**. Raw historical
scanner outputs differ from the Linux runner; the cause remains unqualified.
The exact source header projection and fifteen-entry source dossiers agree
byte for byte with CI. The targeted native probe compares its own local
before/after runtime, not the earlier Linux whole-corpus totals.

## Complete runner qualification

The seven-pass replay also passes locally on these 117 distinct probe forms:
all three identical controls have zero changed counts, all passes have zero
API errors, and the consecutive backlinked pass reproduces the same 117
increases and grammatical multisets. This checks the new replay option and
reporting path without representing the complete LISTALL corpus. The 115
synthetic tests across the affected projection, review and replay suites and
the existing Latin recovery pipeline pass, as do two native integration tests.

The full replay adds an explicit `--include-backlinked` option. CI builds
both quantity variants, checks equal indexes and unchanged nominal witnesses,
then runs a same-root control and a consecutive vowel-to-backlinked LISTALL
comparison in addition to the existing five comparisons. Every changed
count is reanalyzed under the eleven-field grammatical multiset and native
preverb provenance control. Removed previous grammatical readings fail this
new step. Actual lexical outputs remain private; only reports and hashes are
printed. Full runner results are pending when this trial is first committed.
The five remaining spellings, coordinated-grammar case, historical identity
and global reconstruction losses still require their own qualification.
The production corpus remains unchanged.
