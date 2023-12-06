from featurePatch.android.extractFeature import extract_files
from featurePatch.android.applyFeature import initiate_runtime_log
from featurePatch.util import set_warning_logger, set_debug_logger, set_info_logger, init_cygwin


def main():
    init_cygwin()
    set_info_logger()
    #extract_files()
    #initiate_runtime_log()




if __name__ == '__main__':
    main()
