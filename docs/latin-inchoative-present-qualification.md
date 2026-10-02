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
The full identical-root, predecessor and controlled-baseline comparisons are
running; the unchanged subset does not imply unchanged full-corpus results.
