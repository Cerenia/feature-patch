import os
from ..util import contact_points_folder_path, configuration, constants, log


def target_code_folder():
    return os.path.join(contact_points_folder_path(), "code")


def target_drawable_folder():
    return os.path.join(contact_points_folder_path(), "drawable")


def target_string_folder():
    return os.path.join(contact_points_folder_path(), "strings")


def target_layout_folder():
    return os.path.join(contact_points_folder_path(), "layout")


def src_code_folder():
    return configuration()['android_src_root']


def src_layout_folder():
    return configuration()['android_layout_root']


def src_drawable_folder():
    return configuration()['android_drawable_root']


def src_string_folder():
    return configuration()['android_string_root']


def manifest_path(subrepo_path=False):
    """
        Returns the expected path for the manifest file.
    :param subrepo_path: Returns the path inside of the 'contact_points' folder instead of the path of the file in the container.
    :return: 
    """
    if subrepo_path:
        return os.path.join(contact_points_folder_path(), constants()['android_manifest_file'])
    src_path = configuration()["android_src_root"]
    if "main" not in src_path:
        log.critical(f"'main' not found in {src_path}. Invalid 'android_src_root' value in configuration!")
        exit(1)
    return os.path.join(src_path.split("main")[0], "main", constants()["android_manifest_file"])
