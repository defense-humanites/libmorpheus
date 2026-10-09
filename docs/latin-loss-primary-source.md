<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Primary source checks within Latin complete losses

On `b8aea0962a331cee56a742f04cb04b010fe4a094`, the [dedicated job](https://github.com/defense-humanites/libmorpheus/actions/runs/37932184461/job/113825344939)
passed with 45 targeted tests. The [aggregate report](qualification/latin-loss-primary-source-b8aea09.json)
contains the measurements and receipts. This qualification reconstructs the unchanged
original full candidate and checks its four native index receipts before
examining source expectations. It reuses the pinned aggregate from the
[59-lemma source review](latin-loss-source-review.md).
This is a read-only qualification; no source directive is inserted, replaced
or deleted, and no new lexical recovery is claimed.

## Source interpretation

All nine verbal cases whose isolated diagnostic replay differs from the
historical candidate satisfy the bounded primary recipes below. Their
twelve expected primary directives are already present in the candidate.
The same recipes also cover eight other cases in the 59-lemma inventory.

| Bounded source recipe | Lemmas | Primary directives |
| --- | ---: | ---: |
| Regular first conjugation, active | 14 | 14 |
| Regular first conjugation, deponent | 1 | 1 |
| Explicit compound, one perfect and one supine | 1 | 3 |
| Fourth conjugation, explicit perfect without supine | 1 | 2 |
| Total | 17 | 20 |

The first-conjugation rules require one of a fixed set of source grammar
patterns and the corresponding active or deponent headword ending. They
retain the entire literal present root, including quantities and the
explicit compound boundary. A terminal homograph marker stays in the lemma
identity and is removed only from the stem spelling.

For the third-conjugation compound, the headword supplies one explicit
boundary. The perfect must spell the complete present component after
quantity marks alone are removed for that comparison. Replacement parts
retain their literal quantities; the supine must be a complete component
under the bounded length/initial checks. No backward consonant search,
short-suffix expansion, changing component or suppletive inference is used.
Third-conjugation heads in `-io` or `-i^o` require another recipe.

The fourth-conjugation rule requires the explicitly marked headword ending
and its stated perfect slot. It creates no supine expectation. The absence
of that slot in this header is not proof that no supine is attested elsewhere.

All twenty expected primary directives match the candidate exactly.
The full diagnostic filter matches twelve of them; the difference includes
the first-conjugation root repairs and the compound principal-part repair
already made by the reconstruction stages. Therefore an isolated filter
difference is not itself evidence of a candidate regression.

The seventeen cases account for 2,225 old completely lost readings; nine of
those cases account for 559. These are historical loss counts, not newly
recovered or source-approved readings. Five additional `orth` directives
are withheld from this primary review, with no deletion or approval.

## Native families

A separate native reference contains only the twenty source expectations
plus the unchanged retained irregular inputs. Its nominal indexes must
match the original candidate. No flags are transferred from the historical
definitions to construct this reference.

| Source family | Expected cells |
| --- | ---: |
| First-conjugation presents, active or deponent | 90 |
| Compound present, perfect and supine/participle cells | 18 |
| Fourth-conjugation present and perfect | 12 |
| Total | 120 |

The cells cover 117 distinct diagnostic forms. Each expected direct reading
from the source reference must be retained in the full original candidate
on all sixteen recorded fields, including native stem/suffix/ending and
preverb decomposition. Quantity/separator removal applies to diagnostic
analysis inputs, not to the source directives or native reading comparison.
Duplicate readings retain their multiplicities.

All 120 cells are covered in both source reference and candidate, with no
missing reference reading. A separate identical-root control over the 117
forms retains all 345 readings and changes none of the eleven-field grammatical
multisets. All status pairs are \`0,0\`, and used text fields are checked for
truncation. This family qualification
does not repeat the complete LISTALL comparison or independently attest
every generated form. The supine case codes remain those of the historical
engine table, without a philological correction.

## Dependencies and remaining work

Cross-referencing the earlier native-base review by exact source-header
receipt finds six native identifier cases whose sole literal base belongs
to this primary-source group, covering 281 lost readings. This connects the
two review inventories; it neither adds losses to their totals nor approves
the composed identifiers.

The forty unclassified verbal cases have 2,978 historical lost readings:
five second-conjugation cases (254), twenty-seven third-conjugation cases
(2,171), two fourth-conjugation cases (212), and six without a terminal
conjugation digit (341). The terminal digit is a source-header grouping,
not a complete grammar interpretation. The nominal case accounts for 156
lost readings and the unjoined case for 188.

Forty verbal cases remain unclassified by these bounded recipes, alongside
the nominal and unjoined cases. Their grammar needs separate interpretation.
The thirty missing-definition lemmas, the five additional orthographic
directives, and the individual historical lost readings remain open.
Native preverb identities and the 543 unclassified native readings also
require separate evidence.

Source/candidate inputs and indexes remain unchanged. Only tools, synthetic
tests, categorical/numeric reports and hashes are published. Source
headwords, forms, stems, articles and individual dossiers stay private.
The PR remains in draft and production is unchanged.

