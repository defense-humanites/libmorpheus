<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Qualification of a separate full Latin source candidate

On `bca050d`, the [dedicated source qualification](https://github.com/defense-humanites/libmorpheus/actions/runs/37921913936/job/113791604037)
completed successfully. [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/37921919380)
and [platform/release qualification](https://github.com/defense-humanites/libmorpheus/actions/runs/37921919408)
also passed. The older, broader lexical research workflow is a separate run;
this document does not claim its completion. The [aggregate report](qualification/latin-historical-source-candidate-bca050d.json)
contains the complete measurements and receipts.

The trial replaces one lemma's historical directives with its five bounded
source expectations: one present, two alternative perfects and two alternative
supines. An explicit compound boundary supplies the prefix, and source quantity
notation remains literal. The private source-review dossier and candidate
input are pinned to previously qualified receipts. Exactly one definition
block may be replaced; every other source byte is retained. The source delta
removes one perfect directive and adds one perfect and two supine directives.

The reconstruction tool replays all 24 letters-only stages from the original
Linux raw output. It must reproduce the qualified complete candidate source,
then the native reference build must reproduce all four original index
receipts before any global comparison begins. No receipt is substituted to
accept a different starting candidate. Both full builds retain the same
nominal indexes and retained irregular verbal inputs. Thirty-four targeted
tests pass, including the new replacement/receipt tests and the native
synthetic supine test.

## Global comparison on LISTALL

Both passes cover all **1,033,579 distinct literal forms**, with native options
zero. Every API status pair is `0,0`; used text fields are checked for
truncation. The grammatical comparison uses all eleven recorded signature
fields, including forms whose analysis counts are equal.

| Measurement | Original qualified candidate | Separate source trial |
| --- | ---: | ---: |
| Recognized forms | 847,750 | 847,750 |
| Absent forms | 185,829 | 185,829 |
| Native readings | 2,100,530 | 2,100,698 |

The comparison retains **2,100,530 readings**, removes **zero**, and adds
**168** on **80 forms**. There are no recognition gains or losses and no
equal-count multiset changes. Every added reading is classified as direct;
none is classified as a native preverb or mixed-provenance reading in this
inventory.

| API tense of added readings | Rows |
| --- | ---: |
| Unspecified (0) | 4 |
| Future (3) | 66 |
| Perfect (5) | 80 |
| Pluperfect (6) | 12 |
| Future perfect (7) | 6 |

The identical-root control compares the source trial with itself over the
same complete inventory. It retains all **2,100,698 readings**, with no
changed forms or readings. Its private difference file is empty.

## Source supine family control

The twelve expected engine-table cells cover ten distinct forms. Coverage
under the literal source lemma rises from **zero to twelve**. The family
comparison retains **40 readings**, removes none and adds **28**, changing
all ten forms. All sixteen grammatical/decomposition fields are compared
for this family. The family readings overlap the global LISTALL readings;
these measurements must not be added together.

This starting point differs from the earlier isolated diagnostic trial:
the original Linux candidate has neither expected supine, while the portable
four-directive diagnostic already has the first. The previous six-to-twelve
cell result therefore measured the second supine alone. This full candidate
comparison measures the corrected perfect and both supines together.

The supine case codes remain those of the historical engine table
(nominative/dative). They are recorded without claiming a philological
correction of those codes.

## Receipts and limits

| Artifact | SHA-256 |
| --- | --- |
| Original candidate source | `6caf089d03e62d745aebc94d1b1cc5cf06938626db4af8c794a2326ca7a94cd9` |
| Separate source trial | `92965fed7e8d30632dc9eb4118cfa671fafb95918940265b54ef7abca2d28f77` |
| Trial verbal index | `6c634ba6e3bf2a30424156cefcbc9534706761021a5819e1ded7cf12a4064856` |
| Trial verbal side index | `7e6f3b8556c5bef76304e28260d69be720d3d4240c534c672659bca96bbc78f0` |
| Private global difference | `b0913bdf8070e8196dff265fa5968ca19fb388ec42963387530a92f29c15a0b2` |
| Private full-candidate family evidence | `9a0a71c87ee9096522e4ede10ea6204bacaf1bb1d0290aaa8ff01f8f5b11c886` |

The corrected source and all four index receipts also match the local macOS
preflight. Its starting source differs from the qualified Linux reference;
only the corrected source/index receipts are compared across platforms.
No macOS global LISTALL result is claimed.

Original inputs and baseline indexes are verified unchanged. Source lemmas,
principal parts, reconstructed stems, lexical forms and individual differences
remain private. Only code, synthetic tests, categorical/numeric aggregates
and hashes are published.

This qualifies a separate trial against the original candidate on this
inventory. It neither promotes a corpus nor resolves earlier baseline-to-
candidate losses. In particular, the historical 6,789 completely lost forms
and other lexical arbitrations remain open. The comparison covers eleven
global fields, not all native attributes, and it does not attest every
generated form independently or measure forms outside LISTALL. This trial
is distinct from the previously qualified direct-present experiment; their
effects have not been combined or added. The PR remains draft and production
is unchanged.

