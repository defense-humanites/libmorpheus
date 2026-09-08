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
blockers = json.loads((source / "test/stemlib-lexical/blockers.json").read_text())["reports"]
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
            run(command, 1 if corpus and language == "Latin" else 0)
            receipt = stage / "MORPHEUS-STEMLIB-LEXICAL-OUTPUTS.tsv"
            report = json.loads((stage / language / "lexical/comparison.json").read_text())
            comparison_receipt = stage / "MORPHEUS-STEMLIB-LEXICAL-COMPARISON.tsv"
            assert comparison_receipt.exists()
            provenance = json.loads((stage / language / "lexical/provenance.json").read_text())
            # Relocating a clean build must not change its provenance. Keep
            # successful fixtures and blocked full corpora independently pinned.
            if pass_name == "first":
                provenance_by_corpus[corpus] = provenance
            else:
                assert provenance == provenance_by_corpus[corpus]
            for tool in ["indexnoms", "do_conj", "indexvbs"]:
                assert provenance["sha256"][tool] == hashlib.sha256((binary / tool).read_bytes()).hexdigest()
            assert provenance["sha256"]["table_provenance"] == hashlib.sha256(
                (stage / "MORPHEUS-STEMLIB-TABLE-PROVENANCE.tsv").read_bytes()).hexdigest()
            if corpus:
                log = (stage / language / "lexical/indexnoms.log").read_text()
                if language == "Latin":
                    assert not receipt.exists() and not report["complete"]
                    assert report["producers"]["indexnoms"]["exit_code"] == 1
                    assert "as_a" in log
                    assert report["producers"]["verb-source-assembly"] == {
                        "historically_omitted_inputs": ["stemsrc/vbs.mpi"],
                        "baseline": "conjfile",
                        "comparison": "identical",
                        "sha256": "e2189e136902fded363d5d12ac6aa387992d566d45362546237644ba251746c4",
                    }
                    assert report["producers"]["do_conj"]["exit_code"] == 0
                    assert report["producers"]["indexvbs"]["exit_code"] == 0
                    assert sorted(path.name for path in (stage / language / "steminds").iterdir()) == [
                        "vbind", "vbind.lindex"]
                    differences = {
                        path for path, value in report["baselines"].items()
                        if value["comparison"] == "different"
                    }
                    assert differences == {path for path in baseline_exceptions if path.startswith("Latin/")}
                    old_lines = set((source / "stemlib/Latin/steminds/vbind").read_text().splitlines())
                    new_lines = set((stage / "Latin/steminds/vbind").read_text().splitlines())
                    assert len(old_lines - new_lines) == 13
                    assert len(new_lines - old_lines) == 14
                    assert report["baselines"]["Latin/lexical/oddkeys"]["comparison"] == "identical"
                else:
                    assert receipt.exists() and report["complete"]
                    assert report["producers"]["indexnoms"]["exit_code"] == 0
                    assert sorted(path.name for path in (stage / language / "steminds").iterdir()) == [
                        "nomind", "nomind.lindex", "vbind", "vbind.lindex"]
                    assert report["producers"]["do_conj"]["exit_code"] == 0
                    assert report["producers"]["indexvbs"]["exit_code"] == 0
                    differences = {
                        path for path, value in report["baselines"].items()
                        if value["comparison"] == "different"
                    }
                    assert differences == {path for path in baseline_exceptions if path.startswith("Greek/")}
                    old_lines = set((source / "stemlib/Greek/steminds/nomind").read_text().splitlines())
                    new_lines = set((stage / "Greek/steminds/nomind").read_text().splitlines())
                    assert len(old_lines - new_lines) == 55
                    assert len(new_lines - old_lines) == 44
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
                if pass_name == "first":
                    for baseline in [item for item in blockers if item["language"] == language]:
                        producer = baseline["producer"]
                        audit_output = work / f"{language}-{producer}-audit.json"
                        audit_command = [sys.executable, source / "tools/audit-stemlib-lexical.py",
                                         "--stage", stage, "--input", stage / language / "lexical" /
                                         ("verb.input" if producer == "do_conj" else "nominal.input"),
                                         "--tool", binary / producer, "--producer", producer,
                                         "--language", language, "--output", audit_output]
                        run(audit_command, 1)
                        audit = json.loads(audit_output.read_text())
                        assert audit["diagnostic_only"]
                        assert audit["sha256"]["input"] == baseline["input_sha256"]
                        for key in ["records", "failures", "batch_only_failures"]:
                            assert audit[key] == baseline[key], (language, producer, key)
                        original = audit_output.read_bytes()
                        run(audit_command, 2)
                        assert audit_output.read_bytes() == original
                    if language == "Latin":
                        assert not receipt.exists()
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
print("Greek/Latin fixture receipts and the complete Greek corpus match independent clean builds; the Latin nominal blocker remains fail-closed.")
