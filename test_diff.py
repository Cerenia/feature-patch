#import pytest
import os
import diff_match_patch as dmp_module
from featurePatch.util import _inject_config, _inject_constants
from featurePatch.android.applyFeature import (_line_diff, _group_marker_content, _ungroup_marker_content,
                                               _transform_diffs, _compute_line_diff, _create_diff, _create_intermediate_diffs)
from tests.prototest import _print_all_diffs


def mock_constants_and_config(add_const=dict(), add_conf=dict()):
    constants = dict()
    constants.update(add_const)
    configs = dict()
    configs.update(add_conf)
    _inject_config(configs)
    _inject_constants(constants)


def _contents_equal(path1: str, path2: str):
    contents = []
    for p in (path1, path2):
        with open(p, 'r') as f:
            c = f.read()
        contents.append(c)
    return contents[0] == contents[1]


def test_diff():
    exclude = ["02"]

    test_path = "./tests/data/diff"
    testcases = ['01', '02']
    # mock constants
    mock_constants_and_config(add_const={"per_file_diff_deadline":"None"},
                              add_conf={"marker":"TI_GLUE: eNT9XAHgq0lZdbQs2nfH"})
    for t in testcases:
        if t not in exclude:
            files = [f for f in os.listdir(test_path) if t in f]
            upstream_p = os.path.join(test_path, next(filter(lambda fname: 'upstream' in fname, files)))
            predecessor_p = os.path.join(test_path, next(filter(lambda fname: 'modified' in fname, files)))
            untouched_pre_p = os.path.join(test_path, next(filter(lambda fname: 'unmodified' in fname, files)))
            expected_ps = [os.path.join(test_path, filename) for filename in filter(lambda fname: 'expected' in fname, files)]
            initial_contents = []
            for p in (upstream_p, predecessor_p, untouched_pre_p):
                with open(p, 'r') as f:
                    initial_contents.append(f.read())
            print(f"size text1: {len(initial_contents[2])}")
            print(f"size text2: {len(initial_contents[0])}")
            print(f"size text3: {len(initial_contents[1])}")
            text = _create_diff(initial_contents[0], initial_contents[1], initial_contents[2])
            contents = []
            # We have multiple 'correct' solutions. For example, we may not care about a duplicated
            # xml tag at the very end of the file, since this is trivial to manually resolve
            for p in expected_ps:
                with open(p, 'r') as f:
                    contents.append(f)
            result = any((text.strip() == t.strip() for t in contents))
            if not result:
                # print some intermediate results
                (ti_related_diff, unrelated_diffs) = _create_intermediate_diffs(initial_contents[0], initial_contents[1], initial_contents[2])
                diffs = _transform_diffs(unrelated_diffs, ti_related_diff)
                # TODO:
                # These should all be preserved!
                # => Then I should find contxt for the TI_Glue insertion
                # => Which diff does this correspond to? (careful it could be in the middle of an equality)
                # => May be able to solve that by creating a true line level diff, no blocks of equality but one line at a time.
                # Do I need three queues? insertion, deletion and addition? How to keep the linenrs straight?
                # => THEN, create the patching by adding the TI stuff into the original to be preserved diff.

                # Can I do this by comparing diffs between unmodified_pre and modified_pre, then searching for the index
                # of each context line of the original diffs
                print("####\n### ti_related_diff: upstream -> modified_predecessor\n#####\n")
                _print_all_diffs(ti_related_diff)

                print("####\n### unrelated_diffs: unmodified_predecessor -> upstream\n#####\n")
                _print_all_diffs(unrelated_diffs)

                print("####\n### transformed diffs: should create the wanted result\n#####\n")
                _print_all_diffs(diffs)

                print("####\n### Final text: \n#####\n")
                print(dmp_module.diff_match_patch().diff_text2(diffs))
            # Tell pytest if you succeeded or not
            assert(result)


if __name__ == '__main__':
    test_diff()