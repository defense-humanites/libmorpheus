<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Further present recovery qualification

These private experimental stages follow
[latin-inchoative-present-qualification.md](latin-inchoative-present-qualification.md)
with the same pinned source, header hashes, literal LISTALL corpus and native
API options. Only generic code, synthetic tests, aggregates and hashes are
published. Entries, reconstructed stems and individual forms remain private;
production data and historical filters are unchanged.

## Complete velar variants

The opt-in `velar-present` tier requires the exact field `nxi, nctum, 3`, an
active complete canonical head ending in `ngo`, and all three unique unflagged
canonical parts matching that field. A complete same-article alternate must
insert only `u` before the final `o`, preserving the complete preceding spelling,
quantity and delimiters. An explicit POS must be active verbal. This adds only
the alternative present, retaining the original perfect and fourth part.
Three articles supply **three** records; **two** other spellings are withheld.
One article labels its alternative as less correct: it is retained as an
orthographic variant, not promoted as the canonical spelling.

The unchanged filters independently reproduce all **three** alternative
present pairs. A **39**-form probe covers six indicative present persons,
six subjunctive present persons and the present infinitive per spelling.
All **39** have the expected source verbal lemma and recorded grammar after
the trial, previously zero, with **51** expected-lemma readings. All **20**
prior recorded-feature rows remain; **68** rows are added. All **39** probe
forms occur in pinned LISTALL. Before/after grammar SHA-256 are
`127390e6e2b3da72d18b0629c64ab3c86aa3c6059564631de2f7c62838bcfb15`
and `447f0d220dfcc0edfa893f6d9593bd70dfc4e14819ebce8e2e41f47ac788dc33`.
The three principal forms also pass their independent lemma/indicative-present
checks. Their before/after SHA-256 are
`6f0b8cae9e589c99a93508b2dae7302d451152cf1b536c516a164dfb8f3ab34b`
and `0df5a12f64b019746b3b53e2df345d8f7d3ee233cafaa0b1bb1e153184cb24ae`.

Letters-only/all-quantity output SHA-256 are
`4186fa48a4b53d3c6b36fbdb403f7eb319d377d3e3ccbe49e5e8bdb8ff6d046f`
and `9c6ed71056e6dc4c3b6c0eec743d46e02f752f6919bf4df851bfc164800966f4`.
Both variants build identical verbal index/sidecar SHA-256:
`457b91d6f16a20395831dfe25b25ae8293ead46097d386664c2276ecda0318a8`
and `6ecac7377c5e27b615a1f154210d336300d6830141de968fce6be6a9fb2674a0`.

## Conjugation in an untagged tail

Full-entry review of the preceding native-prefix lead found an explicit
third-conjugation declaration in untagged header text. The structured header
had omitted it. This is additional source evidence, not inheritance of the
base verb's paradigm. The dedicated tool requires the exact direct-child
header sequence of two complete orthographies, a bibliographic note and the
first sense. The note's immediate tail must contain exactly a parenthesis
closure, one alphabetic perfect ending in `i`, class `3` and final comma.
The first-sense italic label must be exactly `v. inch. n.`. Projected fields
must match the original source projection plus the validated first-sense
recovery, with no structured grammatical type. The complete orthographies
must share a base, differing only in `isco`/`esco`; each retains its own
quantity and delimiters. The entire unhandled header must occur once in the
candidate, with no existing candidate lemma block or ambiguous source join.

One article supplies **two** present records under its canonical lemma. Its
unhandled header remains unchanged, and no perfect or fourth part is added.
The unchanged historical filters reproduce the original unhandled header
exactly. In separate isolated trials, putting the explicitly attested class
`3` into an `itype` field reproduces both present stem/tag pairs, with the
original inchoative POS retained. This isolated projection is documented as
a trial; the historical filters and pinned TEI are unchanged. The source
article's serialized SHA-256 is
`0bb2506d92526284c8aeaf2bc98af10b10d6b9049898553228ff605290734276`.

A **26**-form present-system probe increases forms with the expected verbal
lemma and recorded grammar from **13 to 26**, and expected readings from
**17 to 51**. Before the trial, the 13 matched forms/17 readings were all
native-prefix readings. After it, all **26** have **34** direct source-lemma
readings with no native preverb, while those **17** earlier prefix readings
remain. All **51** prior eleven-field records are retained; **34** are added.
Thirteen probe forms occur in LISTALL. Before/after grammar SHA-256 are
`7ba99e50a5f9b308a66c55d98779a2957b4164dffa859196980e6e2a03abbb93`
and `cc9abe65c544d9e97928479e5f771852f3de292b2a8c1c558de2125016f29135`;
provenance SHA-256 are
`100f78652877ca2b5e82b6b921c2d216d316250d6d76f0cbfb2af8d344ac4d54`
and `6e033f65bc54168cd3f1e03be19e98e7bfe0c5194f7758dee28c4ec9b16108d1`.

