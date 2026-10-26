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


def principal_parts_profile(case):
    fields = [f['projection'] for f in case['header']['fields'] if f['name'] == 'itype']
    if len(fields) != 1:
        raise ValueError('principal-part review needs the original single source field')
    match = re.fullmatch(r'(.*),\s*([1-4])', fields[0] or '')
    if not match or int(match[2]) != case['digit']:
        raise ValueError('principal-part review differs from the validated source digit')
    parts = [part.strip() for part in match[1].split(',')]
    shapes = []
    for part in parts:
        plain = part.translate(str.maketrans('', '', '_^'))
        syntax = ('single_notated_token' if re.fullmatch(r'[A-Za-z_^]+', part) else
                  'coordinated_or_alternative' if re.search(r'\b(?:and|or)\b', part) else
                  'empty' if not part else 'complex')
        ending = ('ending_re' if plain.endswith('re') else 'ending_ri' if plain.endswith('ri') else
                  'ending_um' if plain.endswith('um') else 'ending_us' if plain.endswith('us') else
                  'ending_i' if plain.endswith('i') else 'other_ending')
        shapes.append({'syntax': syntax, 'terminal_spelling': ending,
                       'quantity_notation': bool(set(part) & set('_^')),
                       'initial_dash': part.startswith('-')})
    head = re.sub(r'#[1-9]$', '', case['header']['headword']).translate(str.maketrans('', '', '_^-'))
    return {'source_conjugation_digit': case['digit'], 'declared_parts': len(parts),
            'headword_morphology': 'passive_headword' if head.endswith('or') else 'active_headword',
            'part_shapes': shapes}, parts


def principal_part_evidence(case, entry, projection):
    _, parts = principal_parts_profile(case)
    full_orths, quoted = set(), set()
    plain = lambda text: text.translate(str.maketrans('', '', '_^'))
    for orth in entry.findall('orth'):
        if orth.get('extent') != 'full' or orth.get('type') not in (None, 'alt'):
            continue
        value = projection.normalize(' '.join(''.join(orth.itertext()).split()), 'Latin')
        if value is not None:
            full_orths.add(plain(value))
    token = r'[A-Za-zÀ-ÖØ-öø-ÿĀ-ſ\u0300-\u036f_^]+(?:-[A-Za-zÀ-ÖØ-öø-ÿĀ-ſ\u0300-\u036f_^]+)*'
    for node in entry.iter():
        if node.tag not in ('quote', 'foreign') or (node.get('lang') or node.get('{http://www.w3.org/XML/1998/namespace}lang')) not in ('la', 'lat'):
            continue
        for word in re.findall(token, ''.join(node.itertext())):
            value = projection.normalize(word, 'Latin')
            if value is not None:
                quoted.add(plain(value))
    head = re.sub(r'#[1-9]$', '', case['header']['headword'])
    component = head.rsplit('-', 1)[-1]
    component = component[:-2] if component.endswith('or') else component[:-1] if component.endswith('o') else ''
    component = plain(component)
    evidence = []
    for part in parts:
        isolated = bool(re.fullmatch(r'[A-Za-z_^]+', part))
        value = plain(part)
        evidence.append({'isolated_source_token': isolated,
            'literal_present_component_prefix': bool(isolated and component and value.startswith(component)),
            'independent_full_orth_exact': bool(isolated and value in full_orths),
            'explicit_latin_quote_token_exact': bool(isolated and value in quoted)})
    return evidence


def review_principal_parts(cases, output, entries=None, projection=None):
    groups = Counter()
    for case in cases:
        profile, parts = principal_parts_profile(case)
        if entries is not None:
            evidence = principal_part_evidence(case, entries[case['header']['id']], projection)
            profile['source_evidence'] = evidence
        groups[json.dumps(profile, sort_keys=True)] += 1
        output.write(json.dumps({'kind': 'source_principal_parts', 'lemma': case['lemma'],
            'header': case['header'], 'literal_comma_separated_parts': parts,
            'profile': profile, 'decision': 'syntax_review_only_no_past_stem_reconstruction'}, sort_keys=True) + '\n')
    return {'scope': 'original source field syntax; endings do not establish complete principal parts or authorize suffix expansion',
            'groups': [dict(json.loads(profile), lemmas=n) for profile, n in sorted(groups.items())]}


ROUTE_FIELDS = ('preverb', 'raw_preverb', 'stem', 'suffix', 'ending')


def route_signature(row):
    return loss.signature(row) + tuple(getattr(row, name) for name in ROUTE_FIELDS)


