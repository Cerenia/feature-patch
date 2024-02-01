"""

Expects an extracted feature and clean repo onto which to patch changes where possible

Capabilities:
- Walk through all the contact point files and attempt to match them in the fresh repo (report anything you could not)
- Diff the matched files and attempt to merge (report failures)
"""
import sys

import traceback
from functools import reduce
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
from .util import target_code_folder, target_drawable_folder, target_string_folder, target_layout_folder, map_contact_points_path_to_container
from .util import src_drawable_folder, src_string_folder, src_layout_folder, src_code_folder, manifest_path
from ..util import runtime_record_path, error_record_path, path_diff, log, configuration, constants, contact_points_folder_path
from ..git import execute, checkout_unmodified_file, unmodified_file_path
import os
import json
import re
from plumbum import local


def print_all_diffs(diffs):
    title_map = {0: "\nEquality", -1: "\nDeletion", 1: "\nInsertion"}
    result = ""
    for d in diffs:
        print(f"{title_map[d[0]]}:")
        print(d[1])
        result = result + f"{title_map[d[0]]}:\n" + d[1] + "\n"
    return result


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
                with open(os.path.join(dirpath, filename), "r", encoding="utf-8") as f:
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
        f.write(f"\n{format_runtime_task(filepath, match)},")


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
    assert logfunction == log.error or logfunction == log.critical or logfunction == log.warning, "Precondition violated! logfunction must be error, critical or warning."
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
            f.write("[")

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
        with open(path(), "r+", encoding="utf-8") as f:
            content = f.read()
            if content == "[\n":
                if path == runtime_record_path:
                    log.critical("No matches found, cannot proceed. Is the correct branch checked out?")
                    exit(1)
                else:
                    content = content + "]"
            else:
                content = content[:-1]
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


def print_some_diffs(title, d, equality=True, deletion=True, markerContains=True, marker=configuration()["marker"]):
    print(title)
    print("_____________________")
    print(len(d))
    if equality:
        print("Equality:")
        if any(x[0] == 0 for x in d):
            print(next(x[1] for x in d if x[0] == 0))
        else:
            print("No Equalities...")
    if deletion:
        print("Deletion:")
        if any(x[0] == -1 for x in d):
            print(next(x[1] for x in d if x[0] == -1))
        else:
            print("No Deletions...")
    if markerContains:
        print("Contains Marker:")
        if any(marker in x[1] for x in d):
            print(next(str(x[0]) for x in d if marker in x[1]) + "\n", next(x[1] for x in d if marker in x[1]))
        else:
            print("No Markers in any diffs...")


def generate_merged_content(match: str, contact_point: str, contact_point_path: str):
    # TODO: Will have to add corner cases as we see them and add them to the test repository
    checkout_unmodified_file(contact_point_path)
    with open(unmodified_file_path(contact_point_path, configuration()["windows"]), "r", encoding="utf-8") as f:
        unmodified_match_text = f.read()
    # Anything added in between the markers will be positive here
    # => This assumption does not hold. May morph, e.g., a button description in an XML file that comes after into the markers.
    if "app_main.xml" in contact_point_path:
        diffs = compute_line_diff(match, contact_point, do_log=True)
    else:
        diffs = compute_line_diff(match, contact_point)
    if "app_main.xml" in contact_point_path:
        print("app_main diffs before transformations:")
        text = print_all_diffs(diffs)
        with open(os.path.join(configuration()["working_dir"], "before_transformations.xml"), "w+", encoding="utf-8") as f:
            f.write(text)
    # Match up any changed lines between unmodified and match and change these in diffs
    updated_code = compute_line_diff(unmodified_match_text, match)
    # Take changes to upgrade into account and turn them into equalities
    diffs = transform_diffs(updated_code, diffs)
    if "app_main.xml" in contact_point_path:
        print("app_main diffs after transformations:")
        text = print_all_diffs(diffs)
        with open(os.path.join(configuration()["working_dir"], "after_transformations.xml"), "w+", encoding="utf-8") as f:
            f.write(text)
    return dmp_module.diff_match_patch().diff_text2(diffs)

"""
if not reduce(lambda value, el: value and el, results):
    last_idx = match_filepath.rfind(os.sep)
    write_error(f"Not all patches were applied for:{match_filepath[last_idx + 1:]}", match_filepath, log.warning)
    print([str(p) for p in patches])
    print(results)
"""


