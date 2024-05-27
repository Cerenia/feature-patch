import os
from ..util import contact_points_folder_path, configuration, constants, log


def target_code_folder():
    return os.path.join(contact_points_folder_path(), "code")


def target_drawable_folder():
    return os.path.join(contact_points_folder_path(), "drawable")


def target_string_folder():
    return os.path.join(contact_points_folder_path(), "values")


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

def find_separator(filepath):
    if "\\" in filepath:
        sep = "\\"
    elif "/" in filepath:
        sep = "/"
    else:
        log.critical(f"Could not find expected separators in filepath:\n{filepath}\nAre you passing a path?")
    return sep


def map_contact_points_path_to_container(filepath: str):
    """
    For a file in the 'contact_points' folder, create the resulting filepath in the container.
    :param filepath: The path to the file in the contact points folder
    :return: the equivalent filepath in the container repository
    """
    if 'contactPoints' not in filepath:
        log.critical(f'Path:\n {filepath}\n Was not a contact points path...')
    sep = find_separator(filepath)
    path_parts = filepath.split(sep)
    filename = path_parts[-1]
    filename_idx = len(path_parts) -1
    if len(path_parts) > 1:
        # find parent dir
        idx = 0
        while path_parts[idx] != 'contactPoints':
            idx = idx + 1
        parent_dir_idx = idx + 1
        parent_dir = path_parts[parent_dir_idx]
        intermediate_dirs = [p for (idx, p) in enumerate(path_parts) if idx > parent_dir_idx and idx < filename_idx]
        if parent_dir == "code":
            return os.path.join(src_code_folder(), *intermediate_dirs, filename)
        if parent_dir == "layout":
            return os.path.join(src_layout_folder(), *intermediate_dirs, filename)
        if parent_dir == "strings":
            return os.path.join(src_string_folder(), *intermediate_dirs, filename)
        if parent_dir == "drawable":
            return os.path.join(src_drawable_folder(), *intermediate_dirs, filename)
        else:
            # Manifest file
            return manifest_path()


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
