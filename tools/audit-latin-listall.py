#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare literal LISTALL forms against two Latin stemlibs (aggregate output).

The optional per-form JSONL is private lexical research data and must be
written outside the repository. No normalization or lemma inference is done.
"""

import argparse
from collections import Counter
import ctypes
import hashlib
import json
import os
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
ABI_VERSION = 2
LATIN = 1


class NativeAnalyzer:
    def __init__(self, library, stemlib):
        api = ctypes.CDLL(str(library.resolve()))
        api.morpheus_open_path.argtypes = [ctypes.c_uint32, ctypes.c_char_p,
                                           ctypes.c_size_t, ctypes.c_uint32,
                                           ctypes.POINTER(ctypes.c_void_p)]
        api.morpheus_open_path.restype = ctypes.c_int
        api.morpheus_analyze.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                         ctypes.c_size_t, ctypes.c_uint64,
                                         ctypes.POINTER(ctypes.c_void_p)]
        api.morpheus_analyze.restype = ctypes.c_int
        api.morpheus_result_count.argtypes = [ctypes.c_void_p]
        api.morpheus_result_count.restype = ctypes.c_size_t
        api.morpheus_result_free.argtypes = [ctypes.c_void_p]
        api.morpheus_close.argtypes = [ctypes.c_void_p]
        path = os.fsencode(stemlib.resolve())
        self.context = ctypes.c_void_p()
        status = api.morpheus_open_path(ABI_VERSION, path, len(path), LATIN,
                                         ctypes.byref(self.context))
        if status:
            raise ValueError(f"cannot open Latin stemlib (status {status})")
        self.api = api

    def analyze(self, word):
        result = ctypes.c_void_p()
        status = self.api.morpheus_analyze(self.context, word, len(word), 0,
                                            ctypes.byref(result))
        try:
            if status == 0 and not result:
                raise RuntimeError("successful native analysis returned no result")
            return status, self.api.morpheus_result_count(result) if status == 0 else 0
        finally:
            if result:
                self.api.morpheus_result_free(result)

    def close(self):
        self.api.morpheus_close(self.context)


def audit(forms, curated, rebuilt, private_output=None):
    if private_output is not None:
        target = private_output.resolve()
        if target == REPO or REPO in target.parents or target == forms.resolve():
            raise ValueError("private per-form output must be outside the repository and input")
    seen = set()
    counts = Counter()
    statuses = Counter()
    digest = hashlib.sha256()
    output = None
    try:
        if private_output is not None:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            output = os.fdopen(os.open(private_output.resolve(), flags, 0o600), "w")
        with forms.open("rb") as source:
            for raw in source:
                digest.update(raw)
                counts["input_lines"] += 1
                word = raw.rstrip(b"\r\n")
                if not word:
                    counts["blank_lines"] += 1
                    continue
                if any(byte < 33 or byte > 126 for byte in word):
                    raise ValueError(f"non-ASCII or whitespace in input line {counts['input_lines']}")
                if word in seen:
                    counts["duplicate_lines"] += 1
                    continue
                seen.add(word)
                counts["distinct_forms"] += 1
                left_status, left_count = curated.analyze(word)
                right_status, right_count = rebuilt.analyze(word)
                statuses[(left_status, right_status)] += 1
                if left_status or right_status:
                    cell = "error"
                else:
                    cell = ("recognized" if left_count else "absent") + "_curated__" + (
                        "recognized" if right_count else "absent") + "_rebuilt"
                counts[cell] += 1
                if output is not None and (cell != "recognized_curated__recognized_rebuilt" or
                                           left_count != right_count):
                    output.write(json.dumps({"form": word.decode("ascii"),
                                             "curated_status": left_status,
                                             "curated_count": left_count,
                                             "rebuilt_status": right_status,
                                             "rebuilt_count": right_count}) + "\n")
    finally:
        if output is not None:
            output.close()
    return {"schema": 1, "mode": "literal ASCII forms; native options 0",
            "input_sha256": digest.hexdigest(),
            "counts": dict(sorted(counts.items())),
            "status_pairs": {f"{a},{b}": count for (a, b), count in sorted(statuses.items())}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forms", required=True, type=Path, help="extracted plain ASCII wordlist")
    parser.add_argument("--library", required=True, type=Path, help="native shared library")
    parser.add_argument("--curated", required=True, type=Path, help="curated stemlib root")
    parser.add_argument("--rebuilt", required=True, type=Path, help="private reconstructed root")
    parser.add_argument("--private-output", type=Path, help="owner-only per-form differences")
    args = parser.parse_args()
    curated = NativeAnalyzer(args.library, args.curated)
    try:
        rebuilt = NativeAnalyzer(args.library, args.rebuilt)
        try:
            print(json.dumps(audit(args.forms, curated, rebuilt, args.private_output), sort_keys=True))
        finally:
            rebuilt.close()
    finally:
        curated.close()


if __name__ == "__main__":
    main()
