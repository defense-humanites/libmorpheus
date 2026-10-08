#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Counterfactual extraction/native probe; never approve a lexical replacement."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import importlib.util

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('missing_review', REPO / 'tools/review-latin-missing-definitions.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
loss = review.loss


def select_cases(path):
    cases = []
    seen = set()
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row['lemma'] in seen:
            raise ValueError('duplicate terminal-conjugation review lemma')
        seen.add(row['lemma'])
        if row['review_decision'] != 'historical_extraction_review' or len(row['articles']) != 1:
            continue
        article = row['articles'][0]
        if article['grammar_profile']['itype_shape'] == 'principal_parts_with_conjugation_digit':
            if (article['partition'] != 'verbal' or article['headword_identity'] != 'same_literal_lemma' or
                    article['replay_state'] != 'emits_no_definitions' or
                    article['grammar_profile']['first_orth_extent'] != 'full'):
                raise ValueError('terminal-conjugation dossier has unexpected scope')
            cases.append(row)
    return sorted(cases, key=lambda row: row['lemma'])


def simplified(row):
    fields = [field for field in row['fields'] if field['name'] == 'itype']
    if len(fields) != 1:
        raise ValueError('terminal-conjugation probe needs one itype')
    match = re.search(r',\s*([1-4])$', fields[0]['projection'] or '')
    if not match:
        raise ValueError('terminal-conjugation probe needs an explicit final digit')
    digit = match[1]
    # A labelled counterfactual, not a source projection. Other fields unchanged.
    result = dict(row, fields=[dict(f, projection=digit) if f is fields[0] else dict(f)
                              for f in row['fields']])
    return result, int(digit)


def trace_profile(traces, original_type, head):
    return [{'filter': trace['filter'],
             'original_itype_survives': ('<itype>' + original_type + '</itype>') in trace['stdout'],
             'itype_fields': len(re.findall(r'<itype>[^<>]*</itype>', trace['stdout'])),
             'headword_prefix_preserved': trace['stdout'].startswith(head + ' ')} for trace in traces]


def candidate_payload(candidate, cases):
    if candidate and not candidate.endswith(b'\n'):
        raise ValueError('counterfactual cannot alter candidate termination')
    # Do not modify even an empty existing block: new blocks must be unambiguous.
    lemmas = {line[4:].strip() for line in candidate.splitlines() if line.startswith(b':le:')}
    output = [candidate]
    for case in cases:
        lemma = case['lemma'].encode('ascii')
        records = case['counterfactual_definitions']
        if not records:
            continue
        if set(records) != {lemma} or lemma in lemmas:
            raise ValueError('counterfactual emits another lemma or duplicates a candidate block')
        lemmas.add(lemma)
        output.append(b':le:' + lemma + b'\n')
        for line, count in sorted(records[lemma].items()):
            output.extend([line + b'\n'] * count)
    return b''.join(output)


def target_forms(path, lemmas):
    forms, total = {}, 0
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row['kind'] != 'lost_form':
            continue
        selected = Counter()
        for reading in row['readings']:
            values = reading['signature']
            if values[1] in lemmas:
                if len(values) != len(loss.SIGNATURE):
                    raise ValueError('invalid target signature')
                selected[tuple(v.encode() if isinstance(v, str) else v for v in values)] += 1
        if selected:
            form = row['form'].encode('ascii')
            if form in forms:
                raise ValueError('duplicate target form')
            forms[form] = selected
            total += sum(selected.values())
    return forms, total


def source_headword_probe(case, before, after):
    head = re.sub(r'#[1-9]$', '', case['header']['headword']).translate(str.maketrans('', '', '_^-'))
    if not re.fullmatch('[A-Za-z]+', head) or not head.endswith(('o', 'or')):
        raise ValueError('source headword is not a full first-person present')
    lemma = case['lemma'].encode('ascii')
    voice = 2 if head.endswith('or') else 1
    def expected(row):
        return (not row.preverb and row.lemma == lemma and
                (row.part_of_speech, row.person, row.number, row.tense, row.mood, row.voice) == (2, 1, 1, 1, 4, voice))
    old, new = before.analyses(head.encode(), require_untruncated=True), after.analyses(head.encode(), require_untruncated=True)
    old_counter, new_counter = Counter(map(loss.signature, old)), Counter(map(loss.signature, new))
    return {'form': head, 'before_expected': sum(map(expected, old)), 'after_expected': sum(map(expected, new)),
            'retained_rows': sum((old_counter & new_counter).values()),
            'removed_rows': sum((old_counter - new_counter).values()),
            'added_rows': sum((new_counter - old_counter).values())}


def source_present_family(case):
    # Expectations come from the full source headword and conjugation digit,
    # independently of expanded stems and native analysis results. Quantities
    # are omitted only in the submitted spelling, as in the headword control.
    head = re.sub(r'#[1-9]$', '', case['header']['headword']).translate(str.maketrans('', '', '_^-'))
    digit = case['digit']
    if not re.fullmatch('[a-z]+', head) or digit not in (1, 3, 4) or not head.endswith(('o', 'or')):
        raise ValueError('unsupported source family headword or conjugation')
    passive = head.endswith('or')
    base = head[:-2] if passive else head[:-1]
    io = digit == 4 or (digit == 3 and base.endswith('i'))
    if io:
        if not base.endswith('i'):
            raise ValueError('fourth conjugation source lacks full io/ior headword')
        base = base[:-1]
    if not base:
        raise ValueError('source family has no literal base')
    if passive:
        if digit == 1:
            indicative, subjunctive, infinitive = ('or aris atur amur amini antur', 'er eris etur emur emini entur', 'ari')
        elif digit == 4:
            indicative, subjunctive, infinitive = ('ior iris itur imur imini iuntur', 'iar iaris iatur iamur iamini iantur', 'iri')
        elif io:
            indicative, subjunctive, infinitive = ('ior eris itur imur imini iuntur', 'iar iaris iatur iamur iamini iantur', 'i')
        else:
            indicative, subjunctive, infinitive = ('or eris itur imur imini untur', 'ar aris atur amur amini antur', 'i')
    elif digit == 1:
        indicative, subjunctive, infinitive = ('o as at amus atis ant', 'em es et emus etis ent', 'are')
    elif io:
        indicative, subjunctive, infinitive = ('io is it imus itis iunt', 'iam ias iat iamus iatis iant', 'ire' if digit == 4 else 'ere')
    else:
        indicative, subjunctive, infinitive = ('o is it imus itis unt', 'am as at amus atis ant', 'ere')
    cells = []
    for mood, suffixes in ((4, indicative.split()), (8, subjunctive.split())):
        for i, suffix in enumerate(suffixes):
            cells.append(dict(form=base + suffix, person=i % 3 + 1, number=1 if i < 3 else 3,
                              mood=mood, voice=2 if passive else 1))
    cells.append(dict(form=base + infinitive, person=0, number=0, mood=5, voice=2 if passive else 1))
    if len({c['form'] for c in cells}) != 13:
        raise ValueError('source family does not contain thirteen distinct cells')
    return cells


def probe_present_families(cases, before, after, output):
    counts = Counter()
    for case in cases:
        lemma = case['lemma'].encode('ascii')
        counts['families'] += 1
        for cell in source_present_family(case):
            def expected(row):
                return (not row.preverb and row.lemma == lemma and
                    (row.part_of_speech, row.person, row.number, row.tense, row.mood, row.voice) ==
                    (2, cell['person'], cell['number'], 1, cell['mood'], cell['voice']))
            left = before.analyses(cell['form'].encode(), require_untruncated=True)
            right = after.analyses(cell['form'].encode(), require_untruncated=True)
            old, new = Counter(map(loss.signature, left)), Counter(map(loss.signature, right))
            old_matches, new_matches = sum(map(expected, left)), sum(map(expected, right))
            if not new_matches or old - new:
                raise ValueError('source present-family expectation missing or previous reading removed')
            counts['cells'] += 1
            counts['before_covered'] += bool(old_matches)
            counts['after_covered'] += bool(new_matches)
            counts['expected_readings'] += new_matches
            counts['retained_rows'] += sum((old & new).values())
            counts['removed_rows'] += sum((old - new).values())
            counts['added_rows'] += sum((new - old).values())
            output.write(json.dumps({'kind': 'source_present_family', 'lemma': case['lemma'], **cell,
                'before_matches': old_matches, 'after_matches': new_matches,
                'retained_rows': sum((old & new).values()), 'added_rows': sum((new - old).values())}, sort_keys=True) + '\n')
    return {'counts': dict(sorted(counts.items())),
        'scope': 'six indicative, six subjunctive and one infinitive present; source headword/digit expectations; direct literal lemma and source morphology'}


def probe_losses(forms, baseline, before, after, output):
    totals, tense_groups = Counter(), Counter()
    for form, expected in sorted(forms.items()):
        witness = baseline.analyses(form, require_untruncated=True)
        actual = Counter(loss.signature(row) for row in witness if row.lemma in {s[1] for s in expected})
        if actual != expected:
            raise ValueError('terminal-conjugation witness differs from qualified lost signatures')
        old, new = before.analyses(form, require_untruncated=True), after.analyses(form, require_untruncated=True)
        if old:
            raise ValueError('terminal-conjugation target is no longer a complete final loss')
        final = Counter(map(loss.signature, new))
        recovered, missing = expected & final, expected - final
        totals['forms'] += 1
        totals['recognized_counterfactual_forms'] += bool(new)
        totals['expected_lost_readings'] += sum(expected.values())
        totals['recovered_exact_readings'] += sum(recovered.values())
        totals['still_missing_exact_readings'] += sum(missing.values())
        totals['other_counterfactual_readings'] += sum((final - expected).values())
        for signature, amount in expected.items():
            tense_groups[(signature[7], 'recovered')] += recovered[signature]
            tense_groups[(signature[7], 'missing')] += missing[signature]
        output.write(json.dumps({'kind': 'target_form', 'form': form.decode(),
            'expected': [{'signature': [loss.decoded(v) for v in sig], 'multiplicity': n} for sig, n in sorted(expected.items())],
            'counterfactual': [{'signature': [loss.decoded(v) for v in sig], 'multiplicity': n} for sig, n in sorted(final.items())]}, sort_keys=True) + '\n')
    return {'counts': dict(sorted(totals.items())),
            'readings_by_tense_outcome': loss.grouped(tense_groups, ('tense', 'outcome'))}


PRESENT_CLASSES = {b'conj1', b'conj2', b'conj3', b'conj3_io', b'conj4'}
PERFECT_CLASSES = {b'perfstem', b'avperf', b'evperf', b'ivperf'}


def definition_type(line):
    if line.startswith(b':de:'):
        return 'derivation'
    if line.startswith(b':vb:'):
        return 'literal_verbal_word'
    if line.startswith(b':wd:'):
        return 'literal_word'
    fields = set(line[4:].split()[1:])
    kinds = []
    if fields & PERFECT_CLASSES: kinds.append('perfect')
    if b'pp4' in fields: kinds.append('supine')
    if fields & PRESENT_CLASSES: kinds.append('present')
    if len(kinds) > 1:
        raise ValueError('expanded directive has conflicting stem classes')
    return kinds[0] if kinds else 'other'


def expanded_directive_profiles(expanded, lemmas):
    # Only fixed grammar names can leave the private expansion. Stems and
    # arbitrary fields never enter this report, even for an unknown directive.
    allowed = PRESENT_CLASSES | PERFECT_CLASSES | {b'pp4', b'are_vb', b'ire_vb', b'reg_conj'}
    groups = Counter()
    for lemma in lemmas:
        for line, n in expanded.get(lemma.encode(), {}).items():
            if not line.startswith(loss.STEM_PREFIXES):
                continue
            classes = tuple(sorted(f.decode() for f in set(line[4:].split()[1:]) & allowed))
            groups[(line[:4].decode(), definition_type(line), classes)] += n
    return [dict(directive=prefix, definition_type=kind, declared_classes=classes, rows=n)
            for (prefix, kind, classes), n in sorted(groups.items())]


def compare_counterfactuals(forms, full, present, output):
    counts, removed_tenses = Counter(), Counter()
    for form, expected in sorted(forms.items()):
        left = Counter(map(loss.signature, full.analyses(form, require_untruncated=True)))
        right = Counter(map(loss.signature, present.analyses(form, require_untruncated=True)))
        retained, removed, added = left & right, left - right, right - left
        old_recovered, new_recovered = expected & left, expected & right
        counts['forms'] += 1
        counts['changed_multisets'] += left != right
        counts['lost_recognition'] += bool(left) and not right
        counts['gained_recognition'] += bool(right) and not left
        counts['retained_rows'] += sum(retained.values())
        counts['removed_rows'] += sum(removed.values())
        counts['added_rows'] += sum(added.values())
        counts['target_recoveries_removed'] += sum((old_recovered - new_recovered).values())
        counts['target_recoveries_added'] += sum((new_recovered - old_recovered).values())
        for sig, n in removed.items():
            removed_tenses[(sig[7],)] += n
        def serial(counter):
            return [{'signature': [loss.decoded(v) for v in sig], 'multiplicity': n}
                    for sig, n in sorted(counter.items())]
        output.write(json.dumps({'kind': 'counterfactual_comparison', 'form': form.decode(),
            'retained_rows': sum(retained.values()), 'removed': serial(removed), 'added': serial(added),
            'target_recoveries_removed': serial(old_recovered - new_recovered),
            'target_recoveries_added': serial(new_recovered - old_recovered)}, sort_keys=True) + '\n')
    return {'counts': dict(sorted(counts.items())),
            'removed_readings_by_tense': loss.grouped(removed_tenses, ('tense',)),
            'same_exact_target_recoveries': not (counts['target_recoveries_removed'] or counts['target_recoveries_added']),
            'present_multisets_included_in_full': counts['added_rows'] == 0}


def present_cases(expanded, cases):
    result = []
    for case in cases:
        lemma = case['lemma'].encode('ascii')
        records = Counter()
        for line, n in expanded.get(lemma, {}).items():
            if line.startswith(loss.STEM_PREFIXES) and definition_type(line) == 'present':
                if not line.startswith(b':vs:') or n != 1:
                    raise ValueError('present isolation needs unique literal verbal stems')
                records[line] = n
        if sum(records.values()) != 1:
            raise ValueError('present isolation needs exactly one stem per source case')
        result.append(dict(case, counterfactual_definitions={lemma: records}))
    return result


def expanded_profiles(expanded, lemmas):
    groups = Counter()
    for lemma in lemmas:
        for line, n in expanded.get(lemma.encode(), {}).items():
            if not line.startswith(loss.STEM_PREFIXES):
                continue
            groups[definition_type(line)] += n
    return dict(sorted(groups.items()))


def retained_inputs(root):
    records = {}
    replaced = 0
    latin = (root / 'Latin').resolve()
    for line in (latin / 'lexical/inputs.tsv').read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        language, role, name, _ = line.split('\t')
        if language != 'Latin' or role not in {'verb', 'irregular-verb-baseline'}:
            continue
        path = (latin / name).resolve()
        if latin not in path.parents or name in records:
            raise ValueError('invalid controlled verbal input path')
        if name == 'stemsrc/vbs.latin':
            replaced += 1
        else:
            records[name] = loss.digest(path)
    if replaced != 1 or len(records) != 3:
        raise ValueError('unexpected retained verbal assembly inputs')
    return records


def prepare(args):
    for path, expected in ((args.review_dossier, args.expected_review_sha256),
                           (args.loss_dossier, args.expected_loss_sha256),
                           (args.candidate_source, args.expected_candidate_sha256),
                           (args.candidate / 'Latin/lexical/present-trial.expanded', args.expected_expanded_sha256),
                           (args.baseline / 'Latin/lexical/verb.expanded', args.expected_baseline_expanded_sha256)):
        if loss.digest(path) != expected:
            raise ValueError('qualified terminal-conjugation input receipt differs')
    cases = select_cases(args.review_dossier)
    if len(cases) != args.expected_lemmas or sum(c['lost_readings'] for c in cases) != args.expected_rows:
        raise ValueError('terminal-conjugation scope differs')
    first = loss.sibling('repair-latin-first-conjugation')
    headers, source, revision = first.source_rows(args.headers, args.lexica)
    by_id = {row['id']: row for row in headers}
    recovery = loss.sibling('recover-latin-initial-sense')
    replay_cases, groups, trace_groups = [], Counter(), Counter()
    for case in cases:
        article = case['articles'][0]
        row = article['header']
        if by_id.get(row['id']) != row:
            raise ValueError('terminal-conjugation header differs from validated source')
        original, traces = review.historical_replay(recovery.render(row), args.filters)
        if original or traces != article['filter_traces']:
            raise ValueError('original historical replay differs from qualified review')
        modified, digit = simplified(row)
        records, simplified_traces = review.historical_replay(recovery.render(modified), args.filters)
        status = review.replay_state(case['lemma'], records)
        if records and set(records) != {case['lemma'].encode()}:
            raise ValueError('simplified header emits another literal lemma')
        groups[(digit, status)] += 1
        field = next(f['projection'] for f in row['fields'] if f['name'] == 'itype')
        profile = trace_profile(traces, field, row['headword'])
        trace_groups[json.dumps({'source_conjugation_digit': digit, 'stages': profile}, sort_keys=True)] += 1
        replay_cases.append({'lemma': case['lemma'], 'header': row, 'digit': digit,
            'counterfactual_definitions': records, 'original_trace_profile': profile,
            'counterfactual_traces': simplified_traces})
    inputs = [args.review_dossier, args.loss_dossier, args.headers, args.lexica, args.candidate_source,
              args.baseline, args.candidate, args.library, args.tools, args.filters, source]
    target = loss.private_target(args.output, inputs)
    if target.exists():
        raise FileExistsError('counterfactual stage already exists')
    target.mkdir(mode=0o700)
    native = loss.sibling('qualify-latin-present-stages')
    original_indexes = {name: loss.digest(args.candidate / 'Latin/steminds' / name)
                        for name in ('nomind', 'nomind.lindex', 'vbind', 'vbind.lindex')}
    if retained_inputs(args.baseline) != retained_inputs(args.candidate) or any(
            original_indexes[name] != loss.digest(args.baseline / 'Latin/steminds' / name)
            for name in ('nomind', 'nomind.lindex')):
        raise ValueError('baseline copy differs from final controlled retained inputs')
    candidate = target / 'counterfactual.stems'
    native.write_private(candidate, candidate_payload(args.candidate_source.read_bytes(), replay_cases))
    # Both roots have identical retained inputs/nominals. Copy the baseline
    # to avoid inheriting the final root's exclusive present-trial work files.
    hashes = native.build_trial(args.baseline, candidate, args.tools, target / 'native')
    if any(hashes[name] != loss.digest(args.candidate / 'Latin/steminds' / name) for name in ('nomind', 'nomind.lindex')):
        raise ValueError('counterfactual changes controlled nominal indexes')
    forms, rows = target_forms(args.loss_dossier, {c['lemma'] for c in cases})
    if rows != args.expected_rows:
        raise ValueError('terminal-conjugation native target inventory differs')
    baseline = native.NativeRows(args.library, args.baseline)
    try:
        before = native.NativeRows(args.library, args.candidate)
        try:
            after = native.NativeRows(args.library, target / 'native')
            try:
                output = target / 'native-probes.jsonl'
                with os.fdopen(os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                                      getattr(os, 'O_NOFOLLOW', 0), 0o600), 'w') as stream:
                    loss_probe = probe_losses(forms, baseline, before, after, stream)
                    headword_counts = Counter()
                    for case in replay_cases:
                        probe = source_headword_probe(case, before, after)
                        headword_counts['before_covered'] += bool(probe['before_expected'])
                        headword_counts['after_covered'] += bool(probe['after_expected'])
                        for key in ('retained_rows', 'removed_rows', 'added_rows'):
                            headword_counts[key] += probe[key]
                        serial = dict(case, kind='source_case', source_headword_probe=probe,
                            counterfactual_definitions={lemma.decode(): [{'line': line.decode(), 'multiplicity': n}
                                for line, n in sorted(lines.items())] for lemma, lines in case['counterfactual_definitions'].items()})
                        stream.write(json.dumps(serial, sort_keys=True) + '\n')
            finally:
                after.close()
        finally:
            before.close()
    finally:
        baseline.close()
    expanded = loss.definitions(target / 'native/Latin/lexical/present-trial.expanded')
    isolated_cases = present_cases(expanded, replay_cases)
    present_source = target / 'present-only.stems'
    native.write_private(present_source, candidate_payload(args.candidate_source.read_bytes(), isolated_cases))
    present_hashes = native.build_trial(args.baseline, present_source, args.tools, target / 'present-native')
    if any(present_hashes[name] != original_indexes[name] for name in ('nomind', 'nomind.lindex')):
        raise ValueError('present-only counterfactual changes nominal indexes')
    present_expanded = loss.definitions(target / 'present-native/Latin/lexical/present-trial.expanded')
    present_profile = expanded_profiles(present_expanded, [c['lemma'] for c in cases])
    if present_profile != {'present': len(cases)}:
        raise ValueError('present-only assembly retains extrapolated or unknown classes')
    present_output = target / 'present-only-probes.jsonl'
    baseline = native.NativeRows(args.library, args.baseline)
    try:
        before = native.NativeRows(args.library, args.candidate)
        try:
            after = native.NativeRows(args.library, target / 'present-native')
            try:
                with os.fdopen(os.open(present_output, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                                      getattr(os, 'O_NOFOLLOW', 0), 0o600), 'w') as stream:
                    present_losses = probe_losses(forms, baseline, before, after, stream)
                    present_families = probe_present_families(isolated_cases, before, after, stream)
                    full = native.NativeRows(args.library, target / 'native')
                    try:
                        direct_comparison = compare_counterfactuals(forms, full, after, stream)
                    finally:
                        full.close()
                    present_heads = Counter()
                    for case in isolated_cases:
                        probe = source_headword_probe(case, before, after)
                        present_heads['before_covered'] += bool(probe['before_expected'])
                        present_heads['after_covered'] += bool(probe['after_expected'])
                        for key in ('retained_rows', 'removed_rows', 'added_rows'):
                            present_heads[key] += probe[key]
                        stream.write(json.dumps({'kind': 'present_source_case', 'lemma': case['lemma'],
                            'source_headword_probe': probe}, sort_keys=True) + '\n')
            finally:
                after.close()
        finally:
            before.close()
    finally:
        baseline.close()
    if any(loss.digest(args.candidate / 'Latin/steminds' / name) != digest for name, digest in original_indexes.items()):
        raise ValueError('counterfactual mutated final candidate indexes')
    return {'schema': 1, 'scope': 'seven private diagnostic counterfactuals; terminal digit only; no repair approval or final-candidate mutation',
        'counts': {'lemmas': len(cases), 'lost_readings': rows},
        'replay_groups': [dict(source_conjugation_digit=digit, counterfactual_replay_state=state, lemmas=n)
                         for (digit, state), n in sorted(groups.items())],
        'original_trace_profiles': [dict(json.loads(profile), lemmas=n) for profile, n in sorted(trace_groups.items())],
        'source_headword_control': dict(sorted(headword_counts.items())), 'lost_reading_control': loss_probe,
        'counterfactual_expanded_definition_types': expanded_profiles(expanded, [c['lemma'] for c in cases]),
        'counterfactual_expanded_directive_profiles': expanded_directive_profiles(expanded, [c['lemma'] for c in cases]),
        'present_only_control': {'scope': 'isolated literal present stems; source-family coverage; not source approval or complete-paradigm qualification',
            'expanded_definition_types': present_profile, 'source_headword_control': dict(sorted(present_heads.items())),
            'full_to_present_comparison': direct_comparison,
            'source_present_family_control': present_families,
            'lost_reading_control': present_losses, 'source_sha256': loss.digest(present_source),
            'indexes_sha256': present_hashes, 'private_native_probe_sha256': loss.digest(present_output)},
        'source_revision': revision, 'input_sha256': {name: loss.digest(path) for name, path in [
            ('review_dossier', args.review_dossier), ('loss_dossier', args.loss_dossier), ('headers', args.headers),
            ('Latin_TEI', source), ('candidate_source', args.candidate_source),
            ('before_expanded', args.candidate / 'Latin/lexical/present-trial.expanded'),
            ('baseline_expanded', args.baseline / 'Latin/lexical/verb.expanded'), ('native_library', args.library)]},
        'counterfactual_source_sha256': loss.digest(candidate), 'counterfactual_indexes_sha256': hashes,
        'final_candidate_indexes_unchanged': True,
        'private_native_probe_sha256': loss.digest(output)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('review-dossier', 'loss-dossier', 'headers', 'lexica', 'candidate-source', 'baseline',
                 'candidate', 'library', 'tools', 'filters', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('review', 'loss', 'candidate'):
        parser.add_argument('--expected-' + name + '-sha256', required=True)
    parser.add_argument('--expected-expanded-sha256', required=True)
    parser.add_argument('--expected-baseline-expanded-sha256', required=True)
    parser.add_argument('--expected-lemmas', type=int, required=True)
    parser.add_argument('--expected-rows', type=int, required=True)
    args = parser.parse_args()
    previous = os.umask(0o077)
    try:
        report = prepare(args)
    finally:
        os.umask(previous)
    print(json.dumps({'latin_terminal_conjugation_probe': report}, sort_keys=True))


if __name__ == '__main__':
    main()
