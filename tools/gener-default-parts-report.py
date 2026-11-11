# SPDX-License-Identifier: AGPL-3.0-or-later
"""Measure what the default principal parts change in a generation index.

Compares two generation indices prepared from the same sources (typically
the historical one, prepared with ``--historical``, and the
default one) through the native library and the in-tree Python binding:

- for each index: lemmas, generated forms, skipped records, failed requests,
  and the latency of ``morpheus_generate()`` (first call in a fresh context,
  then p50, p99 and maximum over every lemma);
- lemma by lemma: lemmas added or removed, lemmas whose form count changes,
  lemmas that lose forms or gain skipped records;
- a round trip on a seeded sample of changed lemmas: the share of added and
  of existing forms that analyze back to their lemma with the same tense and
  mood;
- for a list of verbs, the first-person singular indicative surfaces each
  index adds or removes.

The report is JSON on standard output; a summary goes to standard error. The
whole run takes a few minutes per index. Only the Python standard library,
the built native library and the in-tree binding are used; the binding's
internals provide counts without decoding records.

Usage:

    python3 -I tools/gener-default-parts-report.py \\
        --library build/dev/libmorpheus.so \\
        --greek /path/to/stemlib/Greek \\
        --before build/dev/test-gener-corpus/historical.mgi \\
        --after build/dev/test-gener-corpus/first.mgi
"""

from __future__ import annotations

import argparse
import collections
import ctypes
import json
import os
import random
import re
import statistics
import struct
import sys
import tempfile
import time
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parent.parent
DEFAULT_VERBS = (
    "e)/xw", "pa/sxw", "pi/ptw", "o(ra/w", "me/nw", "i(/sthmi", "bou/lomai",
    "lu/w", "a)kou/w", "poie/w", "dhlo/w", "a)gge/llw", "a)gapa/w", "a)gnoe/w",
)


def index_keys(path: Path) -> list[str]:
    """Return the lemma keys of a version 1 generation index."""
    data = path.read_bytes()
    if data[:8] != b"MORPHGEN":
        raise SystemExit(f"{path}: not a generation index")
    lemmas, blocks, records, _ = struct.unpack_from("<4Q", data, 16)
    strings = 64 + lemmas * 24 + blocks * 16 + records * 24
    keys = []
    for index in range(lemmas):
        (offset,) = struct.unpack_from("<Q", data, 64 + index * 24)
        start = strings + offset
        keys.append(data[start:data.index(b"\0", start)].decode("latin-1"))
    return keys


def stemlib_root(directory: Path, greek: Path, index: Path) -> Path:
    directory.mkdir()
    (directory / "Greek").symlink_to(greek.resolve(), target_is_directory=True)
    (directory / "gener.index").symlink_to(index.resolve())
    return directory


def native_counts(libmorpheus, context, lemma: str, options) -> tuple[int, int, int]:
    """Count records and skipped records without decoding them."""
    from libmorpheus import _library

    encoded, buffer = _library.encoded_buffer(lemma, "Beta Code lemma")
    native_options = _library._generation_options(options)
    native = context._native
    result = ctypes.c_void_p()
    status = native.generate(
        context._require_open(), buffer, len(encoded),
        ctypes.byref(native_options), ctypes.byref(result),
    )
    try:
        if status != 0:
            return 0, 0, status
        return (
            native.generation_result_count(result),
            native.generation_result_skipped_records(result),
            0,
        )
    finally:
        native.generation_result_free(result)


def measure_index(libmorpheus, library, root: Path, keys: list[str]) -> tuple[dict, dict]:
    options = libmorpheus.GenerationOptions(result_limit=65536)
    context = library.context(str(root), libmorpheus.Language.GREEK)
    per_lemma = {}
    latencies = []
    failures = collections.Counter()
    try:
        for position, lemma in enumerate(keys):
            start = time.perf_counter()
            count, skipped, status = native_counts(libmorpheus, context, lemma, options)
            elapsed = (time.perf_counter() - start) * 1000
            if position == 0:
                first_call = elapsed
            else:
                latencies.append(elapsed)
            if status:
                failures[status] += 1
            per_lemma[lemma] = (count, skipped, status)
    finally:
        context.close()
    latencies.sort()
    summary = {
        "lemmas": len(keys),
        "forms": sum(value[0] for value in per_lemma.values()),
        "skippedRecords": sum(value[1] for value in per_lemma.values()),
        "lemmasWithSkippedRecords": sum(1 for value in per_lemma.values() if value[1]),
        "failedRequests": dict(failures),
        "latencyMs": {
            "firstCall": round(first_call, 3),
            "p50": round(statistics.median(latencies), 3),
            "p99": round(latencies[int(len(latencies) * 0.99)], 3),
            "max": round(latencies[-1], 3),
        },
    }
    return summary, per_lemma


