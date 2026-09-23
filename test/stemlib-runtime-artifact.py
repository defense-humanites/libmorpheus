#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile


source = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()
tool = source / "tools/package-stemlib-runtime.py"


def sha(data):
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()


def run(stage, output, success=True):
    result = subprocess.run(
        [sys.executable, str(tool), "--stage", str(stage), "--output", str(output),
         "--language", "Greek"], capture_output=True, text=True)
    assert (result.returncode == 0) == success, result.stdout + result.stderr


def write_stage(stage):
    language = stage / "Greek"
    rules = [
        "vowcontr.table", "conseuph.table", "stemtypes.table", "derivtypes.table",
        "domainlist.table", "raw_preverbs.table", "ppasslist.table",
    ]
    table_inputs = []
    for name in rules:
        data = f"rule:{name}\n"
        path = language / "rule_files" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)
        table_inputs.append({"kind": "rule", "path": f"rule_files/{name}", "sha256": sha(data)})

    table_names = [
        "endtables/indices/nendind", "endtables/indices/vbendind",
        "endtables/out/noun.out", "derivs/indices/derivind",
        "derivs/out/verb.out", "derivs/ascii/verb.asc",
        "endtables/ascii/proof.asc",
    ]
    lexical_names = [
        "steminds/nomind", "steminds/nomind.lindex", "steminds/vbind",
        "steminds/vbind.lindex", "stemsrc/nom.irreg", "stemsrc/vbs.irreg",
        "lexical/verb.expanded", "lexical/oddkeys",
    ]
    outputs = {"table": [], "lexical": []}
    for group, names in (("table", table_names), ("lexical", lexical_names)):
        for name in names:
            data = f"{group}:{name}\n"
            path = language / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data)
            outputs[group].append({"path": f"Greek/{name}", "sha256": sha(data)})
    lexical_inputs = []
    for name in ("stemsrc/vbs.cmp.ml", "stemsrc/lemlist"):
        data = f"runtime:{name}\n"
        path = language / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)
        lexical_inputs.append({"role": "runtime", "path": name, "sha256": sha(data)})
    receipt = {
        "schema": 2, "language": "Greek",
        "inputs": {"table": table_inputs, "lexical": lexical_inputs},
        "outputs": outputs,
    }
    (stage / "MORPHEUS-STEMLIB-PRODUCTION-RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n")


if work.exists():
    import shutil
    shutil.rmtree(work)
stage = work / "stage"
write_stage(stage)
first = work / "first.tar.gz"
second = work / "second.tar.gz"
run(stage, first)
run(stage, second)
assert first.read_bytes() == second.read_bytes()
assert first.stat().st_mode & 0o777 == 0o644
first_receipt = json.loads(Path(str(first) + ".receipt.json").read_text())
assert first_receipt["redistribution"] == "not-qualified"
assert first_receipt["runtime_root"] == "morpheus-stemlib-greek"
payload = {item["path"] for item in first_receipt["payload"]}
assert "Greek/endtables/out/noun.out" in payload
assert "Greek/derivs/ascii/verb.asc" in payload
assert "Greek/stemsrc/vbs.cmp.ml" in payload
assert "Greek/stemsrc/lemlist" in payload
assert "Greek/endtables/ascii/proof.asc" not in payload
assert "Greek/lexical/verb.expanded" not in payload
with tarfile.open(first, "r:gz") as archive:
    names = archive.getnames()
    assert names == sorted(names)
    assert "morpheus-stemlib-greek/MORPHEUS-STEMLIB-RUNTIME-RECEIPT.json" in names
    assert "morpheus-stemlib-greek/Greek/steminds/nomind" in names
    assert all(member.mtime == 0 and member.uid == 0 and member.gid == 0
               for member in archive.getmembers())

# Independently check the assembled qualification's archive-to-receipt gate.
spec = importlib.util.spec_from_file_location(
    "stemlib_qualification", source / "tools/assemble-stemlib-qualification.py")
qualification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualification)
production_bytes = (stage / "MORPHEUS-STEMLIB-PRODUCTION-RECEIPT.json").read_bytes()
receipt_bytes = Path(str(first) + ".receipt.json").read_bytes()
assert first_receipt["payload"] == qualification.runtime_payload(
    json.loads(production_bytes), "Greek")
qualification.verify_runtime_archive(
    first, "Greek", receipt_bytes, production_bytes, first_receipt["payload"])

corrupted = work / "corrupted.tar.gz"
target_member = "morpheus-stemlib-greek/Greek/endtables/out/noun.out"
with tarfile.open(first, "r:gz") as original, tarfile.open(corrupted, "w:gz") as changed:
    for member in original.getmembers():
        data = original.extractfile(member).read()
        if member.name == target_member:
            data = b"corrupted\n"
            member.size = len(data)
        changed.addfile(member, io.BytesIO(data))
try:
    qualification.verify_runtime_archive(
        corrupted, "Greek", receipt_bytes, production_bytes, first_receipt["payload"])
except ValueError as error:
    assert str(error) == "Greek runtime archive payload digest differs"
else:
    raise AssertionError("a changed archive payload was accepted")

try:
    qualification.verify_runtime_archive(
        first, "Greek", receipt_bytes + b" ", production_bytes,
        first_receipt["payload"])
except ValueError as error:
    assert str(error) == "Greek embedded runtime receipt differs"
else:
    raise AssertionError("a changed external runtime receipt was accepted")

# Existing destinations and modified inputs must fail without replacement.
before = first.read_bytes()
run(stage, first, success=False)
assert first.read_bytes() == before
(stage / "Greek/steminds/nomind").write_text("tampered\n")
bad = work / "bad.tar.gz"
run(stage, bad, success=False)
assert not bad.exists()
assert not Path(str(bad) + ".receipt.json").exists()
assert not Path(str(bad) + ".sha256").exists()

# A symbolic-link component must not let a receipt select files indirectly.
link_stage = work / "link-stage"
write_stage(link_stage)
rules = link_stage / "Greek/rule_files"
real_rules = link_stage / "Greek/real-rules"
rules.rename(real_rules)
rules.symlink_to(real_rules.name, target_is_directory=True)
linked = work / "linked.tar.gz"
run(link_stage, linked, success=False)
assert not linked.exists()
