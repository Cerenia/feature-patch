"""

Expects an extracted feature and clean repo onto which to patch changes where possible

Capabilities:
- Walk through all the contact point files and attempt to match them in the fresh repo (report anything you could not)
- Diff the matched files and attempt to merge (report failures)
"""
import sys

import traceback
from typing import Callable
from collections import namedtuple

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
from ..util import runtime_record_path, error_record_path, path_diff, log, configuration, constants, contact_points_folder_path
from ..git import execute, checkout_unmodified_file, unmodified_file_path
import os
import json
import re
from plumbum import local


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
            subrepo_filepath = os.path.join(dirpath, filename)
            container_match = os.path.join(container_dir, filename)
            if os.path.isfile(container_match):
                write_runtime_record(filename, subrepo_filepath, container_match)
            else:
                # Check if the file is a pure-copy file => Markers on two adjacent lines without content
                with open(os.path.join(dirpath, filename), "r") as f:
                    content = f.read()
                marker = configuration()["marker"]
                # '$^' makes sure that there is no content between the markers indicating that the entire file should be copied
                p = rf"{marker}\s*start\s*$\n^\s*//{marker}\s*end|" \
                    rf"{marker}\s*start\s*-->\s*$\n^\s*<!--\s*{marker}\s*end" # XML comments
                found_match = re.search(p, content, re.MULTILINE)
                if found_match:
                    container_match = os.path.join(container_dir, ".")
                    write_runtime_record(filename, subrepo_filepath, container_match)
                else:
                    write_error(
                        f"ERROR: {filename} was not found in container repository and {filename} is not a pure-copy file, please check this file manually.",
                        subrepo_filepath, log.error)


def write_runtime_record(diff, filepath, match):
    m = re.search(r"\.$", match)
    if m:
        log.info(f"Found pure copy file {diff}!")
        log.info(m.group(0))
    else:
        log.info(f"Found matching {diff}!")
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
    element["processed"] = False
    return json.dumps(element)


def write_error(log_msg: str, filepath: str, logfunction: Callable[[str], None]):
    """
    Log an error or critical event both to the error record and log.
    :param log_msg: What message to print to console and log.
    :param filepath: Which file did the error occur in.
    :param logfunction: PRE: must be warn, error or critical.
    :return:
    """
    assert logfunction == log.error or logfunction == log.critical or logfunction == log.warning, "Precondition violated! logfunction must be error or critical."
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
        write_runtime_record("AndroidManifest.xml", manifest_path(subrepo_path=True), manifest_path())

    # Close Json Array Literal
    for path in [runtime_record_path, error_record_path]:
        with open(path(), "r+") as f:
            content = f.read()
            if content == "[\n":
                if path == runtime_record_path:
                    log.critical("No matches found, cannot proceed. Is the correct branch checked out?")
                    exit(1)
                else:
                    content = content + "]"
            else:
                content = content[:-2]
                content = content + "\n]"
            f.seek(0)
            f.truncate()
            f.write(content)


class MissmatchedMarkerError(Exception):
    """
    Raised when a missmatch between 'start' and 'end' markers are detected.
    """
    pass


def linediffs(text1: str, text2: str):
    deadline = constants()["per_file_diff_deadline"]
    deadline = None if deadline == "None" else float(deadline)
    dmp = dmp_module.diff_match_patch()
    return dmp.diff_lineMode(text1, text2, deadline)


def generate_patch_content(match: str, contact_point: str, contact_point_path: str):
    # TODO: Will have to add corner cases as we see them and add them to the test repository
    match_filepath = path_diff(contact_point_path, contact_points_folder_path())
    checkout_unmodified_file(match_filepath)
    with open(unmodified_file_path(match_filepath, configuration()["windows"]), "r") as f:
        unmodified_match_text = f.read()
    diffs = generate_diffs(unmodified_match_text, match, match_filepath)
    print(diffs)
    exit(0)
    diffs = generate_diffs(match, contact_point, contact_point_path)
    marker = configuration()["marker"]
    # Isolate the diff lines that contain the contact point
    # list of tuples, start/end, expects "start" and "end" to be part of the markers
    marker_indices = []
    # TODO: Continue here based on handwritten notes
    # Naively try to apply them
    dmp = dmp_module.diff_match_patch()
    # Don't split strings in diffs => was inserting things in the middle of a line otherwise
    # https://github.com/google/diff-match-patch/blob/master/python3/diff_match_patch.py#L1687
    dmp.Match_MaxBits = 0
    patch, applied = dmp.patch_apply([patches[m] for m in marker_indices], match)
    return "".join(patch)


def generate_diffs(match_text, contact_point_text, contact_point_path):
    """
    iterate over all of them and turn any that contain the marker into an insertion.
    Add context from original file to allow the algorithm to find where to insert it.
    :return: the transformed diffs
    """
    # TODO: Check out the untouched previous version (1.0) and diff against new version (1.1)
    checkout_unmodified_file(contact_point_path)
    # TODO: Check if any of the context around the changes has changed from 1.0 to 1.1
    with open(unmodified_file_path(contact_point_path), "r") as f:
        unmodified_text = f.read()

    new_diffs = []
    context = ""
    for idx, d in enumerate(diffs):
        # TODO: if yes, add the changed context to the diff around the match lines
        # TODO: Otherwise just add the untouched context
        pass
    return new_diffs


def run():
    # create runtime record
    # iterate through runtime log
    # for each entry that has not yet run, generate patched file
    # replace 'match'
    # (any error handling that will become apparent)
    # update runtime log
    initiate_runtime_log()
    # assume the entire record can be kept in memory for now
    with open(runtime_record_path(), "r") as f:
        records = json.load(f)
    current_record = 0
    while bool(records[current_record]["processed"]):
        current_record += 1
    while current_record < len(records):
        try:
            subrepo_path = records[current_record]["contact_point"]
            container_path = records[current_record]["match"]
            if re.search(r"\.$", container_path) is not None:
                # Pure copy file, simply copy
                execute(local["cp"][subrepo_path, container_path])
            else:
                with open(container_path, "r", encoding="utf-8") as f:
                    match = f.read()
                with open(records[current_record]["contact_point"], "r", encoding="utf-8") as f:
                    contact_point = f.read()
                    new_content = generate_patch_content(match, contact_point, records[current_record]["contact_point"])
                    with open(container_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
        except Exception as e:
            write_error(f"{sys.last_type, traceback.format_exception(e)}\n", records[current_record]["match"], log.critical)
            exit(1)
        finally:
            # Write the updated record to file after each iteration
            records[current_record]["diffed"] = True
            with open(runtime_record_path(), "w") as f:
                f.write(json.dumps(records))
            current_record = current_record + 1
