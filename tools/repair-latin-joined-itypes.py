#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Extend the three attachment repairs to headers whose itype fields are joined.

The historical pipeline runs ``combitype`` before ``latvb``: two ``<itype>``
fields separated by white space become one string joined by ``, ``, so a
header written ``<itype>e_mi, emptum</itype> <itype>3</itype>`` reaches the
lexer as ``e_mi, emptum, 3`` and goes through the same attachment rule as a
single field. The partition writes consecutive itype fields tab-separated,
so every header whose itype fields are consecutive is joined that way. The
written-part anchor, sigmatic suffix and residual attachment repairs prove
their shapes from a single source field only and therefore leave those
blocks alone (*dirimo*, ``di^ri^me_m``, is one of them).

This tool emulates the join: for each header whose itype fields are
consecutive and equal to the source projection, it builds the joined string
and hands the three repairs a one-field view of that header and of its
source article, and nothing else. Each repair then applies its own proof
and its own historical-output check unchanged; headers with a single itype
field are not touched here. The lexer tables are read with C comments
removed and character-literal trims accepted, which the residual repair's
own reader does not yet do; the difference withholds, never repairs.
Lexical values stay private.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from lxml import etree

HERE = Path(__file__).resolve().parent


def sibling(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


anchor = sibling('repair-latin-anchor-duplication')
sigmatic = sibling('repair-latin-sigmatic-suffix')
residual = sibling('repair-latin-residual-attachments')
first = anchor.first
LEXER = anchor.LEXER
COMBITYPE = anchor.LEXER.with_name('combitype.l')
JOIN = ', '


lexer_tables = residual.lexer_tables


def join_rule(combitype=COMBITYPE):
    """The combitype rule joining adjacent itype fields; the tool refuses a lexer that joins otherwise."""
    text = combitype.read_text(errors='replace')
    match = re.search(r'"</itype>"\[ \\t\]\+"<itype>"\s+printf\("([^"]*)"\);', text)
    if not match or match.group(1) != JOIN:
        raise ValueError('combitype join rule differs from the emulated one')
    return match.group(1)


def joined_view(row, entry):
    """A one-field view of a header whose consecutive itype fields combitype joins, with a matching source view."""
    if row.get('projection_error') is not None or row.get('id') != entry.get('id'):
        return None
    base, _ = first.review.projection.project(entry, 'Latin')
    if base.get('projection_error') is not None:
        return None
    indexes = [i for i, f in enumerate(row['fields']) if f['name'] == 'itype']
    itypes = [row['fields'][i]['projection'] for i in indexes]
    source = [f['projection'] for f in base['fields'] + first.review.initial_sense_fields(entry) if f['name'] == 'itype']
    if len(itypes) < 2 or itypes != source or indexes != list(range(indexes[0], indexes[0] + len(indexes))):
        return None
    joined = JOIN.join(itypes)
    fields = [f for i, f in enumerate(row['fields']) if i not in indexes[1:]]
    fields[indexes[0]] = dict(row['fields'][indexes[0]], projection=joined, value=joined)
    view = dict(row, fields=fields)
    orth = re.sub(r'#\d+$', '', row['headword'])
    xml = etree.Element('entryFree', id=entry.get('id'), key=entry.get('key'))
    xml.text = ''
    element = etree.SubElement(xml, 'orth', extent='full'); element.text = orth; element.tail = ', '
    element = etree.SubElement(xml, 'itype'); element.text = joined
    etree.SubElement(xml, 'sense').text = 'x'
    check, _ = first.review.projection.project(xml, 'Latin')
    if check.get('projection_error') is not None or check['headword'] != row['headword'] or [
            f['projection'] for f in check['fields'] if f['name'] == 'itype'] != [joined]:
        return None
    return view, xml


def transform(candidate, rows, entries, tables=None):
    join_rule()
    tables = lexer_tables() if tables is None else tables
    literal = anchor.literal_table()
    views, sources = [], {}
    counts = Counter()
    for row in rows:
        if row.get('id') not in entries:
            raise ValueError('missing source article')
        result = joined_view(row, entries[row['id']])
        if result is None:
            continue
        view, xml = result
        views.append(view); sources[row['id']] = xml
        counts['joined_headers'] += 1
    data = candidate
    report = {}
    for name, module, extra in (('anchor_duplication', anchor, {'literal': literal}),
                                ('sigmatic_suffix', sigmatic, {'literal': literal}),
                                ('residual_attachments', residual, {'tables': tables})):
        data, stage_counts = module.transform(data, views, sources, **extra)
        report[name] = stage_counts
        counts['repaired_records'] += stage_counts.get('repaired_records', 0)
        counts['repaired_lemma_blocks'] += stage_counts.get('repaired_lemma_blocks', 0)
    return data, {**dict(sorted(counts.items())), 'stages': report}


def prepare(candidate, headers, lexica, output, expected=None):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = first.source_rows(headers, lexica)
    entries, second_source, second_revision = first.review.load_entries(lexica)
    if source != second_source or revision != second_revision:
        raise ValueError('source changed during validation')
    data, counts = transform(candidate.read_bytes(), rows, entries)
    if expected is not None and counts.get('repaired_records', 0) != expected:
        raise ValueError('unexpected repaired record count')
    report = {'schema': 1,
              'scope': 'headers whose consecutive itype fields combitype joins with ", "; the written-part anchor, sigmatic suffix and residual attachment repairs applied in that order to a one-field view of those headers only, each with its own proof and historical-output check; no other header read',
              'source_revision': revision, 'counts': counts,
              'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (candidate, headers, source, LEXER, COMBITYPE)},
              'output_sha256': hashlib.sha256(data).hexdigest()}
    first.write_private(target, data)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'headers', 'lexica', 'private-output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--expected', type=int)
    args = parser.parse_args()
    print(json.dumps(prepare(args.candidate, args.headers, args.lexica, args.private_output, args.expected), sort_keys=True))


if __name__ == '__main__':
    main()
