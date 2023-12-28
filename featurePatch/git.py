# Helpers for repo/subrepo operations
# Using plumbum for git operations since the standard python libraries
# don't interact with git-subrepo and we need to call this seperately anyways
# for the different subrepo commands see:
# https://github.com/ingydotnet/git-subrepo/blob/master/lib/git-subrepo.d/help-functions.bash
# Unfortunately the documentation is not complete and wrong in places, links to the locations of the bash functions
# in the repo are provided when reading the source proved necessary.
# subrepo expects a bash shell. We make sure to map all paths to POSIX paths in this file to avoid confusions.
import os, inspect
from plumbum import local
from .util import configuration, constants, path_diff
from .log import log

git = local['git']

###
#
# Configuration Constants
#
###

FEATURE_ROOT_PATH = configuration()["feature_git_root"]
FEATURE_REMOTE_URL = configuration()["feature_git_remote"]
FEATURE_ACCESS_TOKEN = configuration()["feature_github_access_token"]
FEATURE_TMP_CHECKOUT_LOCATION = configuration()["feature_git_temp_root"]
FEATURE_TMP_DIRNAME = constants()["subrepo_temporary_directoryname"]
SUBREPO_VERBOSITY = configuration()["subrepo_verbosity"]
CONTAINER_ROOT_PATH = configuration()["container_git_root"]
GITHUB_USERNAME = configuration()["github_username"]
GIT_VERBOSITY = configuration()["git_verbosity"]

run_command_counter = 1

###
#
# Helpers
#
###


