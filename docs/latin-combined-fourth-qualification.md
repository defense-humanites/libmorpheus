<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Combined fourth-conjugation header qualification

This experimental qualification continues the pinned Latin source-recovery
chain documented in [lexical-exports.md](lexical-exports.md). It uses the
PerseusDL lexica revision `56061ca127f4a2844980baffc5f2b6d1332897b3`, Latin
source SHA-256 `ccbd2f79db1006edc607fe51227babab6872fbdaa4e925f4c1999a3b978041ee`
and compound-header SHA-256
`85658956fa68024d032f944f7920d38fa8b424318be6454eebdb6bd74c76cc34`.
Only tools, synthetic tests, aggregates and hashes are published. Individual
lexical records and probe forms remain private; production data are unchanged.

`tools/recover-latin-combined-fourth-parts.py` has two separate opt-in stages.
Both require a unique source article, exactly two complete active `-io`
orthographies, an explicit active verbal POS, and the exact adjacent projected
grammatical fields. The `with-supine` tier accepts only `u^i and i_vi` followed
by `i_tum, 4`; `perfect-only` accepts only `i_vi or u^i` followed by `4`.
Unsupported fields, deponents, incomplete or quantity-only alternates, source
ambiguities, existing lemma blocks, and missing or repeated raw headers are
withheld. No source field is moved. The exact combined raw header must occur
once in the candidate before its new lemma block can be inserted.

The first stage recovers **one** header and adds **eight** stem records: each
complete spelling's present, two explicit perfects and supplied fourth part.
The second independently recovers **one** header and adds **six** records:
each spelling's present and two explicit perfects, with no fourth part.
Canonical and alternate quantities follow their respective source spellings.
Four synthetic tests cover both scopes, exact raw headers, homographs,
source-field preservation, ambiguity, voice, adjacency, idempotence, expected
counts, private output and no overwrite. CI reconstructs both stages in each
quantity tier.

Running the historical filter chain on each original source header reproduces
the unhandled combined raw header exactly, including the disjunction comma
normalization in the perfect-only case. Isolating the explicit `i_vi` variant
reproduces **six** stem/tag pairs for the first stage and **four** for the
second, ignoring only optional short marks. The isolated `u^i` variants remain
unhandled by those filters. Their new perfects use the source's explicit short
`u` suffix on the same fourth-conjugation base proved by the present and
`i_vi` variant; they are not claimed as historical-filter output. The filters
remain unchanged.

Independent principal-form probes find all **eight** expected-lemma forms in
the first stage (previously zero), with **18** such verbal readings, and all
**six** in the second (previously two), with **seven** such readings. Their
private before/after SHA-256 are respectively
`76a57c8ed331cdaa14268d1f08b3031cc26392d6d8dfb69bff3c9504f2ec4449`,
`bb30f56abeda7f7a04e856852284409be9aa4990489f699ef398c293d681601a`,
`ca770fadacf17f66e319b3eeb33abba5360bca19306930f472d69b1bdccdc5d2`
and `31559a93f9018d077c308f648dab7a3a4beb149857f96d272d1dbb9663908591`.
The controlled rebuilt baseline recognizes **two** expected-lemma forms in
each probe, with **two** and **three** readings respectively. These probes do
not establish complete signature equivalence to that baseline.

