import pytest
import os
from featurePatch.util import _inject_config, _inject_constants
from featurePatch.android.applyFeature import (_line_diff, _group_marker_content, _ungroup_marker_content,
                                               _transform_diffs, _compute_line_diff, _create_diff)

def mock_constants_and_config(add_const=dict(), add_conf=dict()):
    constants = dict()
    constants.update(add_const)
    configs = dict()
    configs.update(add_conf)
    _inject_config(configs)
    _inject_constants(constants)


def csf_v752():
    # mock constants
    mock_constants_and_config(add_const={"per_file_diff_deadline":"None"},
                              add_conf={"marker":"TI_GLUE: eNT9XAHgq0lZdbQs2nfH"})

    csf_v752_path = "C:\\Users\\Chrissy\\Code\\feature-patch\\tests\\data\\diff"
    with open(os.path.join(csf_v752_path, "CSF_v752_predecessor.txt"), 'r') as f:
        predecessor = f.read()
    with open(os.path.join(csf_v752_path, "CSF_v752_upstream.txt"), 'r') as f:
        upstream = f.read()
    with open(os.path.join(csf_v752_path, "CSF_v752_untouched_predecessor.txt"), 'r') as f:
        untouched_pre = f.read()
    with open(os.path.join(csf_v752_path, "CSF_v752_expected.txt"), "r") as f:
        expected = f.read()

    text = _create_diff(upstream, predecessor, untouched_pre)
    with open(os.path.join(csf_v752_path, "last_run.txt"), "w") as f:
        f.write(text)
    assert(expected == _create_diff(upstream, predecessor, untouched_pre))

csf_v752()