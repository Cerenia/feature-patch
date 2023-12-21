from featurePatch.android.extractFeature import extract_feature
from featurePatch.android.applyFeature import initiate_runtime_log
from featurePatch.util import init_cygwin
from featurePatch.git import *


def main():
    #extract_feature()
    #clean_subrepo()
    create_migration_branch()


if __name__ == '__main__':
    main()
