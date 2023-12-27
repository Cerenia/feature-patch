from featurePatch.android.extractFeature import extract_feature
from featurePatch.android.applyFeature import initiate_runtime_log
from featurePatch.util import init_cygwin
from featurePatch.git import *


def main():
    #clean_subrepo()
    #create_migration_branch("test")
    # checkout branch
    embed_subpreo(branch_name("test"))
    #extract_feature()


if __name__ == '__main__':
    main()