def compare(before: dict, after: dict) -> tuple[dict, list[str]]:
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(
        lemma for lemma in set(before) & set(after) if before[lemma][0] != after[lemma][0]
    )
    lost = sorted(lemma for lemma in changed if after[lemma][0] < before[lemma][0])
    more_skips = sorted(
        lemma for lemma in set(before) & set(after) if after[lemma][1] > before[lemma][1]
    )
    return {
        "lemmasAdded": added,
        "lemmasRemoved": removed,
        "lemmasChanged": len(changed),
        "lemmasLosingForms": lost,
        "lemmasGainingSkippedRecords": more_skips,
    }, changed


def signature(generation) -> tuple:
    return (
        generation.surface, generation.tense, generation.mood,
        tuple(generation.voices), generation.person, generation.grammatical_number,
        tuple(generation.grammatical_cases), tuple(generation.genders),
        tuple(generation.dialects),
    )


def round_trip(libmorpheus, old, new, lemmas: list[str]) -> dict:
    options = libmorpheus.GenerationOptions(result_limit=65536)
    homonym = re.compile(r"\d+$")
    analyses = {}
    counts = collections.Counter()
    by_tense = collections.defaultdict(collections.Counter)
    for lemma in lemmas:
        earlier = collections.Counter(signature(form) for form in old.generate(lemma, options))
        for form in new.generate(lemma, options):
            key = signature(form)
            if earlier[key]:
                earlier[key] -= 1
                kind = "existing"
            else:
                kind = "added"
            if form.surface not in analyses:
                analyses[form.surface] = new.analyze(form.surface)
            recognized = any(
                homonym.sub("", analysis.lemma) == homonym.sub("", form.lemma)
                and analysis.tense == form.tense and analysis.mood == form.mood
                for analysis in analyses[form.surface]
            )
            counts[(kind, recognized)] += 1
            if kind == "added":
                by_tense[form.tense or "none"][recognized] += 1

    def share(kind: str) -> dict:
        total = counts[(kind, True)] + counts[(kind, False)]
        return {
            "forms": total,
            "recognized": counts[(kind, True)],
            "share": round(counts[(kind, True)] / total, 4) if total else None,
        }

    return {
        "lemmas": len(lemmas),
        "added": share("added"),
        "existing": share("existing"),
        "addedByTense": {
            tense: {"recognized": values[True], "forms": values[True] + values[False]}
            for tense, values in sorted(by_tense.items())
        },
    }


def verb_changes(libmorpheus, old, new, verbs: tuple[str, ...]) -> dict:
    options = libmorpheus.GenerationOptions(
        result_limit=65536,
        mood=libmorpheus.Mood.INDICATIVE,
        person=libmorpheus.Person.FIRST,
        number=libmorpheus.Number.SINGULAR,
    )
    changes = {}
    for verb in verbs:
        earlier = {form.surface for form in old.generate(verb, options)}
        later = {form.surface for form in new.generate(verb, options)}
        changes[verb] = {"added": sorted(later - earlier), "removed": sorted(earlier - later)}
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--greek", type=Path, required=True,
                        help="the Greek stemlib directory (rule files, indices, tables)")
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--sample", type=int, default=120)
    parser.add_argument("--seed", type=int, default=78)
    parser.add_argument("--verbs", default=",".join(DEFAULT_VERBS))
    arguments = parser.parse_args()

    sys.path.insert(0, str(REPOSITORY / "bindings" / "python" / "src"))
    import libmorpheus

    library = libmorpheus.Library(str(arguments.library))
    with tempfile.TemporaryDirectory() as temporary:
        roots = {
            name: stemlib_root(Path(temporary) / name, arguments.greek, index)
            for name, index in (("before", arguments.before), ("after", arguments.after))
        }
        totals = {}
        per_lemma = {}
        for name, index in (("before", arguments.before), ("after", arguments.after)):
            totals[name], per_lemma[name] = measure_index(
                libmorpheus, library, roots[name], index_keys(index)
            )
            print(f"{name}: {json.dumps(totals[name])}", file=sys.stderr)
        comparison, changed = compare(per_lemma["before"], per_lemma["after"])
        sample = random.Random(arguments.seed).sample(changed, min(arguments.sample, len(changed)))
        old = library.context(str(roots["before"]), libmorpheus.Language.GREEK)
        new = library.context(str(roots["after"]), libmorpheus.Language.GREEK)
        try:
            trip = round_trip(libmorpheus, old, new, sorted(sample))
            verbs = verb_changes(libmorpheus, old, new, tuple(
                verb for verb in arguments.verbs.split(",") if verb
            ))
        finally:
            old.close()
            new.close()
    library.close()
    report = {
        "indices": {
            "before": {"path": os.fspath(arguments.before), **totals["before"]},
            "after": {"path": os.fspath(arguments.after), **totals["after"]},
        },
        "comparison": comparison,
        "roundTrip": {"seed": arguments.seed, **trip},
        "verbs": verbs,
    }
    print(
        f"changed lemmas {comparison['lemmasChanged']}, losing forms "
        f"{len(comparison['lemmasLosingForms'])}, gaining skipped records "
        f"{len(comparison['lemmasGainingSkippedRecords'])}; round trip: added "
        f"{trip['added']['share']}, existing {trip['existing']['share']}",
        file=sys.stderr,
    )
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
