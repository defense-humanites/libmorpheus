<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Latin complete-loss source and native-base review

The [dedicated job](https://github.com/defense-humanites/libmorpheus/actions/runs/37927335700/job/113809311246)
passed on `8462af283d245f08029c32d6d1827dc9442cd9cf`, including 55 targeted
tests. The [aggregate report](qualification/latin-loss-source-review-8462af2.json)
archives the measurements and input receipts. This review uses the original
qualified candidate, not the separate corrected source trial.

## Exact reproduction

The workflow reconstructs the original candidate and checks all four native
index receipts before comparing all 1,033,579 distinct literal LISTALL forms.
The baseline has 2,048,328 readings; the candidate has 2,100,530. The eleven-field
comparison retains 2,006,554 readings, removes 41,774 and adds 93,976. Every
native status pair is `0,0`; used text fields are checked for truncation.

The private global difference reproduces SHA-256
`08f0aca20f35eecf95f24a50690ad91a35a139663f558570d9ea86ea07f8bd52`.
Reanalysis of all 6,789 completely lost forms reproduces the 133-lemma,
11,005-reading source dossier, SHA-256
`a4be9ccc97383f48f4ba94bc4e23092e17b729a685eb01c5242d2bfac9c4ba1a`.
The comparison inputs and private output dossier occupy separate directories;
a regression test enforces that privacy boundary.

| Definition state | Lemmas | Lost readings |
| --- | ---: | ---: |
| Changed definition multisets | 59 | 5,547 |
| No final definitions | 30 | 2,672 |
| No definitions in either expanded inventory | 44 | 2,786 |

## Source review of 59 changed-definition lemmas

Literal source joins find 57 verbal articles, one nominal article and one
unjoined lemma. All 58 unique joins have literal headword identity. Replaying
each isolated header through the first three historical filters and the
qualified diagnostic lexer matches the full diagnostic multiset for all 57
verbal articles. The nominal article differs; the unjoined lemma cannot be
replayed from a matched article.

Forty-eight isolated multisets match the raw original candidate. Nine verbal
cases differ, accounting for 559 lost readings, and the nominal case also
differs. These nine verbal cases are a bounded next review set, not approved
repairs. The replay establishes filter behavior; source grammar still needs
independent interpretation.

None of the 58 joined articles satisfies the two currently implemented
independent recipes (bounded fourth-conjugation alternative perfects or
explicit third-conjugation compounds with two perfects and two supines).
Their status is unclassified, not rejected. There are zero definition pairs
classified as quantity-only substitutions by the existing bounded rule.

Thirty-one cases have at least one article surface lead. Counts below are
distinct form matches per lemma and route, not additional recovered readings;
a form may occur in several routes.

| Route | Literal matches | Matches after notation removal |
| --- | ---: | ---: |
| Whole full orthography | 1 | 5 |
| Latin-labelled quotation tokens | 86 | 1 |
| Whole reference | 0 | 0 |

Only whole full orthographies, Latin-labelled quotation tokens and whole
references are searched. Foreign-language descendants are excluded.
Notation removal strips only quantity/separator marks and does not establish
literal identity. A citation occurrence does not attribute the form to the
article lemma or establish its grammar. No repair is inferred from these
leads. The private source-review receipt is
`a3f9c53ad990b6bdfd4d2112bf4f1a55a0e7af1b1d124d6bc681f911e756e05c`.

## Native dependency review of 44 definition-free identifiers

For every lost native reading, the tool first tests whether its identifier
starts with the exact recorded preverb followed by a hyphen. Only that literal
boundary permits a base identifier. It then constructs a diagnostic input
from the recorded stem, suffix and ending, stripping quantity/separator marks
only for reanalysis. Direct peers must share the exact base identifier,
nine grammatical fields and literal stem/suffix/ending. This is a native
dependency diagnostic, not source attestation of the reconstructed form.

Of 2,786 readings across 44 native identifiers, 2,243 have a literal base
relation, spanning 16 distinct bases. Every one has an exact direct peer in
the baseline and none in the candidate. The remaining 543 readings have no
accepted literal identifier decomposition and remain unclassified.

| Literal base state | Base in complete-loss dossier | Baseline-only peer readings |
| --- | --- | ---: |
| Changed definitions, unique source article | Changed definitions | 1,641 |
| Changed definitions, unique source article | No | 215 |
| No final definitions, no source join | No final definitions | 256 |
| No final definitions, unique source article | No final definitions | 129 |
| No final definitions, unique source article | No | 2 |

The 1,641 readings overlap dependencies of the changed-definition group;
they must not be counted as additional losses or recoveries. Some base lemmas
remain recognized through other readings and therefore do not appear in the
complete-loss dossier. The private dependency-review receipt is
`eca0df17b98f95ce89c43e7ab64dd924d53a69ca06edc19216e86237fcfafc40`.
Failure to find a peer or source join is not proof of non-attestation.

## Remaining arbitration

The subsequent [primary-source qualification](latin-loss-primary-source.md)
covers all nine verbal replay differences and eight additional cases. Its
twenty expected primary directives already match the original candidate,
with 120 native family cells covered. This qualifies those directives without
settling every historical lost reading or the additional orthographic records.
Forty verbal grammar cases remain unclassified by those bounded recipes,
alongside the nominal/unjoined cases and the 30 missing-definition lemmas.
Native losses should be reviewed with their base dependencies; their
composed lexical identity still requires source support. The 543 unclassified
native readings require their own identifier/decomposition investigation.

The later [coordinated-supine trial](latin-third-supine-alternatives.md)
screens the 27 remaining third-conjugation headers and inserts three missing
literal source supines across two lemmas in a separate candidate. It covers
30 source-family cells and adds 649 LISTALL readings, with 171 newly recognized
forms and no removed eleven-field readings. Of the additions, 215 are direct
and 434 carry native preverbs; composed identities and reading-by-reading
recovery of the old loss dossier remain unqualified. The other 25
third-conjugation headers stay outside this bounded recipe.

No new lexical recovery is qualified by this earlier read-only review. The earlier separate
source trial and present-only composition control retain their own receipts
and are not combined here. Other removed readings on still-recognized forms,
equal-count multiset changes, the final source selector and corpus
qualification remain open. Source inputs and native indexes are unchanged.
Only code, synthetic tests, aggregate categories and hashes are public;
articles, forms, lemmas, stems and private dossiers are withheld. The PR stays
in draft and no candidate is promoted to production.

