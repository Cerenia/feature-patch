"""
Helpers for repo/subrepo operations related to versioning
Using plumbum for git operations since the standard python libraries
don't interact with git-subrepo and we need to call this seperately anyways
for the different subrepo commands see:
https://github.com/ingydotnet/git-subrepo/blob/master/lib/git-subrepo.d/help-functions.bash
Unfortunately the documentation is not complete and wrong in places, links to the locations of the bash functions
in the repo are provided when reading the source proved necessary.
subrepo expects a bash shell. We make sure to map all paths to POSIX paths in this file to avoid barfs.
"""
import os
import re
from plumbum import local
from .util import configuration, constants, path_diff, execute, contact_points_folder_path, CONTACT_POINTS
from .android.util import map_contact_points_path_to_container
from .log import log

git = local['git']

###
#
# Configuration Constants
#
###

FEATUFEATURE_ROOT_PATH = None
FEATURE_REMOTE_UR = None
FEATURE_ACCESS_TOKEN = None
FEATURE_TMP_CHECKOUT_LOCATION = None
FEATURE_TMP_DIRNAME = None
SUBREPO_VERBOSITY = None
CONTAINER_ROOT_PATH = None
GITHUB_USERNAME = None
GIT_VERBOSITY = None


def initialize_git_constants():
    global FEATURE_ROOT_PATH
    global FEATURE_REMOTE_URL
    global FEATURE_ACCESS_TOKEN
    global FEATURE_TMP_CHECKOUT_LOCATION
    global FEATURE_TMP_DIRNAME
    global SUBREPO_VERBOSITY
    global CONTAINER_ROOT_PATH
    global GITHUB_USERNAME
    global GIT_VERBOSITY
    FEATURE_ROOT_PATH = configuration()["feature_git_root"]
    FEATURE_REMOTE_URL = configuration()["feature_git_remote"]
    FEATURE_ACCESS_TOKEN = configuration()["feature_github_access_token"]
    FEATURE_TMP_CHECKOUT_LOCATION = configuration()["feature_git_temp_root"]
    FEATURE_TMP_DIRNAME = constants()["subrepo_temporary_directoryname"]
    SUBREPO_VERBOSITY = configuration()["subrepo_verbosity"]
    CONTAINER_ROOT_PATH = configuration()["container_git_root"]
    GITHUB_USERNAME = configuration()["github_username"]
    GIT_VERBOSITY = configuration()["git_verbosity"]


###
#
# Helpers:
# because git subrepo expects to run in a bash shell we need to make sure the paths are POSIX compliant
#
###


def _path_join(first_path: str, second_path: str):
    """
        We write our own since python cleverness leads to weirdness when emulating POSIX under Windows.
        We only support POSIX style paths for simplicity.
        PRE: Any backslashes in the paths are treated as a critical error.
    :param first_path: First half of the path
    :param second_path: Second half of the path
    :return: a string representing the joined path
    """
    error_msg = "{path} contained unsupported '\\' character"
    if "\\" in first_path:
        log.critical(error_msg.format(path=first_path))
        exit(1)
    if "\\" in second_path:
        log.critical(error_msg.format(path=second_path))
        exit(1)
    if "/" == first_path[-1]:
        trailing_slash = True
    else:
        trailing_slash = False
    if "/" == second_path[0]:
        starting_slash = True
    else:
        starting_slash = False
    if not trailing_slash and not starting_slash:
        return first_path + "/" + second_path
    if not trailing_slash and starting_slash or trailing_slash and not starting_slash:
        return first_path + second_path
    else:  # both slashes present
        return first_path[0:-1] + second_path


def _map_path(path: str, to_posix=False):
    """
      Maps paths between POSIX and windows compliance. Will check the 'windows' configuration Bit to determine if a
      change is needed.
    :param path: The path to transform.
    :param to_posix: Ignore windows configuration bit and transform windows -> POSIX
    :return: the transformed path
    """
    if to_posix:
        path = path.replace("\\", "/")
        path = path.replace("C:", "/c")
    elif configuration()["windows"]:
        # remap path
        path = path.replace("/", "\\")
        path = path.replace("/c", "C:")
    return path


