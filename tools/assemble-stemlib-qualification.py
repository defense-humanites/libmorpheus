# SPDX-License-Identifier: AGPL-3.0-or-later
"""Assemble and validate the deterministic stemlib qualification evidence."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET


REQUIRED_RUNTIME_TESTS = frozenset({
    "alpheios_greek_fixtures",
    "dialect_option_context",
    "gener_core_fixtures",
    "gener_corpus",
    "gener_service_differential",
    "legacy_fixtures",
    "public_analysis",
    "public_context",
    "public_fixtures",
    "public_generation",
    "public_request_options",
    "public_result",
    "stemlib_qualification_junit",
})


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [
        line.split("\t")
        for line in path.read_text().splitlines()
        if line and not line.startswith("#")
    ]


def comparison_counts(path):
    parsed = rows(path)
    if any(len(row) != 4 for row in parsed):
        raise ValueError("invalid comparison report: " + str(path))
    return parsed, Counter(row[3] for row in parsed)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def current_revision(source):
    commit = subprocess.run(
        ["git", "-C", source, "rev-parse", "--verify", "HEAD"],
        check=True, capture_output=True, text=True).stdout.strip()
    require(len(commit) == 40 and all(character in "0123456789abcdef"
                                       for character in commit),
            "invalid source revision")
    dirty = subprocess.run(
        ["git", "-C", source, "status", "--porcelain", "--untracked-files=no"],
        check=True, capture_output=True, text=True).stdout
    return commit + ("+dirty" if dirty else "")


def ctest_result(ctest_junit):
    suite = ET.parse(ctest_junit).getroot()
    require(suite.tag == "testsuite", "invalid CTest JUnit root")
    testcases = suite.findall("testcase")
    test_names = [case.get("name") for case in testcases]
    require(None not in test_names and len(test_names) == len(set(test_names)),
            "invalid or duplicate CTest case")
    require(REQUIRED_RUNTIME_TESTS <= set(test_names),
            "required runtime qualification tests are missing")
    require(suite.get("tests") == str(len(testcases)) and
            suite.get("errors", "0") == "0" and
            suite.get("failures") == "0" and suite.get("disabled") == "0" and
            suite.get("skipped") == "0" and all(
                case.get("status") == "run" and
                not any(case.find(kind) is not None
                        for kind in ["error", "failure", "skipped"])
                for case in testcases), "CTest qualification did not pass")
    return {
        "all_passed": True,
        "required_tests": sorted(REQUIRED_RUNTIME_TESTS),
        "tests": len(testcases),
    }


def build(source, build_root, ctest_junit, output):
    if output.exists():
        output.unlink()
    table_root = build_root / "test-stemlib-table-build"
    lexical_root = build_root / "test-stemlib-lexical-build"
    production_root = build_root / "stemlib-production"

    runtime_ctest = ctest_result(ctest_junit)

    summary_path = table_root / "baseline-summary.tsv"
    difference_path = table_root / "baseline-differences.tsv"
    alpheios_path = lexical_root / "alpheios-reference-comparison.tsv"
    expected_summary = {
        "Greek": ["357", "156", "0"],
        "Latin": ["211", "73", "0"],
    }
    summary_rows = rows(summary_path)
    require(len(summary_rows) == 3 and
            summary_rows[0] == ["language", "outputs", "binary_differences",
                                "text_or_index_differences"],
            "invalid table baseline summary header")
    require({row[0]: row[1:] for row in summary_rows[1:]} == expected_summary,
            "unexpected table baseline summary")

    difference_rows = rows(difference_path)
    require(difference_rows[0] == ["path", "reason"],
            "invalid table baseline difference header")
    require(len(difference_rows) == 230 and all(
        row[1:] == ["explicit-binary-serialization"]
        for row in difference_rows[1:]), "unexpected table baseline differences")
    binary_exception_path = source / "test/stemlib-binary-baseline-exceptions.tsv"
    binary_exceptions = rows(binary_exception_path)
    require(difference_rows[1:] == binary_exceptions,
            "table difference report does not match its exception manifest")
    lexical_exception_path = source / "test/stemlib-lexical-baseline-exceptions.tsv"
    lexical_exception_rows = rows(lexical_exception_path)
    require(len(lexical_exception_rows) == 12 and
            all(len(row) == 2 for row in lexical_exception_rows),
            "invalid lexical exception manifest")
    lexical_exceptions = {row[0] for row in lexical_exception_rows}
    require(len(lexical_exceptions) == 12, "duplicate lexical exception")

    alpheios_lines = alpheios_path.read_text().splitlines()
    revision_prefix = "# alpheios_revision\t"
    revision_rows = [line[len(revision_prefix):] for line in alpheios_lines
                     if line.startswith(revision_prefix)]
    require(revision_rows == ["4632415fe93c85e9fdca47a0c5a13f31385f0023"],
            "unexpected Alpheios revision")
    alpheios_rows, alpheios_counts = comparison_counts(alpheios_path)
    require(len(alpheios_rows) == 146 and alpheios_counts == Counter({
        "different": 141, "unavailable-reference": 3, "identical": 2,
    }), "unexpected Alpheios comparison summary")

    hash_file = build_root / "stemlib-production-receipts.sha256"
    recorded_hashes = {}
    for row in hash_file.read_text().splitlines():
        fields = row.split()
        require(len(fields) == 2 and len(fields[0]) == 64 and
                all(character in "0123456789abcdef" for character in fields[0]),
                "invalid production target hash receipt")
        key = Path(fields[1]).name + ":" + Path(fields[1]).parent.name
        require(key not in recorded_hashes, "duplicate production target receipt hash")
        recorded_hashes[key] = fields[0]
    require(set(recorded_hashes) == {
        "MORPHEUS-STEMLIB-PRODUCTION-RECEIPT.json:greek",
        "MORPHEUS-STEMLIB-PRODUCTION-RECEIPT.json:latin",
    }, "unexpected production target receipt hash")

    languages = {}
    common_revision = None
    common_profile = None
    common_model = None
    lexical_expected = {
        "Greek": Counter({"different": 6, "unavailable": 1, "identical": 1}),
        "Latin": Counter({"different": 6, "unavailable": 1, "identical": 1}),
    }
    for language in ["Greek", "Latin"]:
        first = lexical_root / f"{language}-first-corpus"
        second = lexical_root / f"{language}-second-corpus"
        target = production_root / language.lower()
        receipt_name = "MORPHEUS-STEMLIB-PRODUCTION-RECEIPT.json"
        receipts = [root / receipt_name for root in [first, second, target]]
        require(receipts[0].read_bytes() == receipts[1].read_bytes(),
                language + " independent production receipts differ")
        require(receipts[0].read_bytes() == receipts[2].read_bytes(),
                language + " target receipt differs from CTest qualification")
        receipt = json.loads(receipts[0].read_text())
        require(receipt.get("schema") == 2 and receipt.get("language") == language,
                language + " production receipt is invalid")
        require(len(receipt["outputs"]["table"]) == int(expected_summary[language][0]),
                language + " table output count changed")
        require(len(receipt["outputs"]["lexical"]) == 8,
                language + " lexical output count changed")

        comparison_name = "MORPHEUS-STEMLIB-LEXICAL-COMPARISON.tsv"
        comparisons = [root / comparison_name for root in [first, second, target]]
        require(comparisons[0].read_bytes() == comparisons[1].read_bytes() ==
                comparisons[2].read_bytes(),
                language + " lexical comparisons differ")
        lexical_rows, lexical_counts = comparison_counts(comparisons[0])
        require(len(lexical_rows) == 8 and lexical_counts == lexical_expected[language],
                language + " lexical comparison summary changed")
        require({row[0] for row in lexical_rows if row[3] == "different"} ==
                {path for path in lexical_exceptions if path.startswith(language + "/")},
                language + " lexical differences do not match their exception manifest")

        target_hash = digest(receipts[2])
        recorded_key = receipt_name + ":" + language.lower()
        require(recorded_hashes.get(recorded_key) == target_hash,
                language + " recorded target receipt hash changed")
        revision = receipt["source_revision"]
        profile = receipt["qualification_profile"]
        model = receipt["execution"]["model"]
        if common_revision is None:
            common_revision, common_profile, common_model = revision, profile, model
        require((revision, profile, model) ==
                (common_revision, common_profile, common_model),
                "language provenance identities differ")
        languages[language] = {
            "binary_baseline_differences": int(expected_summary[language][1]),
            "lexical_comparison": dict(sorted(lexical_counts.items())),
            "lexical_outputs": 8,
            "production_receipt_sha256": target_hash,
            "table_outputs": int(expected_summary[language][0]),
            "text_or_index_baseline_differences": 0,
        }

    report = {
        "schema": 1,
        "status": "qualified",
        "source_revision": common_revision,
        "qualification_profile": common_profile,
        "execution_model": common_model,
        "checks": {
            "independent_ctest_builds_identical": True,
            "production_target_matches_ctest": True,
        },
        "languages": languages,
        "runtime_ctest": runtime_ctest,
        "references": {
            "alpheios": {
                "revision": revision_rows[0],
                "comparison": dict(sorted(alpheios_counts.items())),
                "paths": len(alpheios_rows),
                "report_sha256": digest(alpheios_path),
            },
            "perseids_checked_in": {
                "binary_differences": len(difference_rows) - 1,
                "difference_report_sha256": digest(difference_path),
                "binary_exception_manifest_sha256": digest(binary_exception_path),
                "lexical_exception_manifest_sha256": digest(lexical_exception_path),
                "summary_sha256": digest(summary_path),
                "text_or_index_differences": 0,
            },
        },
    }
    require(common_revision == current_revision(source),
            "qualification evidence does not match the current source revision")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=lambda value: Path(value).resolve(), required=True)
    parser.add_argument("--build", type=lambda value: Path(value).resolve(), required=True)
    parser.add_argument("--ctest-junit", type=lambda value: Path(value).resolve(),
                        required=True)
    parser.add_argument("--output", type=lambda value: Path(value).resolve(), required=True)
    arguments = parser.parse_args()
    try:
        build(arguments.source, arguments.build, arguments.ctest_junit,
              arguments.output)
    except (IndexError, KeyError, OSError, ValueError, ET.ParseError,
            json.JSONDecodeError,
            subprocess.CalledProcessError) as error:
        parser.exit(1, f"stemlib qualification: {error}\n")
