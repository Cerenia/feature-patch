"""
TODO:
- Document expected file hierarchy
Code (contains same folder structure and any file with marker)
Layout
Drawables
Strings


Capabilities:
- create folders inside subrepo (clear if they exist) which holds all contact file points for later diff
- push these files to subrepo
"""

from plumbum import local
from ..util import load_configs
import os


def prepFolders(windows=False):
    """
    Clears/Creates target folders in the subrepo to later be filled with all files of contact
    expects to be run in bash shell (TODO: add a Windows flag + any changed commands?)
    :return:
    """
    conf = load_configs()
    subrepo_path = conf['android_feature_root']
    cd = local('cd')
    layout_path = os.path.join(subrepo_path, "layout")
    string_path = os.path.join(subrepo_path, "string")
    drawable_path = os.path.join(subrepo_path, "drawable")
    code_path = os.path.join(subrepo_path, "code")
    if not windows:
        mkdir = local('mkdir')
        rm = local('rm')
        cd[subrepo_path]()
        rm["-v", "-f", layout_path]()
        rm["-v", "-f", string_path]()
        rm["-v", "-f", drawable_path]()
        rm["-v", "-f", code_path]()
        TODO: CONTINUE HERE
    pass


def extractFiles():
    """
    Walk through expected file hierarchy and find all files that contain the string marker in configs
    :return:
    """
    pass
