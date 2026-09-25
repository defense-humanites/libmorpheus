#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage a versioned, deliberately conservative TEI header projection.

This is an investigation tool, not a stemlib production input. The historical
/local/text/{lsj,ls}/lemmata exports have not survived in the source tree.
"""

import argparse
import hashlib
import json
import re
import subprocess
import unicodedata
from pathlib import Path

try:
    from lxml import etree
except ImportError as exc:
    raise SystemExit("This investigation tool requires lxml (pip install lxml)") from exc


LEXICA_REVISION = "56061ca127f4a2844980baffc5f2b6d1332897b3"
SOURCE_DIRS = {
    "Greek": ("grc/lsj", "grc.lsj.perseus-eng*.xml"),
    # eng2 edits the Latin dictionary's Greek quotations into Unicode. The
    # archival eng1 retains Beta Code and is the edition selected here.
    "Latin": ("lat/ls", "lat.ls.perseus-eng1.xml"),
}
BASELINES = {
    "Greek": ("lsj.nom", "lsj.vbs"),
    "Latin": ("ls.nom", "vbs.latin"),
}
FIELDS = frozenset(("orth", "itype", "gen", "pos", "quant"))
KEY_PATTERN = {
    "Greek": re.compile(r"[A-Za-z*()\\/=+|'^_\-]+(?:#[1-9])?\Z"),
    "Latin": re.compile(r"[A-Za-z^_+\-]+(?:#[1-9])?\Z"),
}


def numbered_path(path):
    match = re.search(r"(\d+)\.xml$", path.name)
    return int(match.group(1)) if match else -1


def normalize(value, language):
    value = " ".join(value.split())
    if language == "Greek":
        return value if value.isascii() else None
    result = []
    for char in value:
        # The archival Latin TEI uses CYRILLIC SMALL LETTER SHORT U in place
        # of short y. Curated ls.nom witnesses include Abdalony^mus, A^by^la
        # and Alcy^o^ne_ for those same TEI entry keys. Do not generalize
        # other non-Latin characters without a similarly reviewable witness.
        if char == "ў":
            result.append("y^")
            continue
        if char in "æÆœŒ":
            result.append({"æ": "ae", "Æ": "Ae", "œ": "oe", "Œ": "Oe"}[char])
            continue
        decomposed = unicodedata.normalize("NFD", char)
        base = decomposed[0]
        marks = decomposed[1:]
        if not marks:
            result.append(base)
        elif base.isascii() and base.isalpha() and set(marks) <= {"\u0304", "\u0306", "\u0308"}:
            result.append(base + "".join({"\u0304": "_", "\u0306": "^", "\u0308": "+"}[m] for m in marks))
        else:
            return None
    result = "".join(result)
    return result if result.isascii() else None


def project(entry, language):
    key = entry.get("key")
    fields = []
    reason = None
    if not key:
        reason = "missing-key"
    # TEI disambiguation suffixes are not themselves historical lemma IDs.
    # Keep the source key in the IR and mark the lexical guess explicitly.
    lemma = re.sub(r"(?<=[A-Za-z)])([1-9])$", r"#\1", key or "")
    if not reason and not KEY_PATTERN[language].fullmatch(lemma):
        reason = "unsupported-key"
    for child in entry:
        if child.tag == "sense":
            break
        if child.tag not in FIELDS:
            continue
        raw = " ".join("".join(child.itertext()).split())
        value = normalize(raw, language)
        if not reason and any(isinstance(node, etree._Entity) for node in child.iter()):
            reason = "unresolved-entity"
        if not reason and value is None:
            reason = "unsupported-character"
        if raw:
            fields.append({"name": child.tag, "type": child.get("type"), "value": raw,
                           "projection": value})
    if not any(field["name"] == "orth" for field in fields):
        reason = reason or "missing-orth"
    record = {"schema": 1, "source_key": key, "lemma": lemma if not reason else None,
              "fields": fields, "projection_error": reason}
    if reason:
        return record, None
    # The first tab separates the headword from the legacy pseudo-TEI fields.
    # This projection is a comparison artifact, not a claim of byte identity.
    fragments = []
    for field in fields:
        name = field["name"]
        # The historical filters only recognize this precise alt spelling.
        tag = "<orth type=alt>" if name == "orth" and field["type"] == "alt" else f"<{name}>"
        value = field["projection"].replace("&", "&amp;").replace("<", "&lt;")
        fragments.append(f"{tag}{value}</{name}>")
    return record, lemma + " \t" + "\t".join(fragments)


def baseline_lemmas(repo, language):
    found = set()
    for filename in BASELINES[language]:
        with (repo / "stemlib" / language / "stemsrc" / filename).open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if line.startswith(":le:"):
                    found.add(line[4:].strip())
    return found


def latin_baseline_header_orths(path):
    """Read only headwords immediately preceding a curated :le: record.

    This is deliberately narrower than parsing all of ls.nom: earlier raw
    dictionary lines are not necessarily associated with the next stem.
    """
    found = {}
    preceding = None
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.rstrip("\r\n")
            if line.startswith(":le:"):
                if preceding is not None:
                    found.setdefault(line[4:].strip(), set()).add(preceding)
                preceding = None
            elif line.startswith(":"):
                preceding = None
            elif line.strip():
                preceding = line.split("\t", 1)[0].strip()
    return found


def latin_header_comparison(repo, candidates):
    baseline = latin_baseline_header_orths(repo / "stemlib/Latin/stemsrc/ls.nom")
    common = sorted(baseline.keys() & candidates.keys())
    exact = {key for key in common if baseline[key] & candidates[key]}

    def spelling(value):
        return re.sub(r"#[1-9]$", "", value).casefold().replace("^", "").replace("_", "").replace("+", "")

    normalized = {key for key in common if {spelling(v) for v in baseline[key]} &
                  {spelling(v) for v in candidates[key]}}
    return {"baseline_lemmas_with_adjacent_header": len(baseline),
            "projected_lemmas_with_adjacent_header": len(common),
            "exact_first_orth": len(exact),
            "same_spelling_ignoring_case_homograph_and_quantity": len(normalized),
            "unmatched_examples": [
                {"lemma": key, "baseline": sorted(baseline[key])[:2],
                 "projected": sorted(candidates[key])[:2]}
                for key in common if key not in normalized
            ][:20]}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(lexica, repo, output, languages=("Greek", "Latin")):
    revision = subprocess.check_output(["git", "-C", str(lexica), "rev-parse", "HEAD"], text=True).strip()
    if revision != LEXICA_REVISION:
        raise ValueError(f"lexica revision {revision} differs from pinned {LEXICA_REVISION}")
    dirty = subprocess.check_output(["git", "-C", str(lexica), "status", "--porcelain", "--",
                                     "CTS_XML_TEI/perseus/pdllex/grc/lsj",
                                     "CTS_XML_TEI/perseus/pdllex/lat/ls"], text=True)
    if dirty:
        raise ValueError("selected TEI source files differ from the pinned revision")
    if output.exists():
        raise ValueError(f"stage already exists: {output}")
    sources = {}
    for language in languages:
        subdir, pattern = SOURCE_DIRS[language]
        files = sorted((lexica / "CTS_XML_TEI/perseus/pdllex" / subdir).glob(pattern), key=numbered_path)
        if not files or (language == "Latin" and len(files) != 1) or (language == "Greek" and len(files) != 27):
            raise ValueError(f"incomplete {language} TEI edition: {len(files)} files")
        sources[language] = files
    output.mkdir(parents=True)
    for language, files in sources.items():
        projected = set()
        header_orths = {}
        reasons = {}
        count = 0
        with (output / f"{language}.headers.jsonl").open("w", encoding="utf-8") as ir, \
             (output / f"{language}.lemmata").open("w", encoding="utf-8") as legacy, \
             (output / f"{language}.skipped.tsv").open("w", encoding="utf-8") as skipped:
            skipped.write("source\tid\tkey\treason\n")
            for source in files:
                # Do not load external DTDs or resolve entities from TEI.
                parser = etree.iterparse(str(source), events=("end",), tag="entryFree",
                                         load_dtd=False, no_network=True,
                                         resolve_entities=False, recover=False, huge_tree=True)
                for _, entry in parser:
                    count += 1
                    record, line = project(entry, language)
                    record.update({"source": source.name, "id": entry.get("id")})
                    ir.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                    if line is None:
                        reason = record["projection_error"]
                        reasons[reason] = reasons.get(reason, 0) + 1
                        skipped.write(f"{source.name}\t{entry.get('id', '')}\t{entry.get('key', '')}\t{reason}\n")
                    else:
                        legacy.write(line + "\n")
                        projected.add(record["lemma"])
                        if language == "Latin":
                            first = next((field["projection"] for field in record["fields"]
                                          if field["name"] == "orth"), None)
                            if first:
                                header_orths.setdefault(record["lemma"], set()).add(first)
                    entry.clear()
                    while entry.getprevious() is not None:
                        del entry.getparent()[0]
                del parser
        baseline = baseline_lemmas(repo, language)
        report = {
            "schema": 2,
            "status": "investigation-only; not a production or redistribution input",
            "source_repository": "PerseusDL/lexica", "source_revision": revision,
            "source_files": [{"path": f.relative_to(lexica).as_posix(), "sha256": sha256(f)} for f in files],
            "entries": count, "projected_rows": count - sum(reasons.values()),
            "skipped_by_reason": dict(sorted(reasons.items())),
            "projected_unique_lemmas": len(projected),
            "baseline_unique_lemmas": len(baseline),
            "exact_lemma_overlap": len(projected & baseline),
            "projected_only_examples": sorted(projected - baseline)[:20],
            "baseline_only_examples": sorted(baseline - projected)[:20],
            "output_sha256": {name: sha256(output / f"{language}.{name}") for name in ("headers.jsonl", "lemmata", "skipped.tsv")},
        }
        if language == "Latin":
            report["curated_header_comparison"] = latin_header_comparison(repo, header_orths)
        (output / f"{language}.report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{language}: {count} entries, {report['projected_rows']} projected, "
              f"{len(projected & baseline)}/{len(baseline)} baseline lemmas overlap")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lexica", type=Path, required=True, help="local PerseusDL/lexica checkout at the pinned revision")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True, help="fresh, private staging directory outside the source checkout")
    parser.add_argument("--language", choices=("Greek", "Latin", "both"), default="both",
                        help="project a single edition without downloading the other")
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.repo.resolve()) or args.output.resolve().is_relative_to(args.lexica.resolve()):
        parser.error("output must be outside both source checkouts")
    try:
        languages = ("Greek", "Latin") if args.language == "both" else (args.language,)
        run(args.lexica, args.repo, args.output, languages)
    except (ValueError, OSError, etree.XMLSyntaxError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
