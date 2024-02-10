from featurePatch.android.extractFeature import extract_feature
from featurePatch.android.applyFeature import run as applyFeature
from featurePatch.android.applyFeature import _generate_merged_content, _compute_line_diff, _transform_diffs
from featurePatch.test import test_patch
from featurePatch.util import clear_contact_points, add_to_config_template
from featurePatch.git import *
from featurePatch.git import _checkout_subrepo
from featurePatch.log import *


def main():
    # Revert
    #clean_subrepo()
    #_checkout_subrepo("master")
    #delete_local_migration_branch("v1.1.1")


    # Flow example
    """
    create_subrepo_migration_branch("v1.1.1")
    checkout_subrepo_migration_branch("v1.1.1")
    extract_feature()
    push_subrepo("Extracted contact points")
    upgrade_container_to("v1.1.1")
    checkout_subrepo_migration_branch("v1.1.1")
    applyFeature()
    clear_contact_points()
    """

    #clear_contact_points()
    commit_subrepo("Contact points removed.")

    #### Fix any remaining merge issues by hand

    #push_subrepo("Upgrade to v1.1.1 functional.")
    #_checkout_subrepo("master")
    #merge_migration_branch("v1.1.1")

    # TODO: push container migration
    # Continue development on the new v1.1.1 container branch until next upgrade.
    pass


if __name__ == '__main__':
    main()
