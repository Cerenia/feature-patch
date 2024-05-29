import yaml
from plumbum import local
from typing import Callable

from ..util import configuration, contact_points_folder_path, subrepo_path, path_diff, log, execute, find_separator
from .util import target_code_folder, target_string_folder, target_drawable_folder, target_layout_folder
from .util import src_layout_folder, src_string_folder, src_drawable_folder, src_code_folder, manifest_path

import os


def _prep_folders():
    """
    Clears/Creates target folders in the subrepo to later be filled with all files of contact "contact points"
    expects to be run in bash-like shell
    :return:
    """
    layout_path = target_layout_folder()
    string_path = target_string_folder()
    drawable_path = target_drawable_folder()
    code_path = target_code_folder()
    mkdir = local['mkdir']
    rm = local['rm']
    log.info("Clearing/creating layout, string, drawable, code directories at:")
    log.info(contact_points_folder_path())
    execute(rm["-r", "-v", "-f", contact_points_folder_path()])
    execute(mkdir[contact_points_folder_path()])
    execute(mkdir[layout_path])
    execute(mkdir[string_path])
    execute(mkdir[drawable_path])
    execute(mkdir[code_path])
    extra_files = configuration()['additional_extraction_file_contact_point_paths']
    if extra_files is not None:
        sep = find_separator(extra_files[0])
        for filepath in extra_files:
            execute(mkdir[sep.join(filepath.split(sep)[0:-1]), "-p"])


def _extract_files():
    """
    Walk through expected file hierarchy and find all files that contain the string marker named in configs
    Assumes Code to be in <feature_git_root>/..
    Additionally checks the AndroidManifest file.
    :return:
    """
    _duplicate_files(subrepo_path(), src_code_folder(), None, target_code_folder())
    _duplicate_files(subrepo_path(), src_layout_folder(), None, target_layout_folder())
    _duplicate_files(subrepo_path(), src_drawable_folder(), None, target_drawable_folder())
    _duplicate_files(subrepo_path(), src_string_folder(), None, target_string_folder())
    _duplicate_manifest()
    extra_files = configuration()['additional_extraction_file_paths']
    if extra_files is not None:
        destination_paths = configuration()['additional_extraction_file_contact_point_paths']
        for (idx, path) in enumerate(extra_files):
            sep = find_separator(destination_paths[idx])
            execute(local['cp'][path, sep.join(destination_paths[idx].split(sep)[0:-1])])


def _duplicate_files(subrepo_path: str, top_level_source_dir: str, current_dir: str, top_level_target_dir: str):
    """
        recursively walks through current dir and copies any file that contains the marker into the contact points folder
        Checks each file for valid combination of 'start' and 'end' markers before copying and exits if any file is invalid
    :param subrepo_path: path of the subrepo inside the container
    :param top_level_source_dir: where the files are expected to be listed (code, drawables, strings, layouts..)
    :param current_dir: recursive directory helper, set to topLevelDir if None
    :param top_level_target_dir: target folder path
    """
    if current_dir is None:
        current_dir = top_level_source_dir
    for f_name in os.listdir(current_dir):
        f_path = os.path.join(current_dir, f_name)
        if f_name != os.path.basename(subrepo_path):
            if os.path.isdir(f_path):
                log.debug(f"Traversing into {f_name}")
                _duplicate_files(subrepo_path, top_level_source_dir, f_path, top_level_target_dir)
            elif os.path.isfile(f_path):
                log.debug(f"Checking {f_name} for marker")
                # if retcode == 1, no match was found
                cmd = (local['cat'][f_path] | local['grep'][configuration()["marker"]])
                (retcode, stdout, _) = execute(cmd, retcodes=(0, 1))
                if retcode == 0:
                    src = os.path.join(current_dir, f_name)
                    if not _check_marker_matchings(src):
                        log.critical(f"ERROR: File {src} had an unequal number of starts and ends! "
                              f"Please review the file and run the extraction again.")
                        exit(1)
                    if top_level_source_dir != current_dir:
                        # What needs to be created in the code folder if it doesn't exist yet
                        intermediate = path_diff(f_path, top_level_source_dir)
                        missing_dirs = path_diff(intermediate, f_name)
                        target = os.path.join(top_level_target_dir, missing_dirs)
                        log.debug(f"creating: {target}")
                        if not os.path.isdir(target):
                            execute(local['mkdir']['-p', target])
                        trg = os.path.join(target, f_name)
                    else:
                        trg = os.path.join(top_level_target_dir, f_name)
                    log.info(f"copying {src} into {trg}")
                    local['cp'][src, trg]()
            else:
                log.error(f"{f_name} was not dir or file!")


def _duplicate_manifest():
    """
    Checks manifest file for marker and duplicates it if necessary.
    """
    log.debug(f"Checking {manifest_path()} for marker")
    # if retcode == 1, no match was found
    cmd = (local['cat'][manifest_path()] | local['grep'][configuration()["marker"]])
    (retcode, _, _) = execute(cmd, retcodes=(0, 1))
    if retcode == 0:
        log.info(f"Copying manifest into {contact_points_folder_path()}...")
        cmd = local['cp'][manifest_path(), manifest_path(subrepo_path=True)]
        execute(cmd)


def _check_marker_matchings(file: str):
    """
    :param file: The path of the file to examine
    :return: true is there is an equal nr. of starts and ends (does not catch missorderings)
    """
    with open(file, "r", encoding="utf-8") as f:
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


def extract_feature(start_over=True):
    """
        Extracts any files interfacing the feature into the 'contact_points' folder.
        PRE: config.yml correctly initialized
    :param start_over: Set False if you are continuing extraction after error or manual edit. Will restart the complete
    process by default.
    """
    if start_over:
        _prep_folders()
    _extract_files()