def _chdir(path: str):
    """
    Map path and change directory with python native method.
    """
    path = _map_path(path)
    os.chdir(path)


def _isdir(path: str):
    """
    Map path and check directory with python native method.
    """
    path = _map_path(path)
    return os.path.isdir(path)


def _navigate_to(path: str):
    """
    Change directory and debug-log the change.
    Call this preferentially.
    """
    log.debug(f"chdir {path}")
    _chdir(path)

###
#
# \Helpers
#
###


def _authenticated_subrepo_url():
    """
    PRE: Assumes repository is hosted on github and credentials are set in config.
    :return: remote url which already contains username and token to skip manual entries
    """
    parts = FEATURE_REMOTE_URL.split("github.com")
    return parts[0] + f"{GITHUB_USERNAME}:{FEATURE_ACCESS_TOKEN}" + f"@github.com{parts[1]}"


def _migration_branch_name(suffix: str):
    """
    Defines format of migration branch name. Uses 'migration_branch_base_name' constant.
    :param suffix:
    :return:
    """
    if suffix is not None:
        suffix = "_" + suffix
    else:
        suffix = ""
    return constants()["migration_branch_base_name"] + suffix


def unmodified_file_path(filepath: str, windows=False):
    """
    Defines the filepath for the checked out 'unmodified' previous version of the file in the 'contact_points' folder.
    Assumes Posix by default and will map filepath accordingly.
    :param filepath: Expects path to current, modified file in the 'contact_points' folder.
    :param windows: Set True if the windows compliance is needed
    :return: The path the unmodified file should be checked out to
    """
    separator = "\\" if windows else "/"
    parts = filepath.split(separator)
    filename = parts[-1]
    # only include any path parts till 'contact_points'
    i = 0
    while i < len(parts) and parts[i] != CONTACT_POINTS:
        i = i + 1
    if i == len(parts):
        # path was already relative
        relpath = os.path.join(separator.join(filepath.split(separator)[:-1]), constants()["unmodified_file_base_name"] + "_" + filename)
    else:
        relpath = os.path.join(separator.join(filepath.split(separator)[i+1:-1]), constants()["unmodified_file_base_name"] + "_" + filename)
    abspath = _map_path(os.path.join(contact_points_folder_path(), relpath), not windows)
    return abspath


def checkout_unmodified_file(filepath: str):
    """
    Checks out the previous, unmodified version of a file in the 'contact_points' folder.
    :param filepath: Which file to attempt to check out.
    """
    _navigate_to(CONTAINER_ROOT_PATH)
    relative_unmodified_path = path_diff(map_contact_points_path_to_container(filepath),
                                         configuration()["container_git_root"])
    unmodified_file_content = git["show", f"{constants()['unmodified_branch']}:{_map_path(relative_unmodified_path, True)}"]()
    with open(unmodified_file_path(filepath, configuration()["windows"]), "w", encoding="utf-8") as f:
        f.write(unmodified_file_content)


def _subrepo_name():
    """
    may also be called <subrepo_dir> in the git subrepo documentation but referred to the 'name' in discussions.
    :return: The subrepo name aka the relative path to the subrepo directory (POSIX)
    """
    return path_diff(_map_path(FEATURE_ROOT_PATH, True), _map_path(CONTAINER_ROOT_PATH, True), "/")


def clean_subrepo():
    """
    remove any erroneous commands.
    :return:
    """
    _navigate_to(CONTAINER_ROOT_PATH)
    cmd = git["subrepo", SUBREPO_VERBOSITY, "clean", _subrepo_name()]
    execute(cmd)


