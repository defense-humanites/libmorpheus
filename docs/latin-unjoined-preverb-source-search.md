<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# Full-source search for an unjoined native preverb lemma

The review on `f3f8c15` binds 123 added native-preverb readings to one other
lemma with no original final-candidate definition and no joined article in
the recovered-header index. This does not establish source absence: that
index excludes projection-error entries and only indexes two literal routes.

`tools/search-latin-unjoined-preverb-source.py` verifies that private review's
receipt and exact one-lemma/123-reading scope. It reads every `entryFree` in
the pinned Latin TEI, irrespective of header projection success. Its search
routes are deliberately bounded:

- entry keys, using the explicitly labelled terminal-digit homograph convention;
- complete direct and nested `orth` strings, never their first token;
- complete `ref` text, labelled as reference evidence rather than identity;
- direct orthographies with the entry-key homograph suffix, as a separate route.

Literal strings, notation leads and case/homograph/notation leads remain
separate categories. No lossy comparison changes a lemma, stem or identity.
Phrases, coordinated alternatives, unresolved entities and unsupported strings
are not reduced to a plausible token. Nested orthography and references do
not become header grammar evidence. The search is not an audit of every prose
token, every XML attribute, corpus citation or external dictionary: an empty
result is not proof of nonattestation. A hit also is not lexical approval.

Matched articles, route strings and source IDs remain in a private 0600
dossier outside the repository. CI prints only article/occurrence counts,
categorical routes and hashes. Input receipts are checked again afterwards;
no candidate, index or production data is modified. Eight synthetic tests
cover exact keys, homograph separation, lossy leads, nested/reference routing,
whole-string boundaries, projection failures, privacy, scope and receipts.
