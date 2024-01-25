from featurePatch.android.extractFeature import extract_feature
from featurePatch.android.applyFeature import initiate_runtime_log
from featurePatch.android.applyFeature import run as applyFeature
from featurePatch.android.applyFeature import generate_patch_content, generate_diffs, print_some_diffs
from featurePatch.util import clear_contact_points
from featurePatch.git import *
from featurePatch.log import *

marker = "________________________----------------------------______________"

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


def print_all_diffs(diffs):
    title_map = {0: "Equality", -1: "Deletion", 1: "Insertion"}
    for d in diffs:
        print(f"{title_map[d[0]]}:")
        print(d[1])


def test_patch():
    print_all_diffs(generate_diffs(update, contact_point))

    pass


def main():
    #clean_subrepo()
    #create_migration_branch("v1.1.1")
    #checkout_subprepo("migration_v1.1.1")
    #extract_feature(True)
    #push_subrepo("Extracted contact points")
    #upgrade_container_to("v1.1.1")
    #checkout_subprepo("migration_v1.1.1")

    #applyFeature()
    #clear_contact_points()

    test_patch()

    # Attempt to apply
    # Clean up by hand
    # Merge subrepo back into master & checkout master
    # Continue development
    pass


if __name__ == '__main__':
    main()
