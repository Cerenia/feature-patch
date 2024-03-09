import yaml

from featurePatch.android.extractFeature import extract_feature
from featurePatch.android.applyFeature import run as applyFeature
from featurePatch.util import clear_contact_points, add_to_config_template
from featurePatch.git import *
from featurePatch.git import checkout_subrepo
from featurePatch.log import *
import argparse
import re

#####
#
# Configuration
#
#####

configparser: argparse.ArgumentParser


def configure(args):
    with open(args.config_filepath, "r") as f:
        lines = f.readlines()
    argdict = vars(args)
    new_lines = []
    for line in lines:
        if ':' in line:
            key = line.split(':')[0].strip()
            if key in argdict.keys() and argdict[key] is not None:
                new_value = argdict[key]
                new_lines.append(f'{key}: {new_value}\n')
                print(f"Updating configuration {key} to:\n{new_value}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    with open(args.config_filepath, 'w') as f:
        f.writelines(new_lines)


def enrich_with_config_options():
    """
    PRE: Assumes ./conf/config_template.yml as location for the template file.
    Otherwise, checks for the absolute path in the environment variable
    FP_CONFIGURATION_TEMPLATE_PATH
    if both fails, throws an error.
    """
    if os.path.isfile("./conf/config_template.yml"):
        configuration_template_path = "./conf/config_template.yml"
    else:
        try:
            configuration_template_path = os.environ["FP_CONFIGURATION_TEMPLATE_PATH"]
        except KeyError as e:
            print(e)
            print(
                "Path to configuration template could not be determined. Please set the environment variable 'FP_CONFIGURATION_TEMPLATE_PATH'")
            exit(1)

    fields = extract_config_fields(configuration_template_path)
    for t in fields:
        configparser.add_argument(f"--{t[0]}", help=t[1])


def extract_config_fields(configuration_template_path):
    """
    :param config_template: Where to find the configuration file.
    :return: list(field,comment), where comment may be empty
    """
    fields = []
    with open(configuration_template_path, 'r') as f:
        config = f.read()
    matches = re.finditer(r'(?P<comment>^#[^\n]*)\n(?P<field>\w+[ \t]*:)|(?P<lone_field>\w+[ \t]*:)', config,
                          re.MULTILINE)
    for match in matches:
        lone_field = match.group('lone_field')
        if lone_field is not None:
            fields.append((lone_field[:-1].strip(), ""))
        else:
            comment = match.group('comment').strip()[1:]
            field = match.group('field')[:-1].strip()
            fields.append((field, comment))
    return fields


#####
#
# Operations
#
#####


def extract(tag):
    print(f"#####\n##Extracting contact points\n#####\n")
    initialize_git_constants()
    create_subrepo_migration_branch(tag)
    checkout_subrepo_migration_branch(tag)
    extract_feature()


def migrate(args):
    initialize_git_constants()
    # TODO
    pass


def patch(args):
    initialize_git_constants()
    print(f"#####\n##Applying to tag {args.tag}\n#####\n")
    push_subrepo("Extracted contact points")
    upgrade_container_to(args.tag)
    checkout_subrepo_migration_branch(args.tag)
    applyFeature()
    clear_contact_points()


def merge(args):
    initialize_git_constants()
    print("#####\n##Merging changes in subrepository to master branch\n#####\n")
    push_subrepo(f"Upgrade to {args.tag} functional.")
    checkout_subrepo("master")
    merge_migration_branch(f"{args.tag}")
    push_subrepo(f"Merged {args.tag} back into master.")


def main():
    # Revert
    # clean_subrepo()
    # _checkout_subrepo("master")
    # delete_local_migration_branch("v1.1.1")

    # CLI Flow example
    """
    python fp.py extract v1.1.1
    -> Check error log for any issues that need to be resolved by hand
    python fp.py patch v1.1.1
    -> Check error log for any issues that need to be resolved by hand
    -> Fix any remaining issues by hand until app runs again
    python fp.py merge v1.1.1
    -> Continue coding on the new branch
    """
    global configparser

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    configuration_template_update = subparsers.add_parser('update_config_template',
                                                          help="Updates the configuration template with any new keys "
                                                               "present in the config.yml file with their associated "
                                                               "comment.")
    configuration_template_update.set_defaults(func=add_to_config_template)

    configparser = subparsers.add_parser('configure', help="configure config.yml with optional named arguments. Will "
                                                           "fetch these arguments from the configuration template.")
    configparser.add_argument('--config_filepath', help="Relative or absolute path to the configuration file. "
                                                        "Default: './conf/config.yml'", default="./conf/config.yml")
    configparser.set_defaults(func=configure)

    extraction = subparsers.add_parser('extract', help="Extracts current interface and pushes it to a new branch of "
                                                       "the subrepository named after the provided tag.")
    extraction.add_argument('tag', help='Tag to which to migrate the container')
    extraction.set_defaults(func=extract)

    patching = subparsers.add_parser('patch', help="Updates the container to the specified tag and attempts to apply "
                                                   "the interface back onto the updated code.")
    patching.add_argument('tag', help='Tag to which to migrate the container')
    patching.set_defaults(func=patch)

    migration = subparsers.add_parser('migrate', help="")
    migration.set_defaults(func=migrate)

    merging = subparsers.add_parser('merge', help="Merges any changes that occured to adapt to the update back into "
                                                  "the master branch of the subrepository.")
    merging.add_argument('tag', help='Tag to which to migrate the container')
    merging.set_defaults(func=merge)

    """
    # TODO: Still needed?
    match_parser = subparsers.add_parser('match', help="")
    match_parser.set_defaults(func=match)
    """

    # CLI TODO:
    # Deduce configs (some automation for the obvious things)
    # Set constant
    # Expose logging change to CLI
    # (Update config template?)

    args = parser.parse_args()

    if "--help" not in args.keys() or "-h" not in args.keys():
        init_log()
        args.func(args)


if __name__ == '__main__':
    main()
