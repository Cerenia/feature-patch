import sys
import traceback
from typing import Callable
import diff_match_patch as dmp_module
from .util import target_code_folder, target_drawable_folder, target_string_folder, target_layout_folder
from .util import src_drawable_folder, src_string_folder, src_layout_folder, src_code_folder, manifest_path
from ..util import runtime_record_path, error_record_path, log, configuration, constants, print_all_diffs, DiffList, path_diff
from ..git import execute, _checkout_unmodified_file, unmodified_file_path
import os
import json
import re
from fuzzywuzzy import fuzz
from plumbum import local


def _match_files(contact_point_subrepo: str, container_dir: str):
    """
    walks through the directory and attempts to match all the files it contains. For each success, appends the runtime record.
    for failures, appends 'errors'
    :param contact_point_subrepo: root of folder to walk
    :param container_dir: corresponding folder in the container repository
    :param runtime_log: path to runtime log file
    """
    for dirpath, _, filenames in os.walk(contact_point_subrepo):
        for filename in filenames:
            subrepo_filepath = os.path.join(dirpath, filename)
            log.debug(f'subrepo_filepath: \n{subrepo_filepath}')
            log.debug(f'subrepo_dir: \n{contact_point_subrepo}')
            diff = path_diff(subrepo_filepath, contact_point_subrepo)
            log.debug(f'diff: \n{diff}')
            container_match = os.path.join(container_dir, diff)
            log.debug(f'container_match: \n{container_match}')
            if os.path.isfile(container_match):
                _write_runtime_record(filename, subrepo_filepath, container_match)
            else:
                # Check if the file is a pure-copy file => Markers on two adjacent lines without content inbetween
                with open(os.path.join(dirpath, filename), "r", encoding="utf-8") as f:
                    content = f.read()
                marker = configuration()["marker"]
                # '$^' makes sure that there is no content between the markers indicating that the entire file should be copied
                #               Java-style comments
                p = rf"{marker}\s*start\s*$\n^\s*//{marker}\s*end|" \
                    rf"{marker}\s*start\s*-->\s*$\n^\s*<!--\s*{marker}\s*end" # XML comments
                found_match = re.search(p, content, re.MULTILINE)
                if found_match:
                    container_match = os.path.join(container_dir, ".")
                    _write_runtime_record(filename, subrepo_filepath, container_match)
                else:
                    _write_error(
                        f"ERROR: {filename} was not found in container repository and {filename} is not a pure-copy file, please check this file manually.",
                        subrepo_filepath, log.error)


def _write_runtime_record(filename, filepath, match):
    """
    Writes an entry to the runtime record.
    Logs what kind of file was found.
    :param filename: the name of the matched file
    :param filepath: path to file in contact points folder
    :param match: path to file in container repository
    :return:
    """
    m = re.search(r"\.$", match)
    if m:
        log.info(f"Found pure copy file {filename}!")
        log.info(m.group(0))
    else:
        log.info(f"Found matching {filename}!")
    with open(runtime_record_path(), 'a') as f:
        f.write(f"\n{_format_runtime_task(filepath, match)},")


def _format_runtime_task(subrepo_file: str, matching_container_file: str = None):
    """
    defines the format of the runtime or error dictionary as json string.
    runtime if both paths are given or pure-copy, error otherwise.
    uses Json formatting
    :return: a Json formatted python dictionary
    """
    element = dict()
    element["contact_point"] = subrepo_file
    element["match"] = "" if matching_container_file is None else matching_container_file
    element["processed"] = False
    return json.dumps(element)


def _write_error(log_msg: str, filepath: str, logfunction: Callable[[str], None]):
    """
    Log a warning,  error or critical event both to the error record and log.
    :param log_msg: What message to print to console and log.
    :param filepath: Which file does the error refer to
    :param logfunction: PRE: must be warn, error or critical.
    :return:
    """
    assert logfunction == log.error or logfunction == log.critical or logfunction == log.warning, "Precondition violated! logfunction must be error, critical or warning."
    logfunction(log_msg)
    with open(error_record_path(), 'a') as f:
        f.write(f"{_format_runtime_task(filepath)},\n")


def match():
    """
     Walk through all the files in the contact_point folder and attempt to match them.
     Record if you cannot match a file and save the matched pairs + status indicator in the runtime_record.
    :return:
    """
    for path in [runtime_record_path, error_record_path]:
        # truncate or create file
        with open(path(), "w") as f:
            f.write("[")# Initiate Json Array Literal

    # go through all folders and create matchings
    print("###\n# Checking code folder...\n###\n")
    #print(target_code_folder())
    #print(src_code_folder())
    _match_files(target_code_folder(), src_code_folder())
    #print(target_drawable_folder())
    #print(src_drawable_folder())
    #print("###\n# Checking drawable folder...\n###\n")
    _match_files(target_drawable_folder(), src_drawable_folder())
    #print(target_string_folder())
    #print(src_string_folder())
    print("###\n# Checking string (values) folder...\n###\n")
    _match_files(target_string_folder(), src_string_folder())
    print("###\n# Checking layout folder...\n###\n")
    _match_files(target_layout_folder(), src_layout_folder())
    # Manifest
    if os.path.isfile(manifest_path(subrepo_path=True)):
        _write_runtime_record("AndroidManifest.xml", manifest_path(subrepo_path=True), manifest_path())

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


