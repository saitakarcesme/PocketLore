#!/usr/bin/env python3
"""Validate evaluation structure without printing private case content."""
import argparse
import collections
import json
import pathlib

CAPABILITIES = {'explanation', 'comparison', 'synthesis', 'reasoning', 'unknown', 'travel'}
FIELDS = {'id', 'domain', 'capability', 'question', 'required_behaviors', 'failure_modes', 'evidence_requirements'}


def validate(document):
    assert document['schema_version'] == 1, 'Unsupported schema'
    assert document['status'] == 'frozen', 'Expected frozen suite'
    assert document['source_type'] == 'local_model_authored_unverified_rubric', 'Missing provenance limitation'
    assert document['split'] in {'development', 'holdout'}, 'Invalid split'
    cases = document['cases']
    assert cases, 'Empty evaluation suite'
    ids, questions = set(), set()
    for case in cases:
        assert set(case) == FIELDS, 'Unexpected case fields'
        assert case['id'] not in ids, 'Duplicate identifier'
        assert case['question'].strip().casefold() not in questions, 'Duplicate question'
        ids.add(case['id'])
        questions.add(case['question'].strip().casefold())
        assert case['capability'] in CAPABILITIES, 'Invalid capability'
        for field in ('id', 'domain', 'question'):
            assert isinstance(case[field], str) and case[field].strip(), 'Missing text'
        for field, length in [('required_behaviors', 3), ('failure_modes', 2), ('evidence_requirements', 2)]:
            assert isinstance(case[field], list) and len(case[field]) == length, 'Invalid rubric length'
            assert all(isinstance(text, str) and text.strip() for text in case[field]), 'Invalid rubric text'
        # A conservative structural guard, not an English-language proof.
        assert all(ord(char) < 128 for char in json.dumps(case, ensure_ascii=False)), 'Non-ASCII text requires language review'
    return {'case_count': len(cases), 'capabilities': dict(collections.Counter(case['capability'] for case in cases)), 'unique_ids': True, 'unique_questions': True, 'ascii_language_guard': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite', type=pathlib.Path)
    args = parser.parse_args()
    print(json.dumps(validate(json.loads(args.suite.read_text())), indent=2))


if __name__ == '__main__':
    main()