def add_subrepo():
    """
    Adds any changes within the subrepository in the container and commits them.
    Preserves working directory.
    :return: True if changes were present and were successfully added, False otherwise
    """
    cwd = os.getcwd()
    _navigate_to(CONTAINER_ROOT_PATH)
    output = execute(git["status"])
    # Search for subrepo directory in output
    pattern = fr"{_subrepo_name()}"
    has_match = re.search(pattern, output)
    if has_match is not None:
        execute(git["add", _path_join(_subrepo_name(), "*")])
        execute(git["commit", "-m", "changes in subrepository"])
        _navigate_to(cwd)
        return True
    _navigate_to(cwd)
    return False


def commit_subrepo(message: str):
    """
    adds and commits changes to subrepo if there are any
    """
    changes = add_subrepo()
    if changes:
        log.info("Committing staged subrepo changes...")
        cwd = os.getcwd()
        _navigate_to(CONTAINER_ROOT_PATH)
        execute(git["subrepo", "commit", "-m", message, _subrepo_name()])
        _navigate_to(cwd)


def _commit_container(message: str):
    """
    Add and commit any changes of the container repository.
    :return:
    """
    cwd = os.getcwd()
    _navigate_to(CONTAINER_ROOT_PATH)
    execute(git["add", "."])
    execute(git["commit", "-m", message])
    _navigate_to(cwd)


def push_subrepo(message: str):
    """
    push to current subrepository branch. Will add and commit with provided message.
    preserves cwd.
    :param: message: If working dir is clean, you may pass None for the message.
    """
    cwd = os.getcwd()
    if message is not None:
        commit_subrepo(message)
    # Navigate to the root of the container and push the changes of the subrepository
    _navigate_to(CONTAINER_ROOT_PATH)
    # Do a clean before attempting to push
    clean_subrepo()
    # Push the changes to the subrepository and log the generated output
    execute(git["subrepo", SUBREPO_VERBOSITY, "-r", _authenticated_subrepo_url(), "push", _subrepo_name()])
    _navigate_to(cwd)


def create_subrepo_migration_branch(suffix: str=None):
    """
    We want to keep the main branch of the subrepo clean so we add the extraction commits to a fresh branch.
    @see: https://github.com/ingydotnet/git-subrepo/blob/110b9eb13f259986fffcf11e8fb187b8cce50921/lib/git-subrepo#L731
    :param suffix: added to the 'migration' name if provided
    """
    # First we make sure that any trailing changes on subrepo master are pushed to remote
    push_subrepo(f"Push before creating {_migration_branch_name(suffix)}")
    # create migration branch on remote
    _create_remote_subrepo_branch(_migration_branch_name(suffix))


def _create_remote_subrepo_branch(branchname: str):
    """
    Checkout master branch of subrepo in temporary location.
    Use generic Git to create, checkout and push new branch to remote.
    Remove local copy of subrepo.
    :param branchname: How to call the new branch
    """
    _navigate_to(FEATURE_TMP_CHECKOUT_LOCATION)
    # Idempotence
    if _isdir(FEATURE_TMP_DIRNAME):
        execute(local["rm"]["-r", FEATURE_TMP_DIRNAME])
    execute(local["mkdir"][FEATURE_TMP_DIRNAME])
    _navigate_to(FEATURE_TMP_DIRNAME)
    # Create url containing username and pw for cloning
    execute(git["clone", GIT_VERBOSITY, _authenticated_subrepo_url()])
    output = execute(local["ls"])
    _navigate_to(output.strip())
    execute(git["checkout", "-b", branchname])
    execute(git["push", GIT_VERBOSITY, "--repo", _authenticated_subrepo_url(), "--set-upstream", "origin", branchname])
    _navigate_to(FEATURE_TMP_CHECKOUT_LOCATION)
    execute(local["rm"]["-r", FEATURE_TMP_DIRNAME])


