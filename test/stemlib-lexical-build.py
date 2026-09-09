# SPDX-License-Identifier: AGPL-3.0-or-later
"""Qualify clean fixture output, corpus blockers, and rejected tool invocations."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

source, binary = map(lambda p: Path(p).resolve(), sys.argv[1:3])
perl = sys.argv[3] if len(sys.argv) > 3 else "perl"
work = binary / "test-stemlib-lexical-build"
if work.exists():
    shutil.rmtree(work)
work.mkdir()
expected = [row for row in (source / "test/stemlib-lexical/outputs.tsv").read_text().splitlines() if row and not row.startswith("#")]
baseline_exceptions = {
    row.split("\t")[0]
    for row in (source / "test/stemlib-lexical-baseline-exceptions.tsv").read_text().splitlines()
    if row and not row.startswith("#")
}


def run(command, expected_code=0, **kwargs):
    result = subprocess.run(list(map(str, command)), capture_output=True, **kwargs)
    if result.returncode != expected_code:
        raise AssertionError((command, result.returncode, result.stdout.decode(errors="replace"), result.stderr.decode(errors="replace")))
    return result


for language in ["Greek", "Latin"]:
    receipts = []
    comparison_receipts = []
    corpus_receipts = []
    corpus_comparison_receipts = []
    provenance_by_corpus = {}
    for pass_name in ["first", "second"]:
        tables = binary / "test-stemlib-table-build" / (language + "-" + pass_name)
        for corpus in [False, True]:
            stage = work / (language + "-" + pass_name + ("-corpus" if corpus else "-fixture"))
            shutil.copytree(tables, stage)
            command = [sys.executable, source / "tools/build-stemlib-lexical.py",
                       "--stage", stage, "--source", source / ("stemlib" if corpus else "test/stemlib-lexical"),
                       "--manifest", source / ("tools/stemlib-lexical-manifest.tsv" if corpus else "test/stemlib-lexical/inputs.tsv"),
                       "--language", language, "--tools", binary, "--perl", perl]
            if corpus:
                command += ["--corrections", source / "tools/stemlib-lexical-corrections.tsv"]
            run(command)
            receipt = stage / "MORPHEUS-STEMLIB-LEXICAL-OUTPUTS.tsv"
            report = json.loads((stage / language / "lexical/comparison.json").read_text())
            comparison_receipt = stage / "MORPHEUS-STEMLIB-LEXICAL-COMPARISON.tsv"
            assert comparison_receipt.exists()
            provenance = json.loads((stage / language / "lexical/provenance.json").read_text())
            # Relocating a clean build must not change its provenance. Keep
            # fixtures and full corpora independently pinned.
            if pass_name == "first":
                provenance_by_corpus[corpus] = provenance
            else:
                assert provenance == provenance_by_corpus[corpus]
            for tool in ["buildword", "indexnoms", "do_conj", "indexvbs"]:
                assert provenance["sha256"][tool] == hashlib.sha256((binary / tool).read_bytes()).hexdigest()
            assert provenance["sha256"]["table_provenance"] == hashlib.sha256(
                (stage / "MORPHEUS-STEMLIB-TABLE-PROVENANCE.tsv").read_bytes()).hexdigest()
            table_provenance = dict(
                row.split("\t")
                for row in (stage / "MORPHEUS-STEMLIB-TABLE-PROVENANCE.tsv").read_text().splitlines()
                if row and not row.startswith("#"))
            assert provenance["source_revision"] == table_provenance["source_revision"]
            assert provenance["toolchain"] == {
                key: table_provenance[key] for key in [
                    "compiler_name", "compiler_id", "compiler_version", "compiler_sha256",
                    "system_name", "system_processor"]
            }
            if corpus:
                assert receipt.exists() and report["complete"]
                assert report["producers"]["indexnoms"]["exit_code"] == 0
                assert report["producers"]["do_conj"]["exit_code"] == 0
                assert report["producers"]["indexvbs"]["exit_code"] == 0
                assert report["producers"]["buildword-nominal"]["exit_code"] == 0
                assert report["producers"]["buildword-verb"]["exit_code"] == 0
                assert sorted(path.name for path in (stage / language / "steminds").iterdir()) == [
                    "nomind", "nomind.lindex", "vbind", "vbind.lindex"]
                differences = {
                    path for path, value in report["baselines"].items()
                    if value["comparison"] == "different"
                }
                assert differences == {
                    path for path in baseline_exceptions if path.startswith(language + "/")
                }
                if language == "Latin":
                    assert report["producers"]["verb-source-assembly"] == {
                        "historically_omitted_inputs": ["stemsrc/vbs.mpi"],
                        "baseline": "conjfile",
                        "baseline_sha256": "e2189e136902fded363d5d12ac6aa387992d566d45362546237644ba251746c4",
                        "comparison": "notice-record-identical",
                        "notice_records_sha256": "26a298a44c9267822e5359f573e8635172c32c228ff49a2c9e0ab18298b96554",
                        "sha256": "0d754f027283ba32c183e291fec45c5e5d2a273fc796b5d524247693603e4309",
                    }
                    for name in ["nom.irreg", "vbs.irreg"]:
                        old_lines = (source / "stemlib/Latin/stemsrc" / name).read_text().splitlines()
                        new_lines = (stage / "Latin/stemsrc" / name).read_text().splitlines()
                        assert sorted(old_lines) == sorted(new_lines)
                    old_lines = set((source / "stemlib/Latin/steminds/nomind").read_text().splitlines())
                    new_lines = set((stage / "Latin/steminds/nomind").read_text().splitlines())
                    assert len(old_lines - new_lines) == 152
                    assert len(new_lines - old_lines) == 86
                    old_lines = set((source / "stemlib/Latin/steminds/vbind").read_text().splitlines())
                    new_lines = set((stage / "Latin/steminds/vbind").read_text().splitlines())
                    assert len(old_lines - new_lines) == 13
                    assert len(new_lines - old_lines) == 14
                    assert report["baselines"]["Latin/lexical/oddkeys"]["comparison"] == "identical"
                else:
                    assert report["baselines"]["Greek/stemsrc/vbs.irreg"]["comparison"] == "identical"
                    old_lines = set((source / "stemlib/Greek/stemsrc/nom.irreg").read_text().splitlines())
                    new_lines = set((stage / "Greek/stemsrc/nom.irreg").read_text().splitlines())
                    assert len(old_lines - new_lines) == 6
                    assert len(new_lines - old_lines) == 5
                    old_lines = set((source / "stemlib/Greek/steminds/nomind").read_text().splitlines())
                    new_lines = set((stage / "Greek/steminds/nomind").read_text().splitlines())
                    assert len(old_lines - new_lines) == 61
                    assert len(new_lines - old_lines) == 49
                    old_lines = set((source / "stemlib/Greek/steminds/vbind").read_text().splitlines())
                    new_lines = set((stage / "Greek/steminds/vbind").read_text().splitlines())
                    assert len(old_lines - new_lines) == 18618
                    assert len(new_lines - old_lines) == 262
                    old_lines = set((source / "stemlib/Greek/oddfile").read_text().splitlines())
                    new_lines = set((stage / "Greek/lexical/oddkeys").read_text().splitlines())
                    assert len(old_lines - new_lines) == 2
                    assert not new_lines - old_lines
                corpus_receipts.append(receipt.read_bytes())
                corpus_comparison_receipts.append(comparison_receipt.read_bytes())
                run(command, 1)  # no overlay, even after success
            else:
                rows = [row for row in receipt.read_text().splitlines() if row and not row.startswith("#")]
                assert rows == [row for row in expected if row.startswith(language + "/")]
                for row in rows:
                    name, sha = row.split("\t")
                    assert hashlib.sha256((stage / name).read_bytes()).hexdigest() == sha
                receipts.append(receipt.read_bytes())
                comparison_receipts.append(comparison_receipt.read_bytes())
                run(command, 1)  # no overlay, even after success
    assert receipts[0] == receipts[1]
    assert comparison_receipts[0] == comparison_receipts[1]
    if corpus_receipts:
        assert corpus_receipts[0] == corpus_receipts[1]
        assert corpus_comparison_receipts[0] == corpus_comparison_receipts[1]

# Invalid table provenance must fail before creating lexical staging outputs.
bad_provenance_stage = work / "bad-provenance-stage"
shutil.copytree(binary / "test-stemlib-table-build/Greek-first", bad_provenance_stage)
table_provenance = bad_provenance_stage / "MORPHEUS-STEMLIB-TABLE-PROVENANCE.tsv"
table_provenance.write_text(
    table_provenance.read_text().replace("schema\t2\n", "schema\t1\n"))
run([sys.executable, source / "tools/build-stemlib-lexical.py",
     "--stage", bad_provenance_stage, "--source", source / "stemlib",
     "--manifest", source / "tools/stemlib-lexical-manifest.tsv",
     "--corrections", source / "tools/stemlib-lexical-corrections.tsv",
     "--language", "Greek", "--tools", binary, "--perl", perl], 1)
assert not (bad_provenance_stage / "Greek/lexical").exists()
assert not (bad_provenance_stage / "Greek/steminds").exists()

# A stale correction must fail before either nominal index is created.
bad_stage = work / "bad-correction-stage"
shutil.copytree(binary / "test-stemlib-table-build/Greek-first", bad_stage)
bad_corrections = work / "bad-corrections.tsv"
correction_lines = (source / "tools/stemlib-lexical-corrections.tsv").read_text().splitlines()
first_correction = next(index for index, row in enumerate(correction_lines) if row and not row.startswith("#"))
fields = correction_lines[first_correction].split("\t")
fields[3] = "0" * 64
correction_lines[first_correction] = "\t".join(fields)
bad_corrections.write_text("\n".join(correction_lines) + "\n")
run([sys.executable, source / "tools/build-stemlib-lexical.py",
     "--stage", bad_stage, "--source", source / "stemlib",
     "--manifest", source / "tools/stemlib-lexical-manifest.tsv",
     "--corrections", bad_corrections, "--language", "Greek",
     "--tools", binary, "--perl", perl], 1)
assert not list((bad_stage / "Greek/steminds").iterdir())
assert not (bad_stage / "MORPHEUS-STEMLIB-LEXICAL-OUTPUTS.tsv").exists()

# A valid correction manifest that re-enables an invalid irregular expansion
# must retain diagnostics without publishing partial lexical success.
bad_expansion_stage = work / "bad-expansion-stage"
shutil.copytree(binary / "test-stemlib-table-build/Greek-first", bad_expansion_stage)
bad_expansion_corrections = work / "bad-expansion-corrections.tsv"
correction_lines = (source / "tools/stemlib-lexical-corrections.tsv").read_text().splitlines()
bad_expansion = next(index for index, row in enumerate(correction_lines)
                     if row.startswith("Greek\tstemsrc/irreg.vbs.src\t193\t"))
fields = correction_lines[bad_expansion].split("\t")
fields[4] = json.dumps("@  fut")
correction_lines[bad_expansion] = "\t".join(fields)
bad_expansion_corrections.write_text("\n".join(correction_lines) + "\n")
run([sys.executable, source / "tools/build-stemlib-lexical.py",
     "--stage", bad_expansion_stage, "--source", source / "stemlib",
     "--manifest", source / "tools/stemlib-lexical-manifest.tsv",
     "--corrections", bad_expansion_corrections, "--language", "Greek",
     "--tools", binary, "--perl", perl], 1)
bad_report = json.loads(
    (bad_expansion_stage / "Greek/lexical/comparison.json").read_text())
assert not bad_report["complete"]
assert bad_report["producers"]["buildword-nominal"]["exit_code"] == 0
assert bad_report["producers"]["buildword-verb"]["exit_code"] == 1
assert (bad_expansion_stage / "Greek/stemsrc/nom.irreg").exists()
assert not (bad_expansion_stage / "Greek/stemsrc/vbs.irreg").exists()
assert not list((bad_expansion_stage / "Greek/steminds").iterdir())
assert not (bad_expansion_stage / "MORPHEUS-STEMLIB-LEXICAL-OUTPUTS.tsv").exists()

# The expander must remove both owned outputs on all input failures and must
# preserve pre-existing files. Exercise cases with and without a final newline.
env = dict(os.environ, MORPHLIB=str(work / "Greek-first-fixture"), LC_ALL="C")
for index, request in enumerate(["vs,-t", "missing", "vs,hs_es"]):
    input_path = work / f"unknown-part-{index}"
    input_path.write_text(":le:probe\n:de:log reg_conj\n;" + request + "\n")
    output, odd = work / f"unknown-{index}.out", work / f"unknown-{index}.odd"
    result = run([binary / "do_conj", input_path, output, odd], 1, env=env)
    assert b"unknown principal part" in result.stderr and b"unmatched" not in result.stderr
    assert not output.exists() and not odd.exists()
for index, data in enumerate([b"", b":le:x\n:de:x missing\n;pr\n", b";pr\n",
                              b":le:x\n:de:x ../missing\n", b":le:" + b"x" * 2048,
                              b":le:x\n:de:br o_stem\n;vn,-mm,h_hs\n"]):
    input_path = work / f"bad-{index}"
    input_path.write_bytes(data)
    output = work / f"bad-{index}.out"
    odd = work / f"bad-{index}.odd"
    run([binary / "do_conj", input_path, output, odd], 1, env=env)
    assert not output.exists() and not odd.exists()
input_path = work / "no-newline"
input_path.write_text(":le:logos\n:vs:log w_stem")
run([binary / "do_conj", input_path, work / "good.out", work / "good.odd"], env=env)
assert (work / "good.out").read_bytes() == input_path.read_bytes()
run([binary / "do_conj", input_path, work / "good.out", work / "other.odd"], 1, env=env)
assert (work / "good.out").read_bytes() == input_path.read_bytes()
for tool in ["indexnoms", "indexvbs"]:
    for case, keys, diagnostic in [
            ("unknown", "missing_nominal_type masc", b"unrecognized keys: missing_nominal_type"),
            ("untyped", "masc", b"no inflectional stem type among recognized keys"),
            ("metadata", "os_ou masc editorial_note", None)]:
        probe = work / f"{tool}-{case}.input"
        probe.write_text(":le:logos\n:no:log " + keys + "\n")
        target = work / f"{tool}-{case}.out"
        result = run([binary / tool, probe, target], 1 if diagnostic else 0, env=env)
        if diagnostic:
            assert diagnostic in result.stderr
            assert not target.exists() and not Path(str(target) + ".lindex").exists()
        else:
            # Unknown editorial metadata must not become a new rejection rule.
            assert target.exists() and Path(str(target) + ".lindex").exists()
    output = work / tool
    sidecar = work / (tool + ".lindex")
    sidecar.write_text("sentinel")
    run([binary / tool, input_path, output], 1, env=env)
    assert sidecar.read_text() == "sentinel" and not output.exists()

# Keep the diagnostic-only audit path covered after the complete corpora cease
# to provide active blocker reports.
audit_input = work / "audit.input"
audit_input.write_text(":le:logos\n:no:log missing_nominal_type masc\n")
audit_output = work / "audit.json"
audit_command = [sys.executable, source / "tools/audit-stemlib-lexical.py",
                 "--stage", work / "Greek-first-fixture", "--input", audit_input,
                 "--tool", binary / "indexnoms", "--producer", "indexnoms",
                 "--language", "Greek", "--output", audit_output]
run(audit_command, 1)
audit = json.loads(audit_output.read_text())
assert audit["diagnostic_only"] and audit["records"] == 1
assert audit["batch_only_failures"] == []
assert len(audit["failures"]) == 1
assert audit["failures"][0]["lemma"] == "logos"
assert "missing_nominal_type" in audit["failures"][0]["diagnostics"]
original = audit_output.read_bytes()
run(audit_command, 2)
assert audit_output.read_bytes() == original
print("Greek/Latin fixture and complete-corpus receipts match independent clean builds.")
