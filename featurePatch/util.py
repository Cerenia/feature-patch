import yaml
import os
from .fp_log import log


config: dict = None
const: dict = None


def init_cygwin():
    # expand path if using cygwin
    os.environ["PATH"] = (
        # TODO: (for plumbum) extract to configs once structure is clearer. or just don't use plumbum :(
        os.path.expanduser("/c/Program Files/Git/usr/bin/") + ";" + os.environ["PATH"]
    )


# can't pass a global as a param thus need to duplicate some code with the following 2 functions

def configuration():
    global config
    if config is None:
        log.info("Loading Configs...")
        with open("./conf/config.yml", 'r') as f:
            config = yaml.safe_load(f)
    return config


def constants():
    global const
    if const is None:
        log.info("Loading Constants...")
        with open("./conf/config.yml", 'r') as f:
            const = yaml.safe_load(f)
    return constants




def subrepo_path():
    """
    :return: absolute root path of feature repository as set in config
    """
    conf = configuration()
    return conf['feature_git_root']


def contact_points_path():
    """
    :return: absolute directory in which all contact point files should be/ were saved after extracting feature.
    """
    return os.path.join(subrepo_path(), "contactPoints")


def add_to_config_template():
    """
     Run whenever you add a configuration variable, expects ..\conf\config.yml will modify ..\conf\config_template.yml additively
     Deleting flags should be done manually (for now)
    :return:
    """
    log.info("Editing configuration template...")
    conf = configuration()
    with open("./conf/config_template.yml", "r") as f:
        conf_template = yaml.safe_load(f)
    for key in conf:
        if key not in conf_template.keys():
            log.info(f"Adding confguration item '{key}'")
            conf_template[key] = ""
    with open("./conf/config_template.yml", "w") as f:
        yaml.dump(conf_template, f)


def runtime_record_path():
    return os.path.join(configuration()["working_dir"], "runtime_record.txt")


def error_record_path():
    return os.path.join(configuration()["working_dir"], "errors.txt")


def path_diff(long_path: str, short_path: str, tail=True):
    """
    Returns the difference in both paths, and removes a trailing os path separator if necessary.
    By default, the method first attempts to find the diff at the tail of long_path.
    If this fails it attempts to find a diff at the start of long_path.

    Example tail:
        long_path = C:Users/usr/myGreatPath/subdir/myfile.txt
        short_path = C:Users/usr/myGreatPath
        result = subdir/myfile.txt

    Example front:
        long_path = myGreatPath/subdir/myfile.txt
        short_path = myfile.txt
        result = myGreatPath/subdir

    Example mid:
        long_path = C:Users/usr/myGreatPath/subdir/myfile.txt
        short_path = usr
        result = C:Users/

    you can change the order of search by passing tail=False

    :param long_path: The first path to diff against. long_path must be longer than short_path
    :param short_path: The second path to diff against (may also be a filename)
    :param tail: Defines preferred diff location if the split happens to be mid path.
    :return: A path sequence that can directly be used with os.path.join.
    """

    assert len(long_path) > len(short_path)

    parts = long_path.split(short_path)
    # empty Strings are falsy https://peps.python.org/pep-0008/#programming-recommendations
    useful_parts = [element for element in filter(lambda x: x, parts)]
    if tail:
        diff = useful_parts[-1]
    else:
        diff = useful_parts[0]
    if diff[0] == os.sep:
        diff = diff[1:]
    if diff[-1] == os.sep:
        diff = diff[0:-2]
    return diff
