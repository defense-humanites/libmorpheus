<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Remaining Latin extraction blockers

The qualified missing-definition review contains eight unique verbal source
headers outside the seven terminal-digit cases: two with multiple `itype`
fields, two without one, three with another field structure and one with an
infinitive spelling. Their completely lost readings total 914. This review
does not add definitions or change a candidate.

`tools/review-latin-extraction-blockers.py` requires the qualified review
receipt, revalidates each complete header and its grammar profile against the
pinned TEI, and reproduces the original four-filter transcript exactly.
For each stage it reports literal `itype` retention with multiplicity,
structural categories of output fields, preservation of the headword prefix,
counts of bound stem directives and presence of stderr. Lexer ECHO text and
empty lemma blocks do not count as definitions. Retention is an observation
of output bytes, not proof that a filter interpreted the grammar correctly.

For a header with multiple `itype` occurrences, a separately labelled trial
retains each original occurrence in turn and removes the others. Every other
field, its order and its notation remain intact. Each trial runs in fresh
historical filter processes and reports whether it emits the missing literal
lemma, only another lemma, or no definitions. This isolates interactions
between fields without choosing a winning field, inferring a conjugation,
or qualifying any emitted stem. Trial counts are not unique lemma counts or
native reading recoveries. No corresponding native index is built.

Literal headers, traces and trial definitions remain in a separate exclusive
mode-0600 private dossier outside the repository. Public reports contain only
fixed structural categories, booleans, directive prefixes, counts and hashes.
The workflow uploads no private artifact. It retains the previous review
receipt and the seven-case experiment unchanged, then runs this review.
Actual results and subsequent source arbitration are recorded in PR #18.