The preceding inchoative trial had added **156** native-prefix readings on
**103** changed-count forms. All **103** now also have **156** direct verbal
readings under this article's canonical lemma, without a native preverb.
Every previous row's form, POS, mood, case, gender and tense is covered by
a corresponding new canonical-lemma reading. That comparison intentionally
excludes lemma, stem, workword, suffix and ending differences and does not
claim complete signature identity. It supplies a direct source-backed
present-system alternative for all 103 earlier review forms; it does not
retroactively validate their older prefixed lemma. Grammar/provenance SHA-256
are `753d55db8c0ab726f1a6af85f48809be64fcf11f3b7905d221f93a69df6b734a`
and `9075a9c3e3b4cfb39c4b0371c6b4f4e3172c37132bf883dfbd234a874e21ea9d`.

Letters-only/all-quantity output SHA-256 are
`dec7f5ee0f03c0403df727e16ba80bf30603e454e46aa07272f2090640a7bd22`
and `262a9c923d9423804b150066bd687d61a81e4cf3f8d12786fd5d95f1f6e110ee`.
Both variants build identical verbal index/sidecar SHA-256:
`0b56983c5ada52ab145ab46d64157457242339b0edd1847701141669004a431a`
and `37ddb75cad0fe26e006390013bb1d8c06aeb73d6504a343c6b0f0f51982b4f74`.
Nominal indexes remain unchanged in both stages. The original 15,255-form loss
subset remains at **4,238** recognized forms and **7,937** readings in both,
with zero API errors. Full LISTALL comparisons follow below.

Two new velar tests and five dedicated untagged-header tests cover exact
patterns, source identity, voice, quantities, matched canonical parts,
unaltered projected fields, duplicates, idempotence, private outputs,
expected counts and no overwrite. All nine repair/recovery test programs
pass: **51** tests. CI reconstructs both stages in both quantity variants.


## Full qualification of the first two stages

All six complete comparisons cover **1,033,579** distinct literal forms with
API options zero, ABI 2, and zero API errors. The velar stage recognizes
**844,237** forms and returns **2,097,381** readings: **412** recognition gains,
zero losses, and **929** increased counts with no decrease. The untagged stage
retains **844,237** recognized forms and returns **2,097,537** readings,
adding **156** readings on **103** increased counts without recognition changes.
Both identical-root controls have zero count differences.

Recorded-feature multiset comparisons on all changed-count forms retain
all **804** prior rows and add **1,563** in the velar stage, then retain all
**312** prior rows and add **156** in the untagged stage, with none removed.
The eleven fields are form, lemma, POS, workword, stem, suffix, ending, mood,
case, gender and tense; other API attributes are outside this comparison.
Private before/after SHA-256 are respectively
`63784f5dbf7f1a2cc99dd1b09ea288ff3b2cd6c496996c58bafc7b94de1c07f9`,
`00c5043a5db3621cb58b3c92858d81fd026b7df7a081f77a13e8e41aa52ee6eb`,
`391a284305fc647095b81d65b6fce37327149b3c35165bf8ceb535c961f20d17`
and `753d55db8c0ab726f1a6af85f48809be64fcf11f3b7905d221f93a69df6b734a`.

The **412** newly recognized velar forms have **312** direct verbal readings
on **206** forms and **468** native-prefix readings on **309** forms.
Those form sets overlap: **103** direct only, **206** prefix only and **103**
with both kinds. All gained-form readings are verbal. The prefix readings use
three different prefixes; an entry or homograph join must be resolved before
attributing their alternate paradigms to source compounds. Independent
provenance SHA-256 is
`5605a909572c23ec06264a3120f55d1d378d5bbba627a196118dd6a77c5d3fac`.
The untagged stage's **156** added full-corpus readings supply the direct
canonical-lemma analyses for the **103** preceding inchoative review forms
qualified above.

Against the controlled rebuilt baseline, final recognition cells are
**826,523** both, **11,467** baseline only, **17,714** candidate only and
**177,875** neither. The earlier **488** first-repair losses remain absent,
with zero API errors. All four previous alternate tiers reproduce their
existing private outputs byte for byte after the velar tool extension.
These improvements do not qualify a production corpus replacement.

The explicit suffix/homograph review continues in
[latin-velar-suffix-qualification.md](latin-velar-suffix-qualification.md).
