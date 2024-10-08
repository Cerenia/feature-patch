# TODO: This is very ad-hoc, may want to use a framework instead
###################
#
# Diffing
#
###################

from featurePatch.android.applyFeature import _compute_line_diff, _transform_diffs
#from featurePatch.util import configuration

"""
def _print_first_diffs(title: str, d: list[tuple[int, str]], equality=True, deletion=True, marker_contains=True, marker=configuration()["marker"]):
    print(title)
    print("_____________________")
    print(len(d))
    if equality:
        print("Equality:")
        if any(x[0] == 0 for x in d):
            print(next(x[1] for x in d if x[0] == 0))
        else:
            print("No Equalities...")
    if deletion:
        print("Deletion:")
        if any(x[0] == -1 for x in d):
            print(next(x[1] for x in d if x[0] == -1))
        else:
            print("No Deletions...")
    if marker_contains:
        print("Contains Marker:")
        if any(marker in x[1] for x in d):
            print(next(str(x[0]) for x in d if marker in x[1]) + "\n", next(x[1] for x in d if marker in x[1]))
        else:
            print("No Markers in any diffs...")
"""

marker = "################"

update = "I\n" \
        "have\n" \
        "never\n" \
        "been\n" \
        "so\n" \
        "glad\n" \
        "to\n" \
        "know\n" \
        "you.\n"

unmodified = "I\n" \
                   "have\n" \
                   "never\n" \
                   "hated\n" \
                   "someone\n" \
                   "as\n" \
                   "much\n" \
                   "as\n" \
                   "you.\n"

contact_point = "I\n" \
                "have\n" \
                "never\n" \
                f"{marker} start\n"\
                "known\n" \
                "how\n" \
                "hard\n" \
                "it\n" \
                "is\n" \
                "for\n" \
                f"{marker} end\n"\
                "someone\n" \
                f"{marker} start\n"\
                f"to\n" \
                f"give\n" \
                "up\n" \
                f"{marker} end\n" \
                "as\n" \
                "much\n" \
                "as\n" \
                "you.\n"

result = "I\n" \
                "have\n" \
                "never\n" \
                f"{marker} start\n"\
                "known\n" \
                "how\n" \
                "hard\n" \
                "it\n" \
                "is\n" \
                "for\n" \
                f"{marker} end\n" \
                "been\n" \
                "so\n" \
                "glad\n" \
                f"{marker} start\n"\
                f"to\n" \
                f"give\n" \
                "up\n" \
                f"{marker} end\n" \
                "to\nknow\n"\
                "you.\n"


def _print_all_diffs(diffs, exclude=[]):
    """
    :param: diffs The diffs to visualize
    :param: exclude list of exclusions 0:Equalities, -1:Deletions, 1:Insertion
    """
    title_map = {0: "\nEquality", -1: "\nDeletion", 1: "\nInsertion"}
    for d in diffs:
        diff_type = d[0]
        if diff_type not in exclude:
            print(f"{title_map[diff_type]}:")
            print(d[1])


def _test_patch():
    print("Up - C")
    print("_____________________")
    up_c = _compute_line_diff(update, contact_point)
    _print_all_diffs(up_c)
    print("Un - Up")
    print("_____________________")
    un_up = _compute_line_diff(unmodified, update)
    _print_all_diffs(un_up)
    #print("Up - Un")
    up_un = _compute_line_diff(update, unmodified)
    #print_all_diffs(up_un)


    diffs = _transform_diffs(un_up, up_c)
    print("Transformed")
    print("_____________________")
    _print_all_diffs(diffs)