<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Global final-root grammatical comparison

The final present candidate qualified on `e42866d` recognizes 847,750 literal
LISTALL forms and returns 2,100,530 readings. Its five bounded spellings restore
206 forms and add 462 direct verb readings. That consecutive comparison does
not say whether those forms repair the earlier baseline-only losses, and the
previous global baseline-to-vowel comparison measured counts rather than all
grammatical multisets. A replaced reading can also leave the count unchanged.

`tools/audit-latin-global-readings.py` now compares every input's multiset of
the same eleven native ABI fields used in the consecutive trials: workword,
lemma, POS, person, number, gender, case, tense, mood, voice and degree.
Multiplicity is preserved and result order does not matter. It records the
complete recognition matrix, total reading counts, changed counts, changed
multisets at equal counts, and retained/removed/added signature occurrences.
Every successful native analysis is read structurally; API or ABI failures
abort the run instead of being treated as missing words.

Two complete passes cover the final root against itself and the controlled
baseline against the final root. The same-root control rejects a different
multiset even when both reading counts are equal. The global comparison is a
diagnostic: genuine baseline removals are measured, not accepted as a safe
corpus replacement. It neither approves reconstructed paradigms nor establishes
equivalence of analysis attributes outside these eleven fields.

## Loss diagnostics and private data

All removed and added signature occurrences are grouped by numeric public ABI
POS, tense and mechanical provenance. A reading is direct when its native
preverb field is empty, a preverb lead when all occurrences of that signature
have a preverb, and mixed when both appear. Because preverb is outside the
signature, a mixed group cannot assign which occurrence was removed. These
groups do not supply philological approval.

For forms with readings only in the baseline, the report additionally counts
removed rows by those groups and exact lemma membership in the **substituted
verbal source**. The other three retained verbal inputs are outside that
membership check. An outside lemma therefore does not mean the runtime lacks
it, and an inside lemma does not prove its required stem or paradigm exists.
Distinct lost lemmas are counted by POS without printing their identities.
These are review queues rather than asserted causes of the losses.

The owner-only private JSONL records only changed multisets, including changes
with equal counts, with their forms and removed/added signatures. Public output
contains aggregates and fingerprints only. Repository/input aliases, existing
outputs and symlinks are rejected; no dossiers, forms or lexical records are
uploaded by the workflow.

## Reproducible continuation of the qualified series

`--include-global-readings` adds the two passes to the existing five-, seven-,
nine- or eleven-pass replay. `--global-readings-only` performs those two passes
after the same source staging, index construction, quantity agreement, fixed
nominal checks and quoted/family controls, without repeating the earlier
count passes. Defaults and existing count-comparison behavior are unchanged.

The research workflow uses global-only mode for this continuation.
`tools/latin-final-present-reference.json` binds it to the exact qualified
`e42866d` source, recovered headers, both final candidate hashes and four
runtime indexes. It also requires identical final recognition and reading
totals and the previous controlled baseline totals. Thus the earlier eleven
count passes remain the reference qualification; the new CI performs two
global grammatical passes over the same candidate and indexes. It does not
claim that all thirteen passes ran again on the new revision.

Eight synthetic unit tests cover the recognition matrix, equal-count changes,
multiplicities, result order, mixed provenance, loss grouping and source
membership, duplicate/blank inputs, literal hashes, invalid inputs, native
failures and private output guards. Native integration checks include a
same-count lemma substitution and the complete global routing alongside the
existing five synthetic replay comparisons. Local Python tests and compilation
pass. Exact final recognition matrix, loss groups and native runner results
remain pending at this commit.