def compare_family_routes(left, right, lemma, cell):
    old, new = Counter(map(route_signature, left)), Counter(map(route_signature, right))
    retained, removed, added = old & new, old - new, new - old
    expected = Counter({sig: n for sig, n in added.items() if
        not sig[11] and sig[1] == lemma and
        tuple(sig[i] for i in (2, 3, 4, 7, 8, 9)) ==
        (2, cell['person'], cell['number'], 1, cell['mood'], cell['voice'])})
    counts = Counter(retained_rows=sum(retained.values()), removed_rows=sum(removed.values()),
                     added_rows=sum(added.values()), added_expected_rows=sum(expected.values()),
                     added_other_rows=sum((added - expected).values()), added_direct_rows=0,
                     added_native_preverb_rows=0, removed_direct_rows=0, removed_native_preverb_rows=0)
    for name, records in (('added', added), ('removed', removed)):
        for sig, n in records.items():
            counts[name + ('_native_preverb_rows' if sig[11] else '_direct_rows')] += n
    groups = Counter()
    for sig, n in (added - expected).items():
        groups[('same_source_lemma' if sig[1] == lemma else 'other_lemma',
                'native_preverb' if sig[11] else 'direct', *sig[2:11])] += n
    def serial(records):
        return [{'signature': [loss.decoded(v) for v in sig[:11]], 'multiplicity': n,
                 'route_fields': {name: loss.decoded(value) for name, value in zip(ROUTE_FIELDS, sig[11:])}}
                for sig, n in sorted(records.items())]
    return counts, groups, {'retained_rows': sum(retained.values()), 'removed': serial(removed), 'added': serial(added)}


def reading_profiles(counter, analyses, source_lemmas, current_lemma=None):
    provenance = {}
    for row in analyses:
        provenance.setdefault(loss.signature(row), set()).add('native_preverb' if row.preverb else 'direct')
    groups = Counter()
    for sig, n in counter.items():
        if sig not in provenance:
            raise ValueError('reading profile lacks native provenance')
        relation = ('same_source_lemma' if sig[1] == current_lemma else
                    'source_lemma' if sig[1] in source_lemmas else 'outside_source_lemmas')
        route = next(iter(provenance[sig])) if len(provenance[sig]) == 1 else 'mixed'
        groups[(relation, route, *sig[2:])] += n
    return groups


def public_reading_profiles(groups):
    return loss.grouped(groups, ('lemma_relation', 'provenance', *loss.SIGNATURE[2:]))


def probe_present_families(cases, before, after, output):
    counts, other_groups = Counter(), Counter()
    route_counts, route_groups = Counter(), Counter()
    source_lemmas = {case['lemma'].encode('ascii') for case in cases}
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
            added = new - old
            expected_new = Counter(loss.signature(row) for row in right if expected(row))
            expected_added = added & expected_new
            other_added = added - expected_added
            counts['added_expected_rows'] += sum(expected_added.values())
            counts['added_other_rows'] += sum(other_added.values())
            other_groups.update(reading_profiles(other_added, right, source_lemmas, lemma))
            sensitive_counts, sensitive_groups, sensitive_private = compare_family_routes(left, right, lemma, cell)
            route_counts.update(sensitive_counts)
            route_groups.update(sensitive_groups)
            output.write(json.dumps({'kind': 'source_present_family', 'lemma': case['lemma'], **cell,
                'before_matches': old_matches, 'after_matches': new_matches,
                'retained_rows': sum((old & new).values()), 'added_rows': sum(added.values()),
                'other_added': [{'signature': [loss.decoded(v) for v in sig], 'multiplicity': n}
                                for sig, n in sorted(other_added.items())],
                'route_sensitive_comparison': sensitive_private}, sort_keys=True) + '\n')
    return {'counts': dict(sorted(counts.items())),
        'route_sensitive_comparison': {'route_fields': list(ROUTE_FIELDS), 'counts': dict(sorted(route_counts.items())),
            'other_added_reading_profiles': public_reading_profiles(route_groups)},
        'other_added_reading_profiles': public_reading_profiles(other_groups),
        'scope': 'six indicative, six subjunctive and one infinitive present; source headword/digit expectations; direct literal lemma and source morphology'}


def probe_losses(forms, baseline, before, after, output):
    totals, tense_groups, other_groups = Counter(), Counter(), Counter()
    source_lemmas = {sig[1] for expected in forms.values() for sig in expected}
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
        other_groups.update(reading_profiles(final - expected, new, source_lemmas))
        for signature, amount in expected.items():
            tense_groups[(signature[7], 'recovered')] += recovered[signature]
            tense_groups[(signature[7], 'missing')] += missing[signature]
        output.write(json.dumps({'kind': 'target_form', 'form': form.decode(),
            'expected': [{'signature': [loss.decoded(v) for v in sig], 'multiplicity': n} for sig, n in sorted(expected.items())],
            'counterfactual': [{'signature': [loss.decoded(v) for v in sig], 'multiplicity': n} for sig, n in sorted(final.items())]}, sort_keys=True) + '\n')
    return {'counts': dict(sorted(totals.items())),
            'other_counterfactual_reading_profiles': public_reading_profiles(other_groups),
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
    parts_output = target / 'source-parts-review.jsonl'
    entries, _, _ = first.review.load_entries(args.lexica)
    with os.fdopen(os.open(parts_output, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                          getattr(os, 'O_NOFOLLOW', 0), 0o600), 'w') as stream:
        parts_review = review_principal_parts(replay_cases, stream, entries, first.review.projection)
    del entries
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
        'source_principal_parts_review': dict(parts_review, private_review_sha256=loss.digest(parts_output)),
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
