# TODO: This is very ad-hoc, may want to use a framework instead
###################
#
# Diffing
#
###################

from featurePatch.android.applyFeature import generate_merged_content, compute_line_diff, print_some_diffs, transform_diffs

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


def print_all_diffs(diffs):
    title_map = {0: "\nEquality", -1: "\nDeletion", 1: "\nInsertion"}
    for d in diffs:
        print(f"{title_map[d[0]]}:")
        print(d[1])


def test_patch():
    print("Up - C")
    print("_____________________")
    up_c = compute_line_diff(update, contact_point)
    print_all_diffs(up_c)
    print("Un - Up")
    print("_____________________")
    un_up = compute_line_diff(unmodified, update)
    print_all_diffs(un_up)
    #print("Up - Un")
    up_un = compute_line_diff(update, unmodified)
    #print_all_diffs(up_un)


    diffs = transform_diffs(un_up, up_c)
    print("Transformed")
    print("_____________________")
    print_all_diffs(diffs)
    pass