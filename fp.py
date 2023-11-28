from featurePatch.android.extractFeature import initialize_extraction, extract_files
from featurePatch.android.applyFeature import initiate_runtime_log
from featurePatch.util import initialize_logger


def main():
    initialize_extraction()
    extract_files()
    #initiate_runtime_log()


if __name__ == '__main__':
    main()
