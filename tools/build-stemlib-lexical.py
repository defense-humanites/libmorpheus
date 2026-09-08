#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build lexical indexes on a freshly produced, verified table staging tree.

The source manifest is ordered: language, role, path, sha256. Prepared irregular
sources are inputs at this boundary. This does not reconstruct lexicon exports.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(args):
    stage = args.stage.resolve()
    source = args.source.resolve()
    language = args.language
    root = stage / language
    if stage == source or source in stage.parents:
        raise ValueError("stage must be outside the source tree")
    receipt = stage / "MORPHEUS-STEMLIB-TABLE-OUTPUTS.tsv"
    received = set()
    for row in receipt.read_text().splitlines():
        if not row or row.startswith("#"):
            continue
        name, expected = row.split("\t")
        if not name.startswith(language + "/") or ".." in Path(name).parts:
            raise ValueError("invalid table receipt path")
        if name in received:
            raise ValueError("duplicate table receipt path")
        received.add(name)
        if digest(stage / name) != expected:
            raise ValueError("table receipt mismatch: " + name)
    if not received:
        raise ValueError("empty table receipt")
    input_receipt = stage / "MORPHEUS-STEMLIB-INPUTS.tsv"
    input_count = 0
    for row in input_receipt.read_text().splitlines():
        if not row or row.startswith("#"):
            continue
        lang, status, kind, name, expected = row.split("\t")
        if lang != language or status != "active" or Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("invalid staged table input receipt")
        if digest(root / name) != expected:
            raise ValueError("staged table input checksum mismatch: " + name)
        input_count += 1
    if not input_count:
        raise ValueError("empty table input receipt")
    rows = []
    seen = set()
    role_by_input = {}
    roles = {"nominal", "verb", "constraints", "constraint-tool", "assembly-baseline",
             "unavailable", "excluded"}
    for row in args.manifest.read_text().splitlines():
        if not row or row.startswith("#"):
            continue
        lang, role, name, expected = row.split("\t")
        if lang not in {"Greek", "Latin"} or role not in roles:
            raise ValueError("invalid lexical manifest classification")
        if Path(name).is_absolute() or ".." in Path(name).parts or not name:
            raise ValueError("invalid lexical manifest path")
        if (lang, name) in seen:
            raise ValueError("duplicate lexical input")
        seen.add((lang, name))
        role_by_input[(lang, name)] = role
        path = source / lang / name
        if role == "unavailable":
            if path.exists() or expected != "-":
                raise ValueError("unavailable input classification is stale")
        elif not re.fullmatch("[0-9a-f]{64}", expected) or digest(path) != expected:
            raise ValueError("lexical source checksum mismatch: " + str(path))
        if lang == language:
            rows.append((role, name, expected))
    if any(name.startswith("stemsrc/") for _, name, _ in rows):
        for lang in ["Greek", "Latin"]:
            discovered = {p.relative_to(source / lang).as_posix()
                          for p in (source / lang / "stemsrc").rglob("*") if p.is_file()}
            declared = {name for row_lang, name in seen if row_lang == lang and name.startswith("stemsrc/")
                        and (source / lang / name).exists()}
            if discovered != declared:
                raise ValueError("lexical source inventory mismatch: " + lang)
    if not any(role == "nominal" for role, _, _ in rows) or not any(role == "verb" for role, _, _ in rows):
        raise ValueError("both nominal and verb input lists are required")
    work = root / "lexical"
    work.mkdir()  # refuse reuse, including failed attempts
    (root / "steminds").mkdir()
    for role, name, expected in rows:
        if role in {"assembly-baseline", "unavailable", "excluded"}:
            continue
        target = root / name
        if target.exists():
            raise ValueError("lexical input would overlay staged file: " + name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source / language / name).read_bytes())
        if digest(target) != expected:
            raise ValueError("staged lexical checksum mismatch: " + name)
    correction_rows = []
    if args.corrections:
        previous = None
        corrected = set()
        for row in args.corrections.read_text().splitlines():
            if not row or row.startswith("#"):
                continue
            fields = row.split("\t", 4)
            if len(fields) != 5:
                raise ValueError("invalid lexical correction")
            lang, name, line_text, expected, replacement_json = fields
            if (lang not in {"Greek", "Latin"} or Path(name).is_absolute() or
                    ".." in Path(name).parts or role_by_input.get((lang, name)) != "nominal"):
                raise ValueError("invalid lexical correction target")
            try:
                line_number = int(line_text)
                replacement = json.loads(replacement_json)
            except (ValueError, json.JSONDecodeError):
                raise ValueError("invalid lexical correction value") from None
            location = (lang, name, line_number)
            if line_number < 1 or location in corrected or (previous and location <= previous):
                raise ValueError("unordered or duplicate lexical correction")
            if not re.fullmatch("[0-9a-f]{64}", expected) or not isinstance(replacement, str):
                raise ValueError("invalid lexical correction fields")
            if "\n" in replacement or "\r" in replacement:
                raise ValueError("multiline lexical correction")
            original_lines = (source / lang / name).read_bytes().splitlines(keepends=True)
            if line_number > len(original_lines):
                raise ValueError("lexical correction line is absent")
            original = original_lines[line_number - 1].rstrip(b"\r\n")
            if hashlib.sha256(original).hexdigest() != expected:
                raise ValueError("lexical correction source mismatch")
            corrected.add(location)
            previous = location
            if lang == language:
                target = root / name
                target_lines = target.read_bytes().splitlines(keepends=True)
                current = target_lines[line_number - 1]
                ending = current[len(current.rstrip(b"\r\n")):]
                target_lines[line_number - 1] = replacement.encode() + ending
                target.write_bytes(b"".join(target_lines))
                correction_rows.append(row)
        if not corrected:
            raise ValueError("empty lexical correction manifest")
        (work / "corrections.tsv").write_text(
            "# SPDX-License-Identifier: MPL-2.0\n" +
            "\n".join(correction_rows) + ("\n" if correction_rows else ""))
    (work / "inputs.tsv").write_text("# SPDX-License-Identifier: MPL-2.0\n" + "".join(
        f"{language}\t{role}\t{name}\t{sha}\n" for role, name, sha in rows))
    env = dict(os.environ, MORPHLIB=str(stage), LC_ALL="C", LANG="C", TZ="UTC")
    provenance = {
        "schema": 1,
        "language": language,
        "environment": {"LC_ALL": "C", "LANG": "C", "TZ": "UTC"},
        "python_version": sys.version,
        "sha256": {
            "recipe": digest(Path(__file__)),
            "python": digest(Path(sys.executable)),
            "lexical_manifest": digest(args.manifest),
            "lexical_inputs": digest(work / "inputs.tsv"),
            "table_inputs": digest(input_receipt),
            "table_outputs": digest(receipt),
            "table_provenance": digest(stage / "MORPHEUS-STEMLIB-TABLE-PROVENANCE.tsv"),
            **{name: digest(args.tools / name) for name in ["indexnoms", "do_conj", "indexvbs"]},
        },
    }
    if args.corrections:
        provenance["sha256"]["lexical_corrections"] = digest(args.corrections)
    if any(role == "constraint-tool" for role, _, _ in rows):
        perl_path = shutil.which(args.perl)
        if perl_path is None:
            raise ValueError("constraint interpreter unavailable: " + args.perl)
        provenance["sha256"]["perl"] = digest(Path(perl_path))
    (work / "provenance.json").write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
    options = ["-L"] if language == "Latin" else []
    report = {"language": language, "producers": {}, "baselines": {}}

    def run(label, command, output=None):
        result = subprocess.run(command, cwd=root, env=env, capture_output=True)
        diagnostics = result.stderr.decode("utf-8", "replace").replace(str(stage), "<stage>")
        (work / (label + ".log")).write_text(diagnostics)
        if output is not None and result.returncode == 0:
            output.write_bytes(result.stdout)
        report["producers"][label] = {"exit_code": result.returncode}
        return result.returncode == 0

    nominal = [root / name for role, name, _ in rows if role == "nominal"]
    constraint_tools = [root / name for role, name, _ in rows if role == "constraint-tool"]
    nominal_input = work / "nominal.input"
    if constraint_tools:
        if len(constraint_tools) != 1:
            raise ValueError("exactly one constraint tool is supported")
        prepared = run("constraints", [args.perl, str(constraint_tools[0]), *map(str, nominal)], nominal_input)
    else:
        nominal_input.write_bytes(b"".join(path.read_bytes() for path in nominal))
        prepared = True
    if prepared:
        run("indexnoms", [str(args.tools / "indexnoms"), *options, str(nominal_input), str(root / "steminds/nomind")])
    verb_input = work / "verb.input"
    unavailable = [name for role, name, _ in rows if role == "unavailable"]
    assembly_baselines = [(name, source / language / name)
                          for role, name, _ in rows if role == "assembly-baseline"]
    data = b"".join((root / name).read_bytes() for role, name, _ in rows if role == "verb")
    if language == "Latin":
        data = re.sub(rb"([a-z])([aei])_v[ \t]+perfstem", rb"\1\t\2vperf", data)
    assembled = not unavailable
    if unavailable:
        if len(assembly_baselines) != 1:
            report["producers"]["verb-source-assembly"] = {
                "blocked_missing_inputs": unavailable,
                "reason": "exactly one historical assembly baseline is required",
            }
        else:
            baseline_name, baseline = assembly_baselines[0]
            assembled = data == baseline.read_bytes()
            report["producers"]["verb-source-assembly"] = {
                "historically_omitted_inputs": unavailable,
                "baseline": baseline_name,
                "comparison": "identical" if assembled else "different",
                "sha256": hashlib.sha256(data).hexdigest(),
            }
    if assembled:
        verb_input.write_bytes(data)
        if run("do_conj", [str(args.tools / "do_conj"), *options, str(verb_input), str(work / "verb.expanded"), str(work / "oddkeys")]):
            run("indexvbs", [str(args.tools / "indexvbs"), *options, str(work / "verb.expanded"), str(root / "steminds/vbind")])
    outputs = [path for path in (root / "steminds").glob("*") if path.is_file()]
    outputs += [path for path in [work / "verb.expanded", work / "oddkeys"] if path.exists()]
    success = all(report["producers"].get(name, {}).get("exit_code") == 0 for name in ["indexnoms", "do_conj", "indexvbs"])
    report["complete"] = success
    comparison_rows = []
    for path in sorted(outputs):
        relative = path.relative_to(stage).as_posix()
        baseline = source / relative
        if relative == f"{language}/lexical/oddkeys" and (source / language / "oddfile").exists():
            baseline = source / language / "oddfile"
        output_sha = digest(path)
        baseline_sha = digest(baseline) if baseline.exists() else None
        comparison = "identical" if baseline_sha == output_sha else "different" if baseline_sha else "unavailable"
        report["baselines"][relative] = {
            "sha256": output_sha,
            "baseline": baseline.relative_to(source).as_posix() if baseline.exists() else None,
            "baseline_sha256": baseline_sha,
            "comparison": comparison,
        }
        comparison_rows.append(f"{relative}\t{output_sha}\t{baseline_sha or '-'}\t{comparison}\n")
    (work / "comparison.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (stage / "MORPHEUS-STEMLIB-LEXICAL-COMPARISON.tsv").write_text(
        "# SPDX-License-Identifier: MPL-2.0\n"
        "# path\toutput_sha256\tbaseline_sha256\tcomparison\n" + "".join(comparison_rows))
    if success:
        (stage / "MORPHEUS-STEMLIB-LEXICAL-OUTPUTS.tsv").write_text(
            "# SPDX-License-Identifier: MPL-2.0\n" + "".join(f"{p.relative_to(stage).as_posix()}\t{digest(p)}\n" for p in sorted(outputs)))
    return 0 if success else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--corrections", type=Path)
    parser.add_argument("--language", choices=["Greek", "Latin"], required=True)
    parser.add_argument("--tools", type=lambda value: Path(value).resolve(), required=True)
    parser.add_argument("--perl", default="perl")
    args = parser.parse_args()
    try:
        raise SystemExit(build(args))
    except (OSError, ValueError) as error:
        parser.exit(1, f"lexical build: {error}\n")
