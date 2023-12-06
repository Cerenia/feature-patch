# Helpers for repo/subrepo operations
# Using plumbum for git operations since the standard python libraries
# don't interact with git-subrepo and we need to call this seperately anyways
# for the different subrepo commands see:
# https://github.com/ingydotnet/git-subrepo/blob/master/lib/git-subrepo.d/help-functions.bash
import os
from plumbum import local
from .util import configuration, logger

git = local['git']
# TODO: export to configs
SUBREPO_VERBOSITY = "-dv"


def run_command(cmd):
    # Also logs it with level info
    logger().info(cmd)
    output = cmd()
    logger().info(output)


def navigate_to(path):
    logger().info(f"chdir {path}")
    os.chdir(path)

def push_subrepo():
    # Navigate to the root of the container and push the changes of the subrepository
    navigate_to(configuration()["container_git_root"])
    # Push the changes to the subrepository and log the generated output
    cmd = git["subrepo", SUBREPO_VERBOSITY, "push", configuration()["feature_git_root"]]
    run_command(cmd)
    # TODO: Error handling?


def pull_subrepo():
    # Navigate to the root of the container and pull the changes of the subrepository
    # Fast forward is attempted and command aborted if this fails.
    navigate_to(configuration()["container_git_root"])
    # Push the changes to the subrepository and log the generated output
    cmd = git["subrepo", SUBREPO_VERBOSITY, "pull", configuration()["feature_git_root"]]
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
    run_command(git["subrepo", SUBREPO_VERBOSITY, "clone", configuration()["feature_git_remote"]])


def initialize_subrepo():
    navigate_to(configuration()["feature_git_root"])
    run_command(git["subrepo", SUBREPO_VERBOSITY, "init"])
