# Helpers for repo/subrepo operations
# Using plumbum for git operations since the standard python libraries
# don't interact with git-subrepo and we need to call this seperately anyways
# for the different subrepo commands see:
# https://github.com/ingydotnet/git-subrepo/blob/master/lib/git-subrepo.d/help-functions.bash
# Unfortunately the documentation is not complete and wrong in places, links to the locations of the bash functions
# in the repo are provided when reading the source proved necessary.
import os
from plumbum import local
from .util import configuration, logger, constants

git = local['git']


def run_command(cmd):
    # Also logs it with level info
    logger().info(cmd)
    output = cmd()
    logger().info(output)
    # TODO: Error handling?


def navigate_to(path):
    logger().info(f"chdir {path}")
    os.chdir(path)


def branch_name(suffix):
    if suffix is not None:
        suffix = "_" + suffix
    else:
        suffix = ""
    return constants()["migration_branch_base_name"] + suffix


def create_migration_branch(suffix=None):
    """
    We want to keep the main branch of the subrepo clean so we add the extraction commits to a fresh branch.
    @see: https://github.com/ingydotnet/git-subrepo/blob/110b9eb13f259986fffcf11e8fb187b8cce50921/lib/git-subrepo#L731
    :param suffix: added to the 'migration' name if provided
    """
    navigate_to(configuration()["container_git_root"])
    cmd = git["subrepo", configuration()["subrepo_verbosity"], "branch", branch_name(suffix)]
    run_command(cmd)
    pass


def merge_migration_branch(suffix=None):
    """
    PRE: master branch of subrepository must have already been pulled into the container
    Merges current subrepo migration branch into master (which was previously cloned into the fresh container)
    @see https://github.com/ingydotnet/git-subrepo/blob/110b9eb13f259986fffcf11e8fb187b8cce50921/lib/git-subrepo.d/help-functions.bash#L71
    :return:
    """
    navigate_to(configuration()["container_git_root"])

    # Check preconditions
    if not os.path.isdir(configuration()["feature_git_root"]):
        logger().critical("Subrepository missing from container. Attempted migration branch merge aborted.")
        exit(1)
    with open(os.path.join(configuration()["feature_git_root"]), ".gitrepo") as f:
        lines = f.readlines()
    idx = 0
    while "branch" not in lines[idx]:
        # idx out of range indicates some issue with the .gitrepo file, there should always be a line listing the branch
        idx = idx + 1
    if "master" not in lines[idx]:
        logger().critical("Master branch is not checked out in subrepository. Attempted migration branch merge aborted.")
        exit(1)

    cmd = git["subrepo", "clone", f"--branch={branch_name(suffix)}", "--method=merge", configuration()["feature_git_remote"], configuration()["feature_git_root"]]
    run_command(cmd)


def push_subrepo():
    # Navigate to the root of the container and push the changes of the subrepository
    navigate_to(configuration()["container_git_root"])
    # Push the changes to the subrepository and log the generated output
    cmd = git["subrepo", configuration()["subrepo_verbosity"], "push", configuration()["feature_git_root"]]
    run_command(cmd)


def pull_subrepo():
    # Navigate to the root of the container and pull the changes of the subrepository
    # Fast forward is attempted and command aborted if this fails.
    navigate_to(configuration()["container_git_root"])
    # Push the changes to the subrepository and log the generated output
    cmd = git["subrepo", configuration()["subrepo_verbosity"], "pull", configuration()["feature_git_root"]]
    run_command(cmd)
    # TODO: Error handling?


def pull_container():
    # TODO: add the option to be much more specific with the new version you want, tags etc...
    logger().info("Pulling container...")
    navigate_to(configuration()["container_git_root"])
    cmd = git["pull"]
    run_command(cmd)


def embed_subpreo():
    # This will clear/create the embedded feature directory
    # and freshly clone the subrepository into this space.
    # Clear and recreate subrepo root
    feature_root = configuration()["feature_git_root"]
    if os.path.isdir(feature_root):
        run_command(local["rm"]["-r", feature_root])
    run_command(local["mkdir"][feature_root])
    navigate_to(feature_root)
    # fresh clone
    run_command(git["subrepo", configuration()["subrepo_verbosity"], "clone", configuration()["feature_git_remote"]])


def initialize_subrepo():
    navigate_to(configuration()["feature_git_root"])
    run_command(git["subrepo", configuration()["subrepo_verbosity"], "init"])
