"""

Expects an extracted feature and clean repo onto which to patch changes where possible

Capabilities:
- Walk through all the contact point files and attempt to match them in the fresh repo (report anything you could not)
- Diff the matched files and attempt to merge (report failures)
"""
from typing import Callable

"""
Merge:
Compare new repo State (Files 'N') and old patch State (Files 'P')
Assumption: patch files have been written in such a way as to minimize the interface
 => We want to apply all changes outside of a marker to get 'P' -> 'N'
 => We want to identify where the marker contents should be placed in 'N' which ideally just means not applying the 
 subtracting steps to get rid of the marker spots (need to check how to achieve this with the diffing libs)
 
 If anything fails, we want to be able to descriptively explain why and let the user deal with it instead 
 (provide log output) but then continue on (don't crash the whole thing because of a failure)
 
 Finally we want to output a summary with action point that the user should have a manual look at.
 
 Obvious cases:
 - file can not be matched (e.g., a class completely dissapeared or was translated to Kotlin)
 
 
 Needed Pieces:
 - Log file location
 - Log file prep
 
 - match files (record matchings in some file that then can be walked. Add a done or not flag to this structure so the 
 program can be started and stopped with some flags to steer what it tries to do again or not)
 - iterate over all matches
    - compute diff
    - merge (resulting in files 'M')
    - replace 'N' with 'M'
"""


import diff_match_patch as dmp_module
from .util import target_code_folder, target_drawable_folder, target_string_folder, target_layout_folder
from .util import src_drawable_folder, src_string_folder, src_layout_folder, src_code_folder, manifest_path
from ..util import runtime_record_path, error_record_path, path_diff, log, configuration
import os
import json


def match_files(subrepo_dir: str, container_dir: str):
    """
    walks through the directory and attempts to match all the files it contains. For each success, appends the runtime log.
    for failures, appends the match error log
    :param subrepo_dir: root of folder to walk
    :param container_dir: corresponding folder in the container repository
    :param runtime_log: path to runtime log file
    """
    # walk through folder hierarchy
    # for each file, check to find the equivalent file in the other folder
    # if found, update the runtime log, otherwise update the error log
    for dirpath, _, filenames in os.walk(subrepo_dir):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            diff = path_diff(filepath, subrepo_dir)
            match = os.path.join(container_dir, diff)
            if os.path.isfile(match):
                create_runtime_entry(diff, filepath, match)
            else:
                write_error(f"ERROR: {diff} was not found in container repository, please check this file manually.",
                            filepath, log.error)


def create_runtime_entry(diff, filepath, match):
    log.info(f"Found matching {diff} in container repository!")
    with open(runtime_record_path(), 'a') as f:
        f.write(f"{format_runtime_task(filepath, match)},\n")

def format_runtime_task(subrepo_file: str, matching_container_file: str = None):
    """
    creates an element of the runtime or error dictionary.
    runtime if both paths are given, error otherwise.
    uses Json formatting
    :return: a Json formatted python dictionary
    """
    element = dict()
    element["contact_point"] = subrepo_file
    element["match"] = "" if matching_container_file is None else matching_container_file
    element["diffed"] = False
    return json.dumps(element)


def write_error(log_msg: str, filepath: str, logfunction: Callable[[str], None]):
    """
    Log an error or critical event both to the error record and log.
    :param log_msg: What message to print to console and log.
    :param filepath: Which file did the error occur in.
    :param logfunction: PRE: must be error or critical.
    :return:
    """
    assert logfunction == log.error or logfunction == log.critical, "Precondition violated! logfunction must be error or critical."
    logfunction(log_msg)
    with open(error_record_path(), 'a') as f:
        f.write(f"{format_runtime_task(filepath)},\n")


