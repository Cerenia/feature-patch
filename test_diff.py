#import pytest
import os
import diff_match_patch as dmp_module
from featurePatch.util import _inject_config, _inject_constants
from featurePatch.android.applyFeature import (_line_diff, _group_marker_content, _ungroup_marker_content,
                                               _transform_diffs, _compute_line_diff, _create_diff, _create_intermediate_diffs)
from tests.prototest import _print_all_diffs
from fuzzywuzzy import fuzz


def mock_constants_and_config(add_const=dict(), add_conf=dict()):
    constants = dict()
    constants.update(add_const)
    configs = dict()
    configs.update(add_conf)
    _inject_config(configs)
    _inject_constants(constants)
    return(configs, constants)


def _contents_equal(path1: str, path2: str):
    contents = []
    for p in (path1, path2):
        with open(p, 'r') as f:
            c = f.read()
        contents.append(c)
    return contents[0] == contents[1]


def test_diff():
    exclude = ['02']
    #exclude = []

    test_path = "./tests/data/diff"
    testcases = list(set(filename.split('-')[0] for filename in os.listdir(test_path)))
    testcases.sort()

    # mock constants
    (configs, constants) = mock_constants_and_config(add_const={"per_file_diff_deadline":"None", 'min_fuzz_score': '80'},
                              add_conf={"marker":"TI_GLUE: eNT9XAHgq0lZdbQs2nfH"})
    min_fuzz_score = float(constants['min_fuzz_score'])
    for t in testcases:
        if t not in exclude:
            files = [f for f in os.listdir(test_path) if t in f]
            upstream_p = os.path.join(test_path, next(filter(lambda fname: 'upstream' in fname, files)))
            predecessor_p = os.path.join(test_path, next(filter(lambda fname: 'modified' in fname, files)))
            untouched_pre_p = os.path.join(test_path, next(filter(lambda fname: 'unmodified' in fname, files)))
            expected_ps = [os.path.join(test_path, filename) for filename in filter(lambda fname: 'expected' in fname, files)]
            initial_contents = []
            for p in (upstream_p, predecessor_p, untouched_pre_p):
                with open(p, 'r', encoding='utf-8') as f:
                    initial_contents.append(f.read())
            text = _create_diff(initial_contents[0], initial_contents[1], initial_contents[2])
            contents = []
            # We have multiple 'correct' solutions. For example, we may not care about a duplicated
            # xml tag at the very end of the file, since this is trivial to manually resolve
            for p in expected_ps:
                with open(p, 'r') as f:
                    contents.append(f.read())
            result = any((fuzz.partial_ratio(text.strip(), t.strip()) >= min_fuzz_score for t in contents))
            if not result:
                # analyse some intermediate results
                (ti_related_diff, unrelated_diffs) = _create_intermediate_diffs(initial_contents[0], initial_contents[1], initial_contents[2])
                diffs = _transform_diffs(unrelated_diffs, ti_related_diff)

                print("####\n### ti_related_diff: upstream -> modified_predecessor\n#####\n")
                _print_all_diffs(ti_related_diff)

                print("####\n### unrelated_diffs: unmodified_predecessor -> upstream\n#####\n")
                _print_all_diffs(unrelated_diffs)

                print("####\n### transformed diffs: should create the wanted result\n#####\n")
                _print_all_diffs(diffs)

                print("####\n### Final text: \n#####\n")
                print(dmp_module.diff_match_patch().diff_text2(diffs))
                assert(result) # Fail fast
            else:
                print(f"####\n### Testcase: {t} succeeded! \n#####\n")
            # Tell pytest if you succeeded or not
            #assert(result)


if __name__ == '__main__':
    test_diff()