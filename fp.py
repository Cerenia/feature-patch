from featurePatch.android.extractFeature import extract_feature
from featurePatch.android.applyFeature import initiate_runtime_log
from featurePatch.util import init_cygwin, add_to_config_template
from featurePatch.git import *
from featurePatch.log import *


def main():
    #clean_subrepo()
    #create_migration_branch("v1.1.1")
    #upgrade_container_to("v1.1.1")
    # TODO: Doesn't work yet, do I need to remove the subrepository before doing a fresh clone?
    checkout_subprepo("v1.1.1")
    #extract_feature(True)
    #push_subrepo("Extracted contact points")

    # TODO: Test then CONTINUE HERE


if __name__ == '__main__':
    main()
