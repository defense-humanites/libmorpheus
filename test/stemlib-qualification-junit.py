# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exercise the stemlib qualification report's CTest JUnit gate."""

import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET


source = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()
shutil.rmtree(work, ignore_errors=True)
work.mkdir(parents=True)

assembler_path = source / "tools/assemble-stemlib-qualification.py"
spec = importlib.util.spec_from_file_location("stemlib_qualification", assembler_path)
assert spec is not None and spec.loader is not None
assembler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assembler)


def write_suite(path, names, **attributes):
    values = {
        "tests": str(len(names)),
        "failures": "0",
        "disabled": "0",
        "skipped": "0",
    }
    values.update(attributes)
    suite = ET.Element("testsuite", values)
    for name in names:
        ET.SubElement(suite, "testcase", {"name": name, "status": "run"})
    ET.ElementTree(suite).write(path, encoding="utf-8", xml_declaration=True)
    return suite


def rejects(path, message):
    try:
        assembler.ctest_result(path)
    except ValueError as error:
        assert str(error) == message
    else:
        raise AssertionError("invalid CTest JUnit result was accepted")


required = sorted(assembler.REQUIRED_RUNTIME_TESTS)
valid_path = work / "valid.xml"
write_suite(valid_path, required + ["additional_test"])
assert assembler.ctest_result(valid_path) == {
    "all_passed": True,
    "required_tests": required,
    "tests": len(required) + 1,
}

missing_path = work / "missing.xml"
write_suite(missing_path, required[:-1])
rejects(missing_path, "required runtime qualification tests are missing")

duplicate_path = work / "duplicate.xml"
write_suite(duplicate_path, required + [required[0]])
rejects(duplicate_path, "invalid or duplicate CTest case")

failed_path = work / "failed.xml"
write_suite(failed_path, required, failures="1")
rejects(failed_path, "CTest qualification did not pass")

error_path = work / "error.xml"
write_suite(error_path, required, errors="1")
rejects(error_path, "CTest qualification did not pass")

failure_case_path = work / "failure-case.xml"
failure_suite = write_suite(failure_case_path, required)
ET.SubElement(failure_suite.find("testcase"), "failure")
ET.ElementTree(failure_suite).write(
    failure_case_path, encoding="utf-8", xml_declaration=True)
rejects(failure_case_path, "CTest qualification did not pass")

skipped_path = work / "skipped.xml"
skipped_suite = write_suite(skipped_path, required)
skipped_suite.set("skipped", "1")
skipped_suite.find("testcase").set("status", "notrun")
ET.SubElement(skipped_suite.find("testcase"), "skipped")
ET.ElementTree(skipped_suite).write(
    skipped_path, encoding="utf-8", xml_declaration=True)
rejects(skipped_path, "CTest qualification did not pass")

wrong_root_path = work / "wrong-root.xml"
ET.ElementTree(ET.Element("testsuites")).write(
    wrong_root_path, encoding="utf-8", xml_declaration=True)
rejects(wrong_root_path, "invalid CTest JUnit root")

malformed_path = work / "malformed.xml"
malformed_path.write_text("<testsuite")
try:
    assembler.ctest_result(malformed_path)
except ET.ParseError:
    pass
else:
    raise AssertionError("malformed CTest JUnit XML was accepted")

stale_output = work / "stale.json"
stale_output.write_text("stale\n")
result = subprocess.run([
    sys.executable, assembler_path,
    "--source", source,
    "--build", work,
    "--ctest-junit", malformed_path,
    "--output", stale_output,
], capture_output=True, text=True)
assert result.returncode == 1
assert result.stderr.startswith("stemlib qualification:")
assert not stale_output.exists()
