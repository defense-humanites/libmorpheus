<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Complete alternate qualification

This private experimental continuation uses the source revision and input
hashes recorded in [latin-combined-fourth-qualification.md](latin-combined-fourth-qualification.md).
Only generic tools, synthetic tests, aggregates and hashes are published.
Lexical entries, reconstructed stems and probe forms remain private.

The existing regular-alternate tool now has two independent opt-in tiers.
`terminal-delimiter` requires the exact `di, sum, 3` field, three unique
unflagged canonical parts matching the source, and a complete alternate
ending in literal `n-do`. It retains the source delimiter in the three new
orthographic records. One article supplies three records; fourteen other
alternates are outside this pattern. The complete article also uses the
syncopated spelling in its citations. Abbreviated alternatives remain withheld.

`present-only` requires exactly the projected field `3`, an existing unique
unflagged matching canonical present, and a complete active alternate of the
same third-conjugation subclass. An explicit POS must be active verbal;
articles without a projected POS remain eligible on the grammatical field
and existing matched present. Four articles supply four orthographic present
records, including one `conj3_io` record. Nine incomplete or incompatible
alternates remain withheld. No perfect or fourth part is supplied or inherited.
Both tiers reject source/block ambiguities and notation-only alternatives.
The default regular tier remains unchanged.

Nine synthetic tests in the alternate tool pass, including four new tests for
opt-in scope, delimiter preservation, voice, conjugation subclass, missing
parts, existing flags and idempotence. All eight repair/recovery test programs
pass: **42** tests in total. CI reconstructs both tiers for both quantity
variants. Linux and platform qualification passed for code commit `a18a2d4`
(runs 36910312951 and 36910312708).

The unchanged historical filter chain independently reproduces all **three**
terminal-delimiter stem/tag pairs and all **four** present-only pairs, ignoring
only optional short marks. Principal-form probes also check the expected
verbal lemma and recorded grammar: indicative present, indicative perfect
and supine for the first tier; indicative present for all four second-tier
forms. The first probe increases expected-lemma forms from **2 to 3**, readings
from **2 to 9**, and correctly classified forms from **1 to 3**. The second
increases expected-lemma and correctly classified forms from **0 to 4**, with
**four** expected verbal readings. Other analyses on those forms are retained;
these checks do not assert complete API signature equivalence.

Private grammar-probe before/after SHA-256 are respectively
`9b84ea5c8ec884f7857b9db2a372911a784a47570b8ae17eba5b008fce6604d1`,
`c716e9e2dd2f7edf4d48c5ad24b436a1092a78e9f1eaa9cdcbe1d1417280e5bb`,
`283f9daf42f9e2ebcf4f14ab19c300baef32f86d749c7dfff28350bb934e64ea`
and `44869197d8e8ecf1ea850ac09461d45c690314ca5c62f1f37525064090414f8a`.

Letters-only/all-quantity stem output SHA-256 for the first tier are
`1ecb7a027abf1c85ae298c7aceedd34247cef76ef47929a5526be7e81f47d5c4`
and `227ea2cc6f1d51584dbf419faf35616433e9b3222bf330a7b3dc0dd413e6392f`;
for the second they are
`66dd12a665583a2498ad9383f0e8def4f06cc1dc727f46263109f668098e940e`
and `46e9d68da4070505314ac08eef264d8d854813a0b8be85137bf9407b018025dd`.
Both quantity variants build identical verbal indexes at each tier.
First-tier index/sidecar SHA-256 are
`078487ef9e566e19d9413d98d451126ddfae348129935e75ee1360fd81339c1c`
and `370b874e18b8f1ab0e0a31aede8177d8d12c464d463a8a48639d4af6241bb55e`;
second-tier hashes are
`2672da46fb5fad52125d2aac422b8ea8b49300e14b9a1ea3665acddb2d2da0ea`
and `819a232428e500def1b4f31bdf7ca05df8aa0939f44f3e2aa60fcfe9138ce591`.
Nominal indexes remain unchanged. The original 15,255-form loss subset has
**3,929** recognized forms and **7,475** readings after the first tier, then
**4,238** forms and **7,937** readings after the second, with no API errors.
The complete LISTALL results are recorded below; subset gains are not
a substitute for full recognition and reading checks.

