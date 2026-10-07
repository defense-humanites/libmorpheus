<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Counterfactual probe of terminal conjugation digits

The qualified private missing-definition review identifies seven verbal
headers with one principal-part `itype` ending in an explicit conjugation
digit. Their completely lost native readings total 928. This experiment
does not introduce a recovery rule or modify the final candidate.

`tools/probe-latin-terminal-conjugation.py` requires the qualified receipts
of both private dossiers, the candidate, and both expanded assemblies. It
revalidates the headers against the pinned source, reproduces the original
four-filter transcripts, and records aggregate survival of the original
field and headword through the filters. No individual header is printed.

In a separately labelled counterfactual, the tool replaces only the one
`itype` projection with its terminal digit. Other header fields stay intact.
It replays the four historical filters in fresh processes. Emitted directives
must remain under the same literal lemma; another lemma or an existing
candidate block aborts the probe. New blocks are appended to a private copy
of the final verbal source; no witness stem or definition is copied.

The independent native index build retains the three other verbal inputs
and the final nominal indexes. The tool probes the literal source headword
as a direct first-person singular present indicative with the appropriate
active/passive morphology. A missing expected reading remains a measured
failure of this counterfactual, not an automatic approval or silent omission.

Every selected lost form is reprobed against the baseline to reproduce the
exact target multiset and its multiplicities. It must still have no reading
in the qualified final candidate. Counterfactual readings are compared with
the 928 target signatures, including all eleven qualified fields. Public
aggregates distinguish exact recoveries, still-missing readings, recognition
of forms, and other readings; these quantities are not interchangeable.

Simplifying principal parts to a class digit discards source information.
In particular, historical derivative directives can extrapolate regular
perfects and supines. Expanded definition types are reported explicitly.
Such outputs are diagnostic evidence, not source-supported past stems, and
must not be promoted to a recovery merely because a source headword or lost
form becomes recognized. This experiment does not establish a complete
paradigm or global absence of regressions.

The private candidate, native copy, transcripts and per-form probes remain
outside the repository and inputs, under a mode-0700 directory with an
exclusive mode-0600 probe file. Nothing is uploaded as a CI artifact. Only
tools, synthetic tests, aggregate counts and hashes are published. The final
candidate's original four indexes are verified unchanged after the experiment.

The workflow repeats the existing global qualification and the two private
reviews before this probe. Actual results and next source-arbitration steps
are recorded in PR #18 after the run completes.
