from featurePatch.android.extractFeature import extract_feature
from featurePatch.android.applyFeature import initiate_runtime_log
from featurePatch.util import init_cygwin, add_to_config_template
from featurePatch.git import *


def main():
    clean_subrepo()
    create_migration_branch("v1.1.1")
    # checkout branch
    embed_subpreo("v1.1.1")
    extract_feature()
    upgrade_container_to("v1.1.1")
    # TODO: Test then CONTINUE HERE


if __name__ == '__main__':
    main()
