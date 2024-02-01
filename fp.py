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
    # TODO: Implement deletion of local branches

    # Flow example
    create_migration_branch("v1.1.1")
    checkout_subrepo_migration_branch("v1.1.1")
    extract_feature()
    push_subrepo("Extracted contact points")
    upgrade_container_to("v1.1.1")
    checkout_subrepo_migration_branch("v1.1.1")
    applyFeature()
    clear_contact_points()

    # Fix any issues by hand
    # Merge subrepo back into master & checkout master (Implementation still TODO)
    # Continue development on the new v1.1.1 container branch until next upgrade.
    pass


if __name__ == '__main__':
    main()
