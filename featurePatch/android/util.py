import os
from ..util import contact_points_path, configuration


def target_code_folder():
    return os.path.join(contact_points_path(), "code")


def target_drawable_folder():
    return os.path.join(contact_points_path(), "drawable")


def target_string_folder():
    return os.path.join(contact_points_path(), "strings")


def target_layout_folder():
    return os.path.join(contact_points_path(), "layout")


def src_code_folder():
    return configuration()['android_src_root']


def src_layout_folder():
    return configuration()['android_layout_root']


def src_drawable_folder():
    return configuration()['android_drawable_root']


def src_string_folder():
    return configuration()['android_string_root']
