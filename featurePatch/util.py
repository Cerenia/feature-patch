import yaml


# Read config file and provided args
def configure():
    pass


def load_configs():
    print("Loading configs...")
    with open("./conf/config.yml", 'r') as f:
        conf = yaml.safe_load(f)
    return conf

def add_to_config_template():
    """
     Run whenever you add a configuration variable, expects ..\conf\config.yml will modify ..\conf\config_template.yml additively
     Deleting flags should be done manually (for now)
    :return:
    """
    print("Editing configuration template...")
    conf = load_configs()
    with open("./conf/config_template.yml", "r") as f:
        conf_template = yaml.safe_load(f)
    for key in conf:
        if key not in conf_template.keys():
            print(f"Adding confguration item '{key}'")
            conf_template[key] = ""
    with open("./conf/config_template.yml", "w") as f:
        yaml.dump(conf_template, f)