def _generate_merged_content(match: str, contact_point: str, contact_point_path: str):
    """
    Best effort merge of the contact point changes with the upgraded container file. Takes the
    unmodified container file (on which the contact point changes are based) into account.
    :param match: The text of the matched file in the upgraded container repo.
    :param contact_point: The text of the contact point file.
    :param contact_point_path: The path to the contact point file.
    :return: The merged text ready to be written to file.
    """
    # TODO: Will have to add corner cases as we see them and add them to the test repository
    _checkout_unmodified_file(contact_point_path)
    with open(unmodified_file_path(contact_point_path, configuration()["windows"]), "r", encoding="utf-8") as f:
        unmodified_match_text = f.read()
    return _create_diff(match, contact_point, unmodified_match_text)



def _create_diff(upstream: str, modified_predecessor: str, unmodified_predecessor: str):
    """"
        @see _generate_merged_content
        this is refactored for unittesting
    """
    (diffs, intermediate) = _create_intermediate_diffs(upstream, modified_predecessor, unmodified_predecessor)
    # Take changes to upgrade into account and turn them into equalities
    diffs = _transform_diffs(intermediate, diffs)
    return dmp_module.diff_match_patch().diff_text2(diffs)


def _create_intermediate_diffs(upstream: str, modified_predecessor: str, unmodified_predecessor: str):
    """"
        @see _generate_merged_content
        this is refactored for unittesting
    """
    diffs = _compute_line_diff(upstream, modified_predecessor)
    # Match up any changed lines between unmodified and match and change these in diffs
    intermediate = _compute_line_diff(unmodified_predecessor, upstream)
    return (diffs, intermediate)


def _compute_line_diff(text1: str, text2: str, deadline: float=None):
    """
    pull the deadline out of the configs (if not provided) and pass onto line_diff
    preprocesses text1 and text2 to treat anything between markers as immutable
    :return: line-level diff turning text1 into text2
    """
    if deadline is None:
        deadline = constants()["per_file_diff_deadline"]
        deadline = None if deadline == "None" else float(deadline)
    diff = _line_diff(_group_marker_content(text1), _group_marker_content(text2), deadline)
    # undo any groupings
    ungrouped_diff = []
    for d in diff:
        ungrouped_diff.append((d[0], _ungroup_marker_content(d[1])))
    return ungrouped_diff


def _transform_diffs(unrelated_diffs: DiffList, ti_related_diff: DiffList):
    """
    Creates a list of equalities from both diffs that should result in the upstream file + any marked insertions.
    :param unrelated_diffs: Diff between unmodified predecessor and upstream
    :param ti_related_diff: Diff between upstream and modified_predecessor
    :return: A mutated version of ti_related_diff, where any changes resulting from the downgrade (captured by unrelated_diffs) are ignored
    # TODO: Very naive approach, may want to refine as we go
    Notation:
    ti := ti_related_diff
    un := unrelated_diff
    I(x) := Insertion in difflist x
    D(x) := Deletion in difflist x
    E(x) := Equality in difflist x
    Algorithm:
        if E(ti) -> E(ti)
        if I(ti):
            if ∃ D(un) == I(ti):
                I(ti) -> ∅ // delete this insertion out of the set
            else:
                I(ti) -> E(ti)
        if D(ti):
            if ∃ I(ti) == D(ti):
                D(ti) -> E(ti)
    POST: The final list only includes equalities.
    """

    # first element of the diff tuple indicates the type of diff
    # Typemap: (-1-Deletion, 1-Insertion, 0-Equality)
    tm = {'equality': 0, 'deletion': -1, 'insertion': 1}

    result = []

    min_fuzz_score = constants()['min_fuzz_score']

    for d in ti_related_diff:
        diff_type = d[0]
        diff_text = d[1]
        if diff_type == tm['equality']:
            result.append(d)
        elif diff_type == tm['deletion']:
            match_found = False
            for (dt, dtext) in unrelated_diffs:
                if dt == tm['insertion'] and fuzz.ratio(dtext, diff_text) >= min_fuzz_score:
                    match_found = True
                    break # found the correct match, no need to keep iterating
            if not match_found:
                log.critical(f'found a deletion without matching insertion: \n{diff_text}')
            # Turn deletion into equality
            result.append((0, diff_text))
        elif diff_type == tm['insertion']:
            match_found = False
            for (dt, dtext) in unrelated_diffs:
                if dt == tm['deletion'] and fuzz.ratio(dtext, diff_text) >= min_fuzz_score:
                    match_found = True
                    break # found the correct match, no need to keep iterating
            if not match_found:
                result.append((0, diff_text))
            # Else we simply ignore this insertion.

    return result


def _group_marker_content(text: str):
    """
    In order to make sure that the contents between the marker are treated as one immutable block, we concatenate
    the lines with ||<marker>|| that are inbetween the 'start' and 'end' markers. This way, this content is treated
    as a single line when using dmp.diff_linesToChars
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


def _ungroup_marker_content(text: str):
    """
    Inverse of 'group_marker_content'
    :return:
    """
    return text.replace(f"||{configuration()['marker']}||", "\n")


def _line_diff(text1: str, text2: str, deadline: float):
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
    #log.debug("line_diffs:\n" + print_all_diffs(diffs))
    # Eliminate freak matches (e.g. blank lines)
    # dmp.diff_cleanupSemantic(diffs)
    # => This was resulting in diffs that were finer than line by line, so we consciously omit it.
    return diffs


def patch():
    # assume the entire record can be kept in memory
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
                    new_content = _generate_merged_content(match, contact_point, records[current_record]["contact_point"])
                    with open(container_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
        except Exception as e:
            _write_error(f"{sys.last_type, traceback.format_exception(e)}\n", records[current_record]["match"], log.critical)
            exit(1)
        finally:
            # Write the updated record to file after each iteration
            records[current_record]["diffed"] = True
            with open(runtime_record_path(), "w") as f:
                f.write(json.dumps(records, indent=1))
            current_record = current_record + 1
