import yaml
import os
from .log import log

config: dict = None
const: dict = None
conf_path = None


def init_cygwin():
    # expand path if using cygwin
    os.environ["PATH"] = (
        # TODO: (for plumbum) extract to configs once structure is clearer. or just don't use plumbum :(
            os.path.expanduser("/c/Program Files/Git/usr/bin/") + ";" + os.environ["PATH"]
    )


def set_conf_path(path):
    global conf_path
    conf_path = path


def find_conf_path(manual_path=None):
    if conf_path is None:
        if os.path.isdir("./conf"):
            return os.path.abspath(os.path.join(".", "conf"))
        else:
            log.error(
                "Expected configuration folder was not found in working directory, please provide the path manually")
            manual_path = input()
            log.error(
                f"You have provided: {manual_path}\nThis will persist through this process instance. You may want to call 'set_conf_path' in the future.")
            return manual_path
    else:
        return conf_path


# can't pass a global as a param thus need to duplicate some code with the following 2 functions

def configuration():
    """
    Assumes to find config.yml at <python_root>/conf/config.yml
    :return:
    """
    global config
    if config is None:
        log.info("Loading Configs...")
        if conf_path is None:
            log.info("Attempting to find configuration folder...")
            path = find_conf_path()
            try:
                with open(os.path.join(path, "config.yml"), 'r') as f:
                    config = yaml.safe_load(f)
            except FileNotFoundError as e:
                log.critical("Could not find configuration.")
                log.critical(str(e))
                exit(1)
            set_conf_path(path)
        else:
            with open(os.path.join(conf_path, "config.yml")) as f:
                config = yaml.safe_load(f)
    return config


def constants():
    global const
    if const is None:
        log.info("Loading Constants...")
        if conf_path is None:
            # call config to attempt finding and setting conf path automagically
            configuration()
        assert conf_path is not None, "Whuut, conf path is None but program did not terminate"
        with open(os.path.join(conf_path, "const.yml"), 'r') as f:
            const = yaml.safe_load(f)
    return const


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
     PRE: Expects to run from repository root
    :return:
    """
    log.info("Editing configuration template...")
    with open("./conf/config_template.yml", "r") as f:
        conf_template = yaml.safe_load(f)
    with open("./conf/config.yml", "r") as f:
        configuration_lines = f.readlines()
    template_lines = []
    for line in configuration_lines:
        if "#" in line:
            template_lines.append(line)
        else:
            element = yaml.safe_load(line)
            key = next(iter(element.keys()))
            if key not in conf_template.keys():
                log.info(f"Adding configuration item '{key}'")
            element[key] = "TODO"
            template_lines.append(yaml.safe_dump(element))
    with open("./conf/config_template.yml", "w") as f:
        f.writelines(template_lines)


def validate_config():
    """
    TODO: implement
    Check any known dependencies in the configurations before starting scripts.
    :return:
    """
    pass

def runtime_record_path():
    return os.path.join(configuration()["working_dir"], "runtime_record.txt")


def error_record_path():
    return os.path.join(configuration()["working_dir"], "errors.txt")


def path_diff(long_path: str, short_path: str, sep=os.sep, tail=True):
    """
    Returns the difference in both paths, and removes a trailing os path separator if necessary.
    By default, the method first attempts to find the diff at the tail of long_path.
    If this fails it attempts to find a diff at the start of long_path.

    Example tail:
        long_path = C:Users/usr/myGreatPath/subdir/myfile.txt
        short_path = C:Users/usr/myGreatPath
        result = subdir/myfile.txt

    Example start:
        long_path = myGreatPath/subdir/myfile.txt
        short_path = myfile.txt
        result = myGreatPath/subdir

    Example mid:
        long_path = C:Users/usr/myGreatPath/subdir/myfile.txt
        short_path = usr
        result = C:Users/

    you can change the order of search by passing tail=False

    :param long_path: The first path to diff against. long_path must be longer than short_path, can't contain backslashes
    :param short_path: The second path to diff against (may also be a filename), can't contain backslashes
    :param tail: Defines preferred diff location if the split happens to be mid path.
    :return: A path sequence that can directly be used with os.path.join.
    """
    if len(long_path) < len(short_path):
        log.critical(f"Precondition violation. Long path: {long_path} was shorter than: {short_path}.")
        exit(1)

    parts = long_path.split(short_path)
    # empty Strings are falsy https://peps.python.org/pep-0008/#programming-recommendations
    useful_parts = [element for element in filter(lambda x: x, parts)]
    if tail:
        diff = useful_parts[-1]
    else:
        diff = useful_parts[0]
    if diff[0] == sep:
        diff = diff[1:]
    if diff[-1] == sep:
        diff = diff[0:-2]
    return diff
