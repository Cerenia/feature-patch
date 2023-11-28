import yaml
import os
import logging


config: dict


def configuration():
    global config
    if config is None:
        print("Loading configs...")
        with open("./conf/config.yml", 'r') as f:
            config = yaml.safe_load(f)
    return config


log: logging.Logger


def initialize_logger():
    """
    Initializes root logger and logger formatting.
    :return: a handle to the root logger.
    """
    global log
    log = logging.getLogger("feature-patch")
    # TODO: special formatting?
    return log


def get_logger(name=None):
    """
    Any logger fetches with get_logger
    down the line will be a descendant if initialize_logger was
    previously called and a name is provided. Otherwise, the root logger is returned.
    PRE: initialize_logger was called
    :param name: subname of the new logger. Root logger returned if none.
    :return:
    """
    assert log is not None, "Please call ..util.initialize_logger."
    if name is None:
        return log
    else:
        return logging.getLogger(f"feature-patch.{name}")
    pass


def subrepo_path():
    """
    :return: absolute root path of feature repository as set in config
    """
    conf = configuration()
    return conf['android_feature_root']


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
    print("Editing configuration template...")
    conf = configuration()
    with open("./conf/config_template.yml", "r") as f:
        conf_template = yaml.safe_load(f)
    for key in conf:
        if key not in conf_template.keys():
            print(f"Adding confguration item '{key}'")
            conf_template[key] = ""
    with open("./conf/config_template.yml", "w") as f:
        yaml.dump(conf_template, f)


def runtime_log_path():
    return os.path.join(configuration()["working_dir"], "runtime_log.txt")


def error_log_path():
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
    print(parts)
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
