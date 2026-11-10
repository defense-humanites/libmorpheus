# SPDX-License-Identifier: AGPL-3.0-or-later
"""Python binding rows for bench/compare.mjs.

compare.mjs runs this script with the interpreter named by MORPHEUS_PYTHON,
passes a JSON configuration on standard input and reads a JSON object on
standard output. The script imports the binding from the source tree
(``package`` in the configuration), opens the same library and stemlib as
the Node.js rows, and measures the same workloads with the same assignment
of operations: analysis of the corpus words distributed round-robin over
the contexts, and warm generation with ``iterations`` generations per
context. Each context runs in its own thread, as a Python application would
use them; ctypes releases the GIL during each native call, and the binding's
normalization runs under it.

Memory comes from ``getrusage``: ``peakRssBytes`` is the peak resident set
of this Python process, ``rssGrowthBytes`` the growth of that peak during
the measurement. They describe the Python process alone, not the Node.js
process that runs the other rows.
"""

from __future__ import annotations

import json
import platform
import resource
import sys
import threading
import time


def peak_rss() -> int:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Linux reports kibibytes, macOS bytes.
    return peak if sys.platform == "darwin" else peak * 1024


def summarize(engine, workload, lemma, contexts, operations, seconds, startup, results, before):
    peak = peak_rss()
    duration_ms = seconds * 1000
    return {
        "engine": engine,
        "workload": workload,
        "lemma": lemma,
        "contexts": contexts,
        "operations": operations,
        "durationMs": duration_ms,
        "operationsPerSecond": operations * 1000 / duration_ms,
        "meanMicroseconds": duration_ms * 1000 / operations,
        "startupMs": startup * 1000,
        "results": results,
        "peakRssBytes": peak,
        "rssGrowthBytes": peak - before,
    }


def run_threads(contexts, work):
    """Run work(index, context) in one thread per context; return the sum."""
    counts = [0] * len(contexts)
    barrier = threading.Barrier(len(contexts) + 1)

    def target(index):
        barrier.wait()
        counts[index] = work(index, contexts[index])

    threads = [threading.Thread(target=target, args=(index,)) for index in range(len(contexts))]
    for thread in threads:
        thread.start()
    barrier.wait()
    start = time.perf_counter()
    for thread in threads:
        thread.join()
    return sum(counts), time.perf_counter() - start


def main() -> int:
    if sys.version_info < (3, 11):
        print(
            f"python-bench.py: Python {sys.version_info[0]}.{sys.version_info[1]} "
            "is too old; the binding requires 3.11 or later",
            file=sys.stderr,
        )
        return 2
    config = json.load(sys.stdin)
    sys.path.insert(0, config["package"])
    import libmorpheus

    library = libmorpheus.Library(config["library"])
    greek = libmorpheus.Language.GREEK
    strict = libmorpheus.Option.STRICT_CASE
    words = config["words"]
    iterations = config["iterations"]
    warmup = config["warmupIterations"]
    measurements = []

    def open_contexts(count):
        start = time.perf_counter()
        contexts = [library.context(config["stemlib"], greek) for _ in range(count)]
        return contexts, time.perf_counter() - start

    for count in config["contexts"]:
        before = peak_rss()
        contexts, startup = open_contexts(count)
        try:
            for _ in range(warmup):
                for index, word in enumerate(words):
                    contexts[index % count].analyze(word, strict)
            operations = iterations * len(words)

            def analyze(worker, context):
                results = 0
                for operation in range(worker, operations, count):
                    results += len(context.analyze(words[operation % len(words)], strict))
                return results

            results, seconds = run_threads(contexts, analyze)
            measurements.append(summarize(
                "python", "analysis", None, count, operations, seconds, startup, results, before,
            ))
        finally:
            for context in contexts:
                context.close()

    lemmas = config.get("generationLemmas") or []
    options = libmorpheus.GenerationOptions(result_limit=config["resultLimit"])
    for count in config["contexts"]:
        for lemma, label in lemmas:
            before = peak_rss()
            contexts, startup = open_contexts(count)
            try:
                for _ in range(1 + warmup):
                    for context in contexts:
                        context.generate(lemma, options)

                def generate(_worker, context):
                    results = 0
                    for _ in range(iterations):
                        results += len(context.generate(lemma, options))
                    return results

                results, seconds = run_threads(contexts, generate)
                measurements.append(summarize(
                    f"python-generation-{label}-warm", "generation", lemma, count,
                    iterations * count, seconds, startup, results, before,
                ))
            finally:
                for context in contexts:
                    context.close()

    library.close()
    json.dump({
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "binding": libmorpheus.__version__,
        },
        "measurements": measurements,
    }, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