The complete compound article associated with the earlier **54** native-prefix
gains supplies only its infinitive/conjugation and an abbreviated alternate.
Its two quotations contain objects without a verbal form. It therefore does
not prove the inherited perfect system. Private serialized article SHA-256 is
`3d0b2856a6ee841ee2a993c397dd76c14280078a45ad3a5f1680de055643b21d`.
Those gains remain inheritance-review leads. The native preverb policy,
historical filters and production corpus remain unchanged.


All six complete passes cover **1,033,579** distinct literal LISTALL forms,
API options zero, ABI 2. The terminal-delimiter tier recognizes **843,516**
forms with **2,095,178** readings: **172** gains, zero losses, and **325**
increased counts versus its predecessor. The present-only tier recognizes
**843,825** forms with **2,095,662** readings: **309** gains, zero losses,
and **327** increased counts. No count decreases occur. Identical-root
controls have zero count differences; every complete pass has zero API errors.

The before/after recorded-feature multisets retain all **515** prior rows
on changed-count forms in the first tier and all **58** in the second, adding
**601** and **484** rows respectively. These eleven recorded fields are form,
lemma, POS, workword, stem, suffix, ending, mood, case, gender and tense;
other native API attributes are outside this comparison. Private before/after
SHA-256 are respectively
`9c443e6b707535383731944c9d8f890607e15d9159cbc4549ac5fa7bdd1cc4d2`,
`d4d3f65dac2a9167e311d3525b1a0ac3b984dd85aa0df0212a48c97f0f88fff8`,
`da9d0611d9f18979ab5267de730a52dbd4db02b868cdced7a5e77b2fb6c462b5`
and `f5a80f5ddcebc340bd392006211e68a833d6a77ea5884ff2b825d024e4176a5c`.

Independent gained-form provenance distinguishes **36** direct source-lemma
forms (**60** verbal readings) from **136** native-prefix forms (**224**
readings) in the first tier. The second has **103** direct source-lemma forms
(**154** verbal readings) and **206** native-prefix forms (**308** readings).
All gained forms have verbal readings; none has another POS in these probes.
The prefixed gains remain inheritance-review leads: a native prefix and a
recognized compound lemma do not independently prove the alternate paradigm.
One prefixed lemma is returned without a delimiter, so provenance uses the
native preverb field rather than lemma punctuation alone. Private provenance
SHA-256 are
`2dd4a615d688279d30a4c8b5dd34b1e8aef3d5aacd22e599690fb56d8d2fdb3a`
and `4f1fcb69bb75d06bbaaa9e32ae306da8e8502f38006e91c50054e55e0ea3d6f7`.

The earlier **54** prefix leads were independently reprobed. All **64**
readings belong to the perfect system: fourteen indicative perfect, twelve
indicative pluperfect, twelve future perfect, twelve subjunctive perfect,
twelve subjunctive pluperfect and two perfect infinitive readings. None is a
present-system reading. An infinitive/conjugation-only reconstruction of
that compound would therefore not qualify these gains. Private grammar
SHA-256 is
`f1278bb20e06f238109cf35acc777ee7c8dcd3470dec7b3c912d0a26c179534b`.

Against the controlled rebuilt baseline the final recognition cells are:

| Recognition | Forms |
| --- | ---: |
| Both | 826,523 |
| Baseline only | 11,467 |
| Candidate only | 17,302 |
| Neither | 178,287 |

The remaining losses contain **20,100** baseline readings under **1,025**
lemma groups: **631** exact source joins, **12** notation joins, **19** native
preverb/base review leads and **363** unresolved groups. Private loss dossier
SHA-256 is
`4e0e5be0ab3f019bbbb1f5553e5dd316e6e7c6ba585a4fa4b6f891ce698502f8`.
The earlier **488** first-repair losses remain absent, with zero API errors.
These results do not settle inheritance, source rights or corpus promotion.

A subsequent narrowly bounded inchoative-present stage is recorded in
[latin-inchoative-present-qualification.md](latin-inchoative-present-qualification.md).
