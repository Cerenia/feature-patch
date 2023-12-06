# Helpers for repo/subrepo operations
# Using plumbum for git operations since the standard python libraries
# don't interact with git-subrepo and we need to call this seperately anyways
# for the different subrepo commands see:
# https://github.com/ingydotnet/git-subrepo/blob/master/lib/git-subrepo.d/help-functions.bash
import os
from plumbum import local
from .util import configuration, logger

git = local['git']


def run_command(cmd):
    # Also logs it with level info
    logger().info(cmd)
    output = cmd()
    logger().info(output)


def navigate_to_container_root():
    os.chdir(configuration()["container_git_root"])

def push_subrepo():
    # Navigate to the root of the container and push the changes of the subrepository
    navigate_to_container_root()
    # Push the changes to the subrepository and log the generated output
    cmd = git["subrepo", "-dv", "push", configuration()["feature_git_root"]]
    run_command(cmd)
    # TODO: Error handling?


def pull_subrepo():
    # Navigate to the root of the container and pull the changes of the subrepository
    # Fast forward is attempted and command aborted if this fails.
    navigate_to_container_root()
    # Push the changes to the subrepository and log the generated output
    cmd = git["subrepo", "-dv", "pull", configuration()["feature_git_root"]]
    run_command(cmd)
    # TODO: Error handling?


def pull_container():
    # TODO: add the option to be much more specific with the new version you want, tags etc...
    logger().info("Pulling container...")
    navigate_to_container_root()
    cmd = git["pull"]
    run_command(cmd)


def embed_subpreo():
    pass


def initialize_subrepo():
    pass
