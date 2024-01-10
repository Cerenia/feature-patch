from featurePatch.android.extractFeature import extract_feature
from featurePatch.android.applyFeature import initiate_runtime_log
from featurePatch.util import init_cygwin, add_to_config_template
from featurePatch.git import *
from featurePatch.log import *


def main():
    clean_subrepo()
    create_migration_branch("v1.1.1")
    checkout_subprepo("migration_v1.1.1")
    extract_feature(True)
    # Something went wrong here...
    push_subrepo("Extracted contact points")
    #upgrade_container_to("v1.1.1")
    #checkout_subprepo("migration_v1.1.1")
    # Attempt to apply
    # Clean up by hand
    # Merge subrepo back into master & checkout master
    # Continue development


if __name__ == '__main__':
    main()
