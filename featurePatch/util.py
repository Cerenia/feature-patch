import yaml


config = None


def configuration():
    global config
    if config is None:
        print("Loading configs...")
        with open("./conf/config.yml", 'r') as f:
            config = yaml.safe_load(f)
    return config


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