def path_join(first_path, second_path):
    """
        We write our own since python cleverness leads to weirdness when emulating POSIX under Windows.
        We only support POSIX style paths for simplicity.
        PRE: Any backslashes in the paths are treated as a critical error.
    :param first_path: First half of the path, can't contain backslashes
    :param second_path: Second half of the path, can't contain backslashes
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


def map_path(path, to_posix=False):
    """
      Maps paths between POSIX and windows compliance. Will check the 'windows' configuration Bit to determine if a
      change is needed.
    :param path: The path to transform.
    :param to_posix: Ignore windows configuration bit and transform windows -> POSIX
    :return: the transformed path
    """
    if to_posix:
        path = path.replace("\\", "/")
        path = path.replace("C:", "\\c\\")
    elif configuration()["windows"]:
        # remap path
        path = path.replace("/", "\\")
        path = path.replace("\\c\\", "C:")
    return path


def chdir(path):
    path = map_path(path)
    os.chdir(path)


def isdir(path):
    path = map_path(path)
    return os.path.isdir(path)


def execute(cmd):
    global run_command_counter
    log.debug(f"Command nr: {run_command_counter}")
    run_command_counter = run_command_counter + 1
    output = cmd()
    # inspect.stack()[1][3] is the name of the calling function
    # https://docs.python.org/3/library/inspect.html#the-interpreter-stack
    log.info(f"{inspect.stack()[1][3]}: \n{cmd} \nOutput: {output}")
    # TODO: Error handling?
    return output


def navigate_to(path):
    log.debug(f"chdir {path}")
    chdir(path)

###
#
# \Helpers
#
###


def authenticated_subrepo_url():
    """
    PRE: Assumes repository is hosted on github and credentials are set in config.
    :return: remote url which already contains username and PW to skip manual entries
    """
    parts = FEATURE_REMOTE_URL.split("github.com")
    return parts[0] + f"{GITHUB_USERNAME}:{FEATURE_ACCESS_TOKEN}" + f"@github.com{parts[1]}"


def branch_name(suffix):
    if suffix is not None:
        suffix = "_" + suffix
    else:
        suffix = ""
    return constants()["migration_branch_base_name"] + suffix


def subrepo_name():
    """
    may also be called <subrepo_dir> in the documentation but referred to the 'name' in discussions.
    :return:
    """
    return path_diff(map_path(FEATURE_ROOT_PATH, True), map_path(CONTAINER_ROOT_PATH, True), "/")


def clean_subrepo():
    """
    remove any erroneous commands. TODO: when else is this necessary?
    :return:
    """
    navigate_to(CONTAINER_ROOT_PATH)
    cmd = git["subrepo", SUBREPO_VERBOSITY, "clean", subrepo_name()]
    execute(cmd)


def add_subrepo():
    """
    Adds any changes within the subrepository in the container and commits them.
    Preserves working directory.
    :return: True if changes were present and were successfully added, False otherwise
    """
    cwd = os.getcwd()
    navigate_to(CONTAINER_ROOT_PATH)
    output = execute(git["status"])
    lines = output.split("\n")
    change_present = False
    for line in lines:
        if "modified:" in line:
            # used 'all' to avoid issues with varying separators in pathnames
            if all([dirname in line for dirname in subrepo_name().split("/")]):
                change_present = True
                log.info("Unstaged changes in subrepo, adding...")
            else:
                log.debug(f"all of {subrepo_name().split('/')} not found in:\n {line}")
        else:
            log.debug(f"modified not found in:\n {line}")
    if change_present:
        # Doesn't matter if it was already added, change present will still be true
        execute(git["add", path_join(subrepo_name(), "*")])
        execute(git["commit", "-m", "changes in subrepository"])
        # TODO: Error handling?
    navigate_to(cwd)
    return change_present


def commit_subrepo(message):
    """
    adds and commits changes to subrepo if there are any
    preserves cwd.
    """
    changes = add_subrepo()
    if changes:
        log.info("Committing staged subrepo changes...")
        cwd = os.getcwd()
        navigate_to(CONTAINER_ROOT_PATH)
        execute(git["subrepo", "commit", "-m", message, subrepo_name()])
        navigate_to(cwd)


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
    navigate_to(CONTAINER_ROOT_PATH)
    # Do a clean before attempting to push
    clean_subrepo()
    # Push the changes to the subrepository and log the generated output
    execute(git["subrepo", SUBREPO_VERBOSITY, "-r", authenticated_subrepo_url(), "push", subrepo_name()])
    navigate_to(cwd)


def create_migration_branch(suffix=None):
    """
    We want to keep the main branch of the subrepo clean so we add the extraction commits to a fresh branch.
    @see: https://github.com/ingydotnet/git-subrepo/blob/110b9eb13f259986fffcf11e8fb187b8cce50921/lib/git-subrepo#L731
    :param suffix: added to the 'migration' name if provided
    """
    # First we make sure that any trailing changes on subrepo master are pushed to remote
    push_subrepo(f"Push before creating {branch_name(suffix)}")
    # create migration branch on remote
    create_remote_subrepo_branch(branch_name(suffix))


def create_remote_subrepo_branch(branchname):
    """
    Checkout master branch of subrepo in temporary location.
    Use generic Git to create, checkout and push new branch to remote.
    Remove local copy of subrepo.
    :param branchname: How to call the new branch
    """
    navigate_to(FEATURE_TMP_CHECKOUT_LOCATION)
    # Idempotence
    if isdir(FEATURE_TMP_DIRNAME):
        execute(local["rm"]["-r", FEATURE_TMP_DIRNAME])
    execute(local["mkdir"][FEATURE_TMP_DIRNAME])
    navigate_to(FEATURE_TMP_DIRNAME)
    # Create url containing username and pw for cloning
    execute(git["clone", GIT_VERBOSITY, authenticated_subrepo_url()])
    output = execute(local["ls"])
    navigate_to(output.strip())
    execute(git["checkout", "-b", branchname])
    execute(git["push", "--set-upstream", "origin", branchname])
    navigate_to(FEATURE_TMP_CHECKOUT_LOCATION)
    execute(local["rm"]["-r", FEATURE_TMP_DIRNAME])


def merge_migration_branch(suffix=None):
    """
    PRE: master branch of subrepository must have already been pulled into the container
    Merges current subrepo migration branch into master (which was previously cloned into the fresh container)
    @see https://github.com/ingydotnet/git-subrepo/blob/110b9eb13f259986fffcf11e8fb187b8cce50921/lib/git-subrepo.d/help-functions.bash#L71
    :return:
    """
    navigate_to(CONTAINER_ROOT_PATH)

    # Check preconditions
    if not isdir(FEATURE_ROOT_PATH):
        log.critical("Subrepository missing from container. Attempted migration branch merge aborted.")
        exit(1)
    with open(path_join(FEATURE_ROOT_PATH, ".gitrepo"), "r") as f:
        lines = f.readlines()
    idx = 0
    while "branch" not in lines[idx]:
        # idx out of range indicates some issue with the .gitrepo file, there should always be a line listing the branch
        idx = idx + 1
    if "master" not in lines[idx]:
        log.critical("Master branch is not checked out in subrepository. Attempted migration branch merge aborted.")
        exit(1)

    cmd = git["subrepo", "clone", f"--branch={branch_name(suffix)}", "--method=merge", FEATURE_REMOTE_URL, FEATURE_ROOT_PATH]
    execute(cmd)


def pull_subrepo():
    # Navigate to the root of the container and pull the changes of the subrepository
    # Fast forward is attempted and command aborted if this fails.
    navigate_to(CONTAINER_ROOT_PATH)
    # Push the changes to the subrepository and log the generated output
    cmd = git["subrepo", SUBREPO_VERBOSITY, "pull", FEATURE_ROOT_PATH]
    execute(cmd)
    # TODO: Error handling?


def pull_container():
    # TODO: add the option to be much more specific with the new version you want, tags etc...
    log.info("Pulling container...")
    navigate_to(CONTAINER_ROOT_PATH)
    cmd = git["pull"]
    execute(cmd)


def upgrade_container_to(tag, main_branch_name="main"):
    log.info(f"Updating container to tag: {tag}")
    # checkout main
    navigate_to(CONTAINER_ROOT_PATH)
    execute(git["checkout", main_branch_name])


def embed_subpreo(branchname):
    """
    Clone different branch of subrepository into container.
    PRE: Clean working tree.
    :param branchname: which branch to switch to
    :return:
    """
    navigate_to(CONTAINER_ROOT_PATH)
    execute(git["subrepo", SUBREPO_VERBOSITY, "clone", "-b", branchname, authenticated_subrepo_url()])


def initialize_subrepo():
    navigate_to(FEATURE_ROOT_PATH)
    execute(git["subrepo", SUBREPO_VERBOSITY, "init"])