def compute_line_diff(text1, text2, deadline=None, do_log=False):
    """
    pull the deadline out of the configs (if not provided) and pass onto line_diff
    preprocesses text1 and text2 to treat anything between markers as immutable
    :return: line-level diff turning text1 into text2
    """
    if deadline is None:
        deadline = constants()["per_file_diff_deadline"]
        deadline = None if deadline == "None" else float(deadline)
    diff = line_diff(group_marker_content(text1), group_marker_content(text2), deadline, do_log=do_log)
    # undo any groupings
    ungrouped_diff = []
    for d in diff:
        ungrouped_diff.append((d[0], ungroup_marker_content(d[1])))
    return ungrouped_diff


def transform_diffs(diff_update, diff_patched):
    """
    Turns any deletion in diff_update that can be matched by an insertion in diff_changes into an equality.
    # TODO: Very naive approach, may want to refine as we go
    :param diff_update: Diff between unmodified and updated files
    :param diff_patched: Diff between updated and patched files
    :return: 
    """
    for update in diff_update:
        if update[0] == 1:
            # Search for equivalent deletion in diffs and turn into equality
            new_element = ()
            for idx, d in enumerate(diff_patched):
                if d[0] == -1:
                    if d[1].strip() == update[1].strip():
                        new_element = (0, d[1])
                        break
                    else:
                        log.debug("The Insertion did not match the deletion:\n", update[1], "!=\n", d[1])
            if new_element != ():
                if idx == 0:
                    diff_patched = [new_element] + diff_patched[idx + 1:]
                if idx == len(diff_patched) - 1:
                    diff_patched = diff_patched[:idx] + [new_element]
                else:
                    diff_patched = diff_patched[0:idx] + [new_element] + diff_patched[idx + 1:]
    return diff_patched


def group_marker_content(text):
    """
    In order to make sure that the contents between the marker are treated as one unchanged block, we concatenate
    the lines with ||<marker>|| that are inbetween the markers. This way, this content is treated as a single line
    when using dmp.diff_linesToChars
    :return: text with anything between the markers regrouped in a single line
    """
    marker = configuration()['marker']
    new_lines = []
    grouping = None
    for line in text.split("\n"):
        if grouping is not None:
            grouping = grouping + f"||{marker}||" + line
            if marker in line and "end" in line:
                new_lines.append(grouping)
                grouping = None
        elif marker in line and "start" in line:
            grouping = line
        else:
            new_lines.append(line)
    return "\n".join(new_lines)


def ungroup_marker_content(text):
    """
    Inverse of 'group_marker_content'
    :return:
    """
    return text.replace(f"||{configuration()['marker']}||", "\n")


def line_diff(text1, text2, deadline, do_log=False):
    """
    Pre: text1 and/or text2 have been passed through 'group_marker_content' if they contain marked content
    :param deadline: timeconstraint for the diff in [s], may be None
    :param do_log:
    :return:
    """
    dmp = dmp_module.diff_match_patch()
    # Scan the text on a line-by-line basis
    (text1, text2, linearray) = dmp.diff_linesToChars(text1, text2)

    diffs = dmp.diff_main(text1, text2, False, deadline)

    # Convert the diff back to original text.
    dmp.diff_charsToLines(diffs, linearray)
    if do_log:
        print("app_main line_diffs before clean_up_semantics")
        print_all_diffs(diffs)
    # Eliminate freak matches (e.g. blank lines)
    # dmp.diff_cleanupSemantic(diffs)
    # This was resulting in diffs that were finer than line by line.
    return diffs


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
            if re.search(r"\.$", container_path) is not None or re.search(r"/.$", container_path) is not None:
                # Pure copy file, simply copy
                execute(local["cp"][subrepo_path, container_path], do_log=False)
                execute(local["git"]["add", container_path], do_log=False)
                log.info(f"Copied {os.path.basename(subrepo_path)}...")
            else:
                log.info(f"Creating a merged version of {os.path.basename(subrepo_path)}...")
                with open(container_path, "r", encoding="utf-8") as f:
                    match = f.read()
                with open(records[current_record]["contact_point"], "r", encoding="utf-8") as f:
                    contact_point = f.read()
                    new_content = generate_merged_content(match, contact_point, records[current_record]["contact_point"])
                    with open(container_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
        except Exception as e:
            write_error(f"{sys.last_type, traceback.format_exception(e)}\n", records[current_record]["match"], log.critical)
            exit(1)
        finally:
            # Write the updated record to file after each iteration
            records[current_record]["diffed"] = True
            with open(runtime_record_path(), "w") as f:
                f.write(json.dumps(records, indent=1))
            current_record = current_record + 1
