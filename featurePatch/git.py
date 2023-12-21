# Helpers for repo/subrepo operations
# Using plumbum for git operations since the standard python libraries
# don't interact with git-subrepo and we need to call this seperately anyways
# for the different subrepo commands see:
# https://github.com/ingydotnet/git-subrepo/blob/master/lib/git-subrepo.d/help-functions.bash
# Unfortunately the documentation is not complete and wrong in places, links to the locations of the bash functions
# in the repo are provided when reading the source proved necessary.
import os
from plumbum import local
from .util import configuration, constants, path_diff
from .log import log

git = local['git']

###
#
# Configuration Constants
#
###

FEATURE_GIT_ROOT = configuration()["feature_git_root"]
FEATURE_REMOTE_URL = configuration()["feature_git_remote"]
SUBREPO_VERBOSITY = configuration()["subrepo_verbosity"]


def run_command(cmd):
    # Also logs it with level info
    log.info(cmd)
    output = cmd()
    log.info(output)
    # TODO: Error handling?


def navigate_to(path):
    log.info(f"chdir {path}")
    os.chdir(path)


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
    return path_diff(FEATURE_GIT_ROOT, configuration()["container_git_root"])


def clean_subrepo():
    """
    remove any erroneous commands. TODO: when else is this necessary?
    :return:
    """
    navigate_to(configuration()["container_git_root"])
    cmd = git["subrepo", SUBREPO_VERBOSITY, "clean", subrepo_name()]
    run_command(cmd)


def create_migration_branch(suffix=None):
    """
    We want to keep the main branch of the subrepo clean so we add the extraction commits to a fresh branch.
    @see: https://github.com/ingydotnet/git-subrepo/blob/110b9eb13f259986fffcf11e8fb187b8cce50921/lib/git-subrepo#L731
    :param suffix: added to the 'migration' name if provided
    """
    navigate_to(configuration()["container_git_root"])
    #cmd = git["subrepo", SUBREPO_VERBOSITY, "branch", branch_name(suffix), "update_wanted=true"]
    #cmd = git["subrepo", SUBREPO_VERBOSITY, "branch", subrepo_name()]
    #cmd = git["subrepo", "pull", subrepo_name(), "-b", branch_name(suffix), "--force"]
    # first create a new remote branch
    cmd = git["subrepo", "clone", "--force", "-b", branch_name(suffix), FEATURE_REMOTE_URL]
    run_command(cmd)


def merge_migration_branch(suffix=None):
    """
    PRE: master branch of subrepository must have already been pulled into the container
    Merges current subrepo migration branch into master (which was previously cloned into the fresh container)
    @see https://github.com/ingydotnet/git-subrepo/blob/110b9eb13f259986fffcf11e8fb187b8cce50921/lib/git-subrepo.d/help-functions.bash#L71
    :return:
    """
    navigate_to(configuration()["container_git_root"])

    # Check preconditions
    if not os.path.isdir(FEATURE_GIT_ROOT):
        log.critical("Subrepository missing from container. Attempted migration branch merge aborted.")
        exit(1)
    with open(os.path.join(FEATURE_GIT_ROOT), ".gitrepo") as f:
        lines = f.readlines()
    idx = 0
    while "branch" not in lines[idx]:
        # idx out of range indicates some issue with the .gitrepo file, there should always be a line listing the branch
        idx = idx + 1
    if "master" not in lines[idx]:
        log.critical("Master branch is not checked out in subrepository. Attempted migration branch merge aborted.")
        exit(1)

    cmd = git["subrepo", "clone", f"--branch={branch_name(suffix)}", "--method=merge", FEATURE_REMOTE_URL, FEATURE_GIT_ROOT]
    run_command(cmd)


def push_subrepo():
    # Navigate to the root of the container and push the changes of the subrepository
    navigate_to(configuration()["container_git_root"])
    # Push the changes to the subrepository and log the generated output
    cmd = git["subrepo", SUBREPO_VERBOSITY, "push", FEATURE_GIT_ROOT]
    run_command(cmd)


def pull_subrepo():
    # Navigate to the root of the container and pull the changes of the subrepository
    # Fast forward is attempted and command aborted if this fails.
    navigate_to(configuration()["container_git_root"])
    # Push the changes to the subrepository and log the generated output
    cmd = git["subrepo", SUBREPO_VERBOSITY, "pull", FEATURE_GIT_ROOT]
    run_command(cmd)
    # TODO: Error handling?


def pull_container():
    # TODO: add the option to be much more specific with the new version you want, tags etc...
    log.info("Pulling container...")
    navigate_to(configuration()["container_git_root"])
    cmd = git["pull"]
    run_command(cmd)


def embed_subpreo():
    # This will clear/create the embedded feature directory
    # and freshly clone the subrepository into this space.
    # Clear and recreate subrepo root
    if os.path.isdir(FEATURE_GIT_ROOT):
        run_command(local["rm"]["-r", FEATURE_GIT_ROOT])
    run_command(local["mkdir"][FEATURE_GIT_ROOT])
    navigate_to(FEATURE_GIT_ROOT)
    # fresh clone
    run_command(git["subrepo", SUBREPO_VERBOSITY, "clone", FEATURE_REMOTE_URL])


def initialize_subrepo():
    navigate_to(FEATURE_GIT_ROOT)
    run_command(git["subrepo", SUBREPO_VERBOSITY, "init"])
