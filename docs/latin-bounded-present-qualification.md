<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Bounded whole-word present spellings

The individual review recorded five complete spellings in their own source
headers, without a qualifying independent reverse reference. This trial
follows the [quoted coordinated-supine present](latin-coordinated-present-qualification.md)
and uses five separate spelling rules. Each remains conditional on an explicit
same-article alternate, compatible active POS, strict complete class-three
principal-part grammar, a unique existing lemma block and a source-matched
unflagged canonical present of the same conjugation subclass.

| Rule | Exact spelling bound |
| --- | --- |
| Nasal omission | Initial `con` becomes `co` before initial `i`; the whole remaining class-three `io` word agrees |
| Prefix and vowel restoration | An explicitly delimited `ef` before `fi` becomes `ec` before `fa`; the remaining `io` word agrees |
| Stop alternation | One `c`/`g` substitution immediately before `l`, with the same first letter and word length |
| Prefix-boundary vowel elision | An explicitly delimited `are` becomes `ar`; the entire following `io` word agrees |
| Short/full preverb | Initial `tra` becomes `trans` before initial `i`, optionally inserting `j` before that `i`; the remaining `io` word agrees |

These are bounded matches between source-supplied whole words, not a general
edit-distance or prefix inference. The original quantity marks and delimiters
are preserved in each inserted `orth` present. Original bytes, perfects and
fourth parts remain unchanged. Homograph-numbered heads, incompatible voices,
ambiguous or flagged canonical blocks and conjugation-subclass changes are
withheld. A contextual component lacking the compound's initial letters
cannot pass these rules.

## Source and native expectations

CI requires five inserted records, one for each rule, in both quantity
treatments. Five private witnesses bind the source lemma and thirteen active
present cells to the exact source revision/hash, recovered-header hash and
candidate hash. Quantity witnesses must agree apart from their candidate
hash. The remaining diagnostic must be the same one serialized dossier in
both treatments, a strict subset of the previous six with exactly five
resolved records. Its article fingerprint must match the reviewed contextual
abbreviation. The dossier and lexical data are never printed or uploaded.

The native family control is independent of LISTALL membership. Each source
alternate has six indicative cells, six subjunctive cells and an infinitive:
**65** cells in total, using the public ABI's person, number, mood, tense and
voice constants. Every cell must have a direct reading under its source lemma,
with verb POS, present tense and active voice. Native preverb leads and
wrong-voice readings cannot qualify. Coverage before insertion is measured;
the trial need not invent gains for cells already recognized. Previous
eleven-field grammatical multisets must be retained with their multiplicities.

`--include-bounded` enables the earlier nine comparisons plus a same-root
control and a consecutive coordinated-to-bounded comparison, covering all
**1,033,579** literal LISTALL inputs eleven times. Both quantity indexes must
agree, and baseline nominal witnesses remain fixed. Native errors, count
mismatches or removed grammatical readings on changed-count inputs fail.
The five-, seven- and nine-pass options remain available. This does not check
all analysis attributes or all unchanged-count grammatical rows, and does not
resolve the earlier baseline-to-candidate recognition losses.

Seven synthetic recovery tests cover all five rules, exact matching, quantity
preservation, grammar/voice/subclass and ambiguity guards, idempotence, witness
bindings and private output. Three family-control unit tests cover all thirteen
cells, preexisting coverage, bindings, missing/wrong-voice/preverb readings,
removals and API errors. Two new synthetic native tests check active families
for both class-three subclasses and passive quotations with new or preexisting
coverage. Local Python tests and compilation pass; real source and native
runner results are pending at this commit.

Only tools, synthetic fixtures, aggregates and fingerprints are published.
The production corpus remains unchanged; this trial does not reconstruct
perfects or supines and does not authorize the withheld contextual component.
