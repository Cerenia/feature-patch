import yaml
import os


config = None

def configuration():
    global config
    if config is None:
        print("Loading configs...")
        with open("./conf/config.yml", 'r') as f:
            config = yaml.safe_load(f)
    return config


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
