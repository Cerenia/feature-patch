import pytest
import os

from featurePatch.android.applyFeature import (_line_diff, _group_marker_content, _ungroup_marker_content,
                                               _transform_diffs, _compute_line_diff, _create_diff)

# Mock constants
_c = dict()



def csf_v752():
    # mock constants
    global _c
    _c["per_file_diff_deadline"] = "None"
    csf_v752_path = "C:\\Users\\Chrissy\\Code\\feature-patch\\tests\\data\\diff"
    with open(os.path.join(csf_v752_path, "CSF_v752_predecessor.txt"), 'r') as f:
        predecessor = f.read()
    with open(os.path.join(csf_v752_path, "CSF_v752_upstream.txt"), 'r') as f:
        upstream = f.read()
    with open(os.path.join(csf_v752_path, "CSF_v752_untouched_predecessor.txt"), 'r') as f:
        untouched_pre = f.read()
    with open(os.path.join(csf_v752_path, "CSF_v752_expected.txt"), "r") as f:
        expected = f.read()

    assert(expected == _create_diff(upstream, predecessor, untouched_pre))

csf_v752()