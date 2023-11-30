from featurePatch.android.extractFeature import initialize_extraction, extract_files
from featurePatch.android.applyFeature import initiate_runtime_log
from featurePatch.util import set_warning_logger, set_debug_logger, set_info_logger


def main():
    set_info_logger()
    initialize_extraction()
    extract_files()
    #initiate_runtime_log()


if __name__ == '__main__':
    main()