Letters-only/all-quantity private stem output SHA-256 for the first stage are
`0d1cb7bbed25ebec78a0a1dab0e076e1d1597b82f57f4d43c0074c85328fb8e3`
and `da67334a3fb7298cc5a3bb43431aaff0f505986233278c17b19989d825dc32c0`;
for the second they are
`ba7caeda7f08a556d6d193418d3cf816c3ad792bde6e7961ea6be1a03e6dd0f1`
and `afd48c076de0349ef1668ac1181faed153c9b1a614c74a3971e5fc1bb93209d0`.
Both quantity tiers produce identical native verbal indexes at each stage.
First-stage index/sidecar SHA-256 are
`ddb0318e0b4535fe0130f24d79bc18cfcfc7844404fb49594a0d100ac2dd5fff`
and `1b4b092e2292a38de701231f2d12ffb3ece8d61564cbf8489c27889a50f60b7f`;
second-stage hashes are
`588d825508b1477e1c120a58874e98da9ad351721ed3cf301f669c64e3ebdfd5`
and `7eca5d37736bba0ebc56618fe4df9799d02c42e24c3580eb6cd56e723ede2c3a`.
Nominal indexes remain unchanged. Both stages recognize **3,929** forms in the
original **15,255**-form loss subset with **7,426** readings and zero API errors.
Complete LISTALL qualification follows separately.

The first complete LISTALL pass recognizes **843,344** forms and returns
**2,094,545** readings: **218** forms become recognized, none becomes absent,
and all **712** changed counts increase. The second retains **843,344**
recognized forms and returns **2,094,577** readings, adding **32** readings
across **27** increased counts, without recognition-status changes. Both
identical-root controls have zero count differences; all six complete passes
have zero API errors.

An independent gained-form probe distinguishes **164** forms directly under
the recovered source lemma (**236** readings) from **54** forms with a native
preverb (**64** readings). The latter use one native prefix and a corresponding
compound source header whose projected grammatical field provides only the
infinitive/conjugation. They remain paradigm-inheritance review leads; the
base's explicit perfects and fourth part do not prove their lexical inheritance
by the compound. The controlled baseline returns **32** readings with that
same native-prefixed lemma on the gained-form probe, which is useful witness
evidence but does not fill the missing source principal parts. Private current
and baseline provenance SHA-256 are
`f14a1e5c4a45ff3c6eb5a0657b3009b05b472647c45369f95307b20ff894dbc3`
and `eb568d465f65a6d488873f27c06282406878f5f4f6ec9081fed7d72102925f4a`.
The recognition gain is therefore not described as 218 source-qualified
compound forms. The existing native preverb policy remains unchanged.

All **eight** and **six** principal probes also have their expected recorded
grammar under the expected verbal lemma: indicative present for the headwords,
indicative perfect for both supplied perfects and supine for the supplied
fourth parts. Their grammar-provenance SHA-256 are
`e77d9dade5c80ffe7988f0490251c8f55881fc77ee3c97417aa9f01ef89d5fd6`
and `acbfcc401e8d0e1059660f318db7ab8942ba5500b1dfc740e5c2e512341a68fa`.

On all changed-count forms, the before/after recorded-feature multisets
retain all **868** prior rows in the first stage and all **32** in the second,
adding **1,132** and **32** rows. The comparison includes form, lemma, POS,
workword, stem, suffix, ending, mood, case, gender and tense. It does not claim
identity for other native API attributes. Private before/after SHA-256 are
`ff2c6ca97f2d527f37b420fa0632fe6ab6daaf929e25de8306889462010b2177`,
`bed95c9d9ac3353f9a3cbd73adb44bd8b22c287d29fd3abbd124b46791c62f07`,
`4fac70f5b03b2cc402b5bd4dfbe223c736dbaab60117d9bf934b18151d889b7d`
and `71c18ef59b3f66b2b264ab8af56944834db5837d597c558ba50de7f372334811`.

Against the rebuilt controlled baseline the final recognition cells are
**826,214** both, **11,776** baseline only, **17,130** candidate only and
**178,459** neither. Remaining losses comprise **20,716** baseline readings
in **1,028** lemma groups: **632** exact source joins, **14** notation joins,
**19** native-preverb/base review leads and **363** unresolved groups. Private
loss dossier SHA-256 is
`7e28f35daa2d9ed506eea567420f83df37da8f3e3fdff2d1c0735df4e7eb262d`.
The earlier **488** first-repair losses remain absent with zero API errors.
Recognition gains and restored recorded features do not establish a production
replacement or settle the new native-prefix inheritance leads.

