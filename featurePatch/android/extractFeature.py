"""
TODO:
- Document expected file hierarchy
Code (contains same folder structure and any file with marker)
Layout
Drawables
Strings


Capabilities:
- create folders inside subrepo (clear if they exist) which holds all contact file points for later diff
- push these files to subrepo
"""

from plumbum import local
from ..util import configuration, contact_points_path, subrepo_path, path_diff, get_logger
from .util import target_code_folder, target_string_folder, target_drawable_folder, target_layout_folder
from .util import src_layout_folder, src_string_folder, src_drawable_folder, src_code_folder
import logging

import os

log: logging.Logger = get_logger()


def prep_folders(windows=False):
    """
    Clears/Creates target folders in the subrepo to later be filled with all files of contact
    expects to be run in bash shell (TODO: add a Windows flag + any changed commands?)
    :return:
    """
    # expand path if using cygwin
    os.environ["PATH"] = (
        # TODO: (for plumbum) extract to configs once structure is clearer. or just don't use plumbum :(
        os.path.expanduser("/c/Program Files/Git/usr/bin/") + ";" + os.environ["PATH"]
    )
    layout_path = target_layout_folder()
    string_path = target_string_folder()
    drawable_path = target_drawable_folder()
    code_path = target_code_folder()
    if not windows:
        mkdir = local['mkdir']
        rm = local['rm']
        log.info("Clearing/creating layout, string, drawable, code directories at:")
        log.info(contact_points_path())
        rm["-r", "-v", "-f", contact_points_path()]()
        mkdir[contact_points_path()]()
        mkdir[layout_path]()
        mkdir[string_path]()
        mkdir[drawable_path]()
        mkdir[code_path]()


def extract_files():
    """
    Walk through expected file hierarchy and find all files that contain the string marker in configs
    Assumes Code to be in <android_feature_root>/..
    :return:
    """
    duplicate_files(subrepo_path(), src_code_folder(), None, target_code_folder())
    duplicate_files(subrepo_path(), src_layout_folder(), None, target_layout_folder())
    duplicate_files(subrepo_path(), src_drawable_folder(), None, target_drawable_folder())
    duplicate_files(subrepo_path(), src_string_folder(), None, target_string_folder())


def duplicate_files(subrep_path: str, top_level_source_dir: str, current_dir: str, top_level_target_dir: str):
    """
        recursively walks through current dir and copies any file that contains the marker into
    :param subrep_path: path of the subrepo inside the container
    :param top_level_source_dir: where the files are expected to be listed (code, drawables, strings, layouts..)
    :param current_dir: recursive directory helper, set to topLevelDir if None
    :param get_top_level_target_dir: pass the function handle for the target folder
    """
    if current_dir is None:
        current_dir = top_level_source_dir
    for f_name in os.listdir(current_dir):
        f_path = os.path.join(current_dir, f_name)
        if f_name != os.path.basename(subrep_path):
            if os.path.isdir(f_path):
                log.debug(f"Traversing into {f_name}")
                duplicate_files(subrep_path, top_level_source_dir, f_path, top_level_target_dir)
            elif os.path.isfile(f_path):
                log.debug(f"Checking {f_name} for marker")
                # if retcode == 1, no match was found
                cmd = (local['cat'][f_path] | local['grep'][configuration()["marker"]])
                (retcode, stdout, _) = cmd.run(retcode=(0, 1))
                if retcode == 0:
                    src = os.path.join(current_dir, f_name)
                    if not check_marker_matchings(src):
                        log.critical(f"ERROR: File {src} had an unequal number of starts and ends! "
                              f"Please review the file and run the extraction again.")
                        exit(1)
                    if top_level_source_dir != current_dir:
                        # What needs to be created in the code folder if it doesn't exist yet
                        missing_dirs = path_diff(path_diff(f_path, top_level_source_dir), f_name)
                        target = os.path.join(top_level_target_dir, missing_dirs)
                        log.debug(f"creating: {target}")
                        if not os.path.isdir(target):
                            local['mkdir'][target]()
                        trg = os.path.join(target, f_name)
                    else:
                        trg = os.path.join(top_level_target_dir, f_name)
                    log.info(f"copying {src} into {trg}")
                    local['cp'][src, trg]()
            else:
                log.error(f"{f_name} was not dir or file!")


def check_marker_matchings(file: str):
    """
    :param file: The path of the file to examine
    :return: true is there is an equal nr. of starts and ends (does not catch missorderings)
    """
    with open(file, "r") as f:
        lines = f.readlines()
    starts = 0
    ends = 0
    for l in lines:
        if configuration()["marker"] in l:
            if "start" in l:
                starts += 1
            elif "end" in l:
                ends += 1
    return starts == ends

