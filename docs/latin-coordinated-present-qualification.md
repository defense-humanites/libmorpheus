<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Quoted present alternate with two coordinated supines

This opt-in trial follows the nine
[reverse-reference presents](latin-backlinked-present-qualification.md).
The source review found one additional article outside the strict selector:
an explicit perfect, two supines joined by `and`, third conjugation, a full
alternate and a Latin passive-present quotation. Handling both supines
requires separate principal-part work; this trial only uses the explicit
conjugation and quotation to qualify a present stem.

`tools/recover-latin-coordinated-present.py` requires that exact alphabetic
perfect/two-supine/class-three grammar, compatible active POS and a plain
class-three primary. The same-article full alternate must retain the first
letter and word length and differ by one letter. This spelling bound alone
is not approval: its third-singular passive present must occur as a complete
word in a `quote` element with `lang="la"` in that article. Explanatory text,
other languages, substrings, perfects, entities in the quotation, abbreviated
spellings and class-three `io` alternates do not qualify. Unicode quantities
and capitalization are normalized for this quotation lookup only.

Existing source/block uniqueness and source-matched unflagged primary checks
remain. A copied row supplies the explicit class-three declaration to the
present-only selector. Neither the source header nor either supine is changed.
No paradigm is inherited from another article. Inserted stems retain their
source quantities and delimiters and carry `orth`; all previous bytes stay
unchanged, with no perfect or fourth-part addition.

## Expected source and native controls

CI requires **one** insertion and one private quotation witness in each
quantity treatment. The witness binds the quoted form and existing lemma to
the pinned source revision/hash, recovered-header hash, source article and
quotation hashes and exact candidate hash. Both quantity witnesses must agree
apart from their candidate hash. The broader diagnostic after insertion must
contain the same six serialized dossiers as the earlier strict diagnostic:
five pending spellings and the withheld contextual abbreviation. These remain
expectations until the pinned-source run succeeds.

`--include-coordinated` enables the previous seven replay passes plus a
same-root control and a consecutive reverse-reference-to-coordinated pass.
Both quantity indexes must agree and nominal witnesses remain fixed. All nine
passes cover 1,033,579 literal LISTALL inputs. Every changed count is reanalyzed
under the eleven-field grammatical multiset; removing previous readings fails
the trial. The five-pass default and explicit seven-pass option remain.

A native control also analyzes the source quotation independently of LISTALL
membership. Before insertion it must have no direct source-lemma reading
with verb POS, third person, singular, present, indicative and passive voice;
after insertion it must have that exact reading. A native preverb lead cannot
satisfy it. Wrong candidate/header/source bindings, API errors and removed
previous eleven-field readings fail. Other analysis attributes and
unchanged-count forms remain outside the multiset control.

Seven new source tests and five new native-control unit tests pass locally;
the seven existing replay tests also pass. They exercise quotation boundaries,
Unicode quantities, entities, grammar/voice/subclass and ambiguity exclusions,
idempotence, preserved bytes, witness binding, exact native grammar, preverbs,
errors, removals and private output. Source and full native runner results are
pending at this commit.

Only tools, synthetic fixtures, counts and fingerprints are published. Actual
quotations, forms, lemmas and candidate records stay in private runner paths.
The production corpus remains unchanged. This trial authorizes neither supine,
the five other pending spellings nor the contextually abbreviated component.
