from featurePatch.android.extractFeature import extract_feature
from featurePatch.android.applyFeature import initiate_runtime_log
from featurePatch.android.applyFeature import run as applyFeature
from featurePatch.android.applyFeature import generate_merged_content, compute_line_diff, print_some_diffs, transform_diffs
from featurePatch.test import test_patch
from featurePatch.util import clear_contact_points
from featurePatch.git import *
from featurePatch.log import *









def main():
    #clean_subrepo()
    #create_migration_branch("v1.1.1")
    #checkout_subprepo("migration_v1.1.1")
    #extract_feature(True)
    #push_subrepo("Extracted contact points")
    #upgrade_container_to("v1.1.1")
    #checkout_subprepo("migration_v1.1.1")

    applyFeature()
    clear_contact_points()

    # Attempt to apply
    # Clean up by hand
    # Merge subrepo back into master & checkout master
    # Continue development
    pass


if __name__ == '__main__':
    main()