def initiate_runtime_log():
    """
     Walk through all the files and attempt to match them.
     Record if you cannot match a file and save the matched pairs + status indicator in the working dir.
    :return:
    """
    for path in [runtime_record_path, error_record_path]:
        # truncate or create file
        with open(path(), "w") as f:
            # Initiate Json Array Literal
            f.write("[\n")

    # go through all folders and create matchings
    match_files(target_code_folder(), src_code_folder())
    match_files(target_drawable_folder(), src_drawable_folder())
    match_files(target_string_folder(), src_string_folder())
    match_files(target_layout_folder(), src_layout_folder())
    # Manifest
    if os.path.isfile(manifest_path(subrepo_path=True)):
        create_runtime_entry("AndroidManifest.xml", manifest_path(subrepo_path=True), manifest_path())

    # Close Json Array Literal
    for path in [runtime_record_path, error_record_path]:
        with open(path(), "a") as f:
            f.write("]")


class MissmatchedMarkerError(Exception):
    """
    Raised when a missmatch between 'start' and 'end' markers are detected.
    """
    pass


def generate_patch_content(match: str, contact_point: str, filepath):
    # Will have to add corner cases as we see them and add them to the test repository
    diffs = diff_lines(match, contact_point)
    # Isolate the diff lines that contain the contact point
    marker = configuration()["marker"]
    # list of tuples, start/end, expects "start" and "end" to be part of the markers
    marker_indices = []
    marker_idx = (None, None)
    for idx, diff in enumerate(diffs):
        if marker in diff[1]:
            if "start" in diff[1]:
                if marker_idx.first is None:
                    marker_idx = (idx, None)
                else:
                    error_msg = f"Found repeated 'start' marker before matching 'end' marker! Check this file manually."
                    write_error(error_msg + f"\n {filepath}", filepath, log.error)
                    raise MissmatchedMarkerError(error_msg)
            elif "end" in diff[1]:
                if marker_idx.first is None:
                    error_msg = f"'end' marker found before 'start' marker! Check this file manually."
                    write_error(error_msg + f"\n {filepath}", filepath, log.error)
                    raise MissmatchedMarkerError(error_msg)
                else:
                    marker_idx = (marker_idx.first, idx)
            else:
                error_msg = f"Invalid marker! Neither 'start' or 'end' specified."
                write_error(error_msg + f"\n {filepath}", filepath, log.error)
                raise MissmatchedMarkerError(error_msg)
            if marker_idx.first is not None and marker_idx.end is not None:
                marker_indices.append(marker_idx)
                marker_idx = (None, None)
    # Naively try to apply them
    dmp = dmp_module.diff_match_patch()
    patch, _ = dmp.patch_apply([diffs[start:end+1] for (start, end) in marker_indices], match)
    return patch


def diff_lines(text1: str, text2: str):
    # TODO: May want to allow to tweak the options of the module for certain corner cases
    # https://github.com/google/diff-match-patch/wiki/Line-or-Word-Diffs
    dmp = dmp_module.diff_match_patch()
    intermediate = dmp.diff_linesToChars(text1, text2)
    log.info(f"intermediate: {intermediate}")
    line_text1 = intermediate.chars1
    line_text2 = intermediate.chars2
    line_array = intermediate.lineArray
    return dmp.diff_charsToLines(dmp.diff_main(line_text1, line_text2, False), line_array)


def run():
    # iterate through runtime log
    # for each entry that has not yet run, generate patched file
    # replace 'match'
    # (any error handling that will become apparent)
    # update runtime log

    # assume the entire record can be kept in memory for now
    with open(runtime_record_path(), "r") as f:
        records = json.loads(f.read())
    current_record = 0
    while records[current_record]["diffed"]:
        current_record += 1
    while current_record < len(records):
        match_path = records[current_record]["match"]
        with open(match_path, "r") as f:
            match = f.read()
        with open(records[current_record]["contact_point"], "r") as f:
            contact_point = f.read()
        try:
            new_content = generate_patch_content(match, contact_point, records[current_record]["contact_point"])
            with open(match_path, "w") as f:
                f.write(new_content)
        except Exception as e:
            write_error(f"An exception occured:\n {str(e)}", records[current_record]["match"])
            pass
        finally:
            # Write the updated record to file after each iteration
            records[current_record]["diffed"] = True
            with open(runtime_record_path(), "w") as f:
                f.write(json.dumps(records))
