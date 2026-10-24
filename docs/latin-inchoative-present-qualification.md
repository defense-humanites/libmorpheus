<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Inchoative present alternate qualification

This experimental stage follows [latin-complete-alternate-qualification.md](latin-complete-alternate-qualification.md)
with the same pinned source revision, header/source hashes, literal LISTALL
corpus and native API options. Only tools, synthetic tests, aggregates and
hashes are public; entries, reconstructed stems and individual probes remain
private. Production data and historical filters are unchanged.

The opt-in `inchoative-present` tier requires one projected grammatical field
consisting of a complete alphabetic perfect ending in `i`, followed by `, 3`.
The canonical active head must end in literal `esco`, and its unique unflagged
`conj3` present must match the source. The complete same-article alternate
must replace only that terminal `esco` by `isco`, preserving the entire prefix
including quantity marks and delimiters exactly. An explicit POS must be
active verbal; an absent projected POS is accepted on the declared grammar
and existing matched present. Source/block ambiguity, other spellings and
incompatible voice are withheld. This stage adds only the alternate present;
existing perfects and fourth parts remain untouched.

Both quantity tiers add **four** records in **four** article blocks, withholding
**fourteen** ambiguous or unavailable blocks and **fourteen** alternates outside
the exact pattern. Two new synthetic tests cover prefix and quantity
preservation, voice, grammatical field, existing flags, idempotence and
retention of unrelated parts. All eight repair/recovery programs pass,
**44** tests in total. CI reconstructs this tier after the prior two tiers in
both quantity variants.

The unchanged historical chain reproduces all **four** alternate present
stem/tag pairs independently. The four principal forms increase from **zero**
to **four** under their expected verbal source lemmas, with **four** expected
readings, all indicative present. Their complete probe contains two prior
other readings and six readings after the trial. Private grammar-probe
before/after SHA-256 are
`8453d556f71b1d2a7cec36618f8a9cb40edaaf4e0a848ab46582c5dcaa45effe`
and `4f9e04088068cb363067510a8b76bd25c60def5c9493441f67917dc9f2ec4a5c`.

Letters-only/all-quantity output SHA-256 are
`65d73c230789a24aedb75cdb10927e3f023ff10831751f4c7ba8c75f121ecd97`
and `6d54e874ea9d945f08bfe31616a103f2006dc4f1aeda6fa4fb0c68a87fb09309`.
Both variants produce the same verbal index/sidecar SHA-256:
`96507325b0397b2efc6c591f67180d98974fac9638b3ade49d63aa9b8d8ffa5c`
and `d7e19253fbee673764cf74e76f07a8d37825b0563b17ff811e2f3c265ebad8d9`.
Nominal indexes remain unchanged. The original 15,255-form loss subset remains
at **4,238** recognized forms and **7,937** readings, with zero API errors.
The full identical-root, predecessor and controlled-baseline comparisons
have completed; the unchanged subset does not imply unchanged reading counts.

The broader third-conjugation inventory contains **53** eligible complete
alternate candidates before this bounded stage. After removing its four
records, **49** candidates in **47** articles remain for individual review.
The inventory is not an authorization to add every spelling under its source
lemma: an inspected article marks a bare ending variant as `extent="full"`,
while its citations retain the compound prefix. A generic third-conjugation
rule would incorrectly treat that contextual ending as a whole headword.
This stage's identical-prefix requirement avoids that inference. Private
remaining-review dossier SHA-256 is
`e135a2a3521335f2a92cbbaf7160cf8740bc5931ac7e7752998c47e1e43a425b`;
serialized inspected article SHA-256 is
`22ee9442f5a3f0608dd071f9a191a21463c67a7a1efc2dd573b0774c98d34c93`.


All three complete LISTALL comparisons have zero API errors. The candidate
retains **843,825** recognized forms and returns **2,095,818** readings.
There are zero recognition gains or losses versus its predecessor, with
**103** increased counts and no decreased counts. The identical-root control
has zero count differences. Baseline recognition cells remain **826,523**
both, **11,467** baseline only, **17,302** candidate only and **178,287**
neither. The nominal indexes and original loss subset remain unchanged.

On all changed-count forms, the eleven recorded-feature multisets retain
all **156** prior rows and add **156** rows, removing none. The fields and
scope limits are those listed in the preceding qualification. Private
before/after SHA-256 are
`670383dd9b4323716d80538aac8dd32f77fbac9bb379b0cdaa5fa29700642c10`
and `391a284305fc647095b81d65b6fce37327149b3c35165bf8ceb535c961f20d17`.
Independent native-preverb provenance confirms that all **156** added readings
on these **103** forms use one prefixed lemma, with no direct source-lemma
addition on LISTALL. At this stage the projected compound header had complete spelling
variants and an inchoative verbal label but no grammatical field. Subsequent
full-entry review found an explicit conjugation in untagged header text; its
separate recovery is qualified in
[latin-present-recovery-qualification.md](latin-present-recovery-qualification.md).
The earlier returned prefixed lemma differs from the source canonical lemma;
its provenance remains distinct from the new direct source-lemma readings.
Private before/after provenance SHA-256 are
`2d49ea8988d0251d69e66c4c2f7783944556cbedff1add199758ce761ad1e1b3`
and `51f1e83be02f9374b118c463f305206ea1bf75e5ea5a1119caf9e0994cce34b7`.

A separate **52**-form present-system probe covers all six indicative present
persons, all six subjunctive present persons and the present infinitive for
each new spelling. All **52** have the expected verbal source lemma and
recorded mood/tense after the trial, previously zero. Their expected-lemma
readings increase from zero to **68**, while all **34** prior recorded-feature
rows remain and none is removed. None of these **52** literal probe forms
occurs in pinned LISTALL. This independent probe qualifies the added direct
present paradigms without attributing the full-corpus native-prefix readings
to them automatically. Private before/after grammar SHA-256 are
`6722c8d2d1a5af1a3dca6fce8ef41e698c336bfdd33ab2fc70d6f901c37a75e8`
and `06e01f0101a90fee5c053e7c626aebd2da0ef5a6c29178bccff50c0f4db3fec3`.

Re-running the prior regular, terminal-delimiter and present-only tiers with
the revised tool reproduces their existing private outputs byte for byte.
Linux CI, platform/release qualification and lexical research all passed on
code commit `9415726` (runs **36980375927**, **36980375871** and **36980371607**).
No production corpus promotion or source-rights decision follows from these
checks.