def delete_local_migration_branch(suffix: str = None):
    """
    Remove local migration branch
    :param suffix: added to the 'migration' name if provided
    """
    _navigate_to(FEATURE_TMP_CHECKOUT_LOCATION)
    execute(git["branch", GIT_VERBOSITY, "-D", _migration_branch_name(suffix)])


def merge_migration_branch(suffix: str = None):
    """
    PRE: master branch of subrepository must have already been pulled into the container
    Merges current subrepo migration branch into master (which was previously cloned into the fresh container)
    @see https://github.com/ingydotnet/git-subrepo/blob/110b9eb13f259986fffcf11e8fb187b8cce50921/lib/git-subrepo.d/help-functions.bash#L71
    :param suffix: Suffix to migration branch name
    :return:
    """
    _navigate_to(CONTAINER_ROOT_PATH)

    # Check preconditions
    if not _isdir(FEATURE_ROOT_PATH):
        log.critical("Subrepository missing from container. Attempted migration branch merge aborted.")
        exit(1)
    with open(os.path.join(FEATURE_ROOT_PATH, ".gitrepo"), "r") as f:
        lines = f.readlines()
    idx = 0
    while "branch" not in lines[idx]:
        # idx out of range indicates some issue with the .gitrepo file, there should always be a line listing the branch
        idx = idx + 1
    if "master" not in lines[idx]:
        log.critical("Master branch is not checked out in subrepository. Attempted migration branch merge aborted.")
        exit(1)

    cmd = git["subrepo", "clone", f"--branch={_migration_branch_name(suffix)}", "--method=merge", FEATURE_REMOTE_URL, FEATURE_ROOT_PATH]
    execute(cmd)


def upgrade_container_to(tag: str, main_branch_name="main"):
    """
        Fetches all tags and creates a branch for that tag. Merges the current main into the 'unmodified_branch'.
         Merges main up to this tag and finally checks out the newly created branch.
    :param tag: Which tag to upgrade to.
    :param main_branch_name: Name of the main branch.
    """
    log.info(f"Updating container to tag: {tag}")
    # checkout main
    _navigate_to(CONTAINER_ROOT_PATH)
    execute(git["checkout", main_branch_name])
    execute(git["fetch", "--all", "--tags"])
    # Create new branch for this version
    execute(git["checkout", f"tags/{tag}", "-b", tag])
    # Create 'unmodified_branch' &
    # Merge current main into 'unmodified_branch'
    execute(git["checkout", "-b", constants()["unmodified_branch"]])
    execute(git["merge", main_branch_name])
    # Merge into main branch to note latest sync.
    execute(git["checkout", main_branch_name])
    execute(git["merge", tag])
    execute(git["checkout", tag])


def checkout_subrepo_migration_branch(tag: str):
    """
    Checks out the migration branch for the specified tag.
    :param tag: The tag for which to checkout the migration branch.
    """
    checkout_subrepo(_migration_branch_name(tag))


def checkout_subrepo(subrepo_branch: str):
    """
    Clones a different branch of the subrepo.
    :param subrepo_branch: which branch to switch to
    :return:
    """
    _navigate_to(CONTAINER_ROOT_PATH)
    # Push first to not destroy anything.
    push_subrepo(f"Push before cloning {subrepo_branch}...")
    execute(local["rm"]["-r", _subrepo_name()], retcodes=(0, 1))
    execute(local["mkdir"][_subrepo_name()])
    _commit_container(f"Commit before cloning branch {subrepo_branch} of subrepository.")
    execute(git["subrepo", SUBREPO_VERBOSITY, "clone", _authenticated_subrepo_url(), _subrepo_name(), "-b", subrepo_branch, "--force"])


def initialize_subrepo():
    """
    Initializes a fresh subrepository at 'FEATURE_ROOT_PATH' if this has not yet happened.
    """
    _navigate_to(FEATURE_ROOT_PATH)
    execute(git["subrepo", SUBREPO_VERBOSITY, "init"])
