import yaml

from featurePatch.android.extractFeature import extract_feature
from featurePatch.android.applyFeature import run as applyFeature
from featurePatch.util import clear_contact_points, add_to_config_template
from featurePatch.git import *
from featurePatch.git import checkout_subrepo
from featurePatch.log import *
import argparse
import re


def extract(tag):
    print(f"#####\n##Extracting contact points\n#####\n")
    create_subrepo_migration_branch(tag)
    checkout_subrepo_migration_branch(tag)
    extract_feature()


def migrate():
    pass


def match():
    pass


def apply():
    pass


def configure(config_filepath, args):
    with open(config_filepath, "r") as f:
        lines = f.readlines()
    argdict = vars(args)
    new_lines = []
    for line in lines:
        if ':' in line:
            key = line.split(':')[0].strip()
            if key in argdict.keys():
                new_value = argdict[key]
                new_lines.append(f'{key}: {new_value}')
                print(f"Updating configuration {key} to:\n{new_value}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    with open(config_filepath, 'w'):
        f.writelines(new_lines)


def enrich_with_config_options(config_filepath, parser):
    fields = extract_config_fields(config_filepath)
    for t in fields:
        parser.add_argument(f"--{t[0]}", help=t[1])


def extract_config_fields(config_filepath):
    """
    :param config_filepath: Where to find the configuration file.
    :return: list(field,comment), where comment may be empty
    """
    fields = []
    with open(config_filepath, 'r') as f:
        config = f.read()
    matches = re.finditer(r'(?P<comment>^#[^\n]*)\n(?P<field>\w+[ \t]*:)|(?P<lone_field>\w+[ \t]*:)', config, re.MULTILINE)
    for match in matches:
        lone_field = match.group('lone_field')
        if lone_field is not None:
            fields.append((lone_field[:-1].strip(),""))
        else:
            comment = match.group('comment').strip()[1:]
            field = match.group('field')[:-1].strip()
            fields.append((field, comment))
    return fields


def patch(tag):
    print(f"#####\n##Applying to tag {tag}\n#####\n")
    push_subrepo("Extracted contact points")
    upgrade_container_to(tag)
    checkout_subrepo_migration_branch(tag)
    applyFeature()
    clear_contact_points()


def merge(tag):
    print("#####\n##Merging changes in subrepository to master branch\n#####\n")
    push_subrepo(f"Upgrade to {tag} functional.")
    checkout_subrepo("master")
    merge_migration_branch(f"{tag}")
    push_subrepo(f"Merged {tag} back into master.")


def main():
    # Revert
    #clean_subrepo()
    #_checkout_subrepo("master")
    #delete_local_migration_branch("v1.1.1")

    # CLI Flow example
    """
    python fp.py extract v1.1.1
    -> Check error log for any issues that need to be resolved by hand
    python fp.py apply v1.1.1
    -> Check error log for any issues that need to be resolved by hand
    -> Fix any remaining issues by hand until app runs again
    python fp.py merge v1.1.1
    -> Continue coding on the new branch
    """

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    extract_parser = subparsers.add_parser('extract', help="Extracts current interface and pushes it to a new branch of the subrepository named after the provided tag.")
    extract_parser.add_argument('tag', help='Tag to which to migrate the container')
    extract_parser.set_defaults(func=extract)

    apply_parser = subparsers.add_parser('patch', help="Updates the container to the specified tag and attempts to apply the interface back onto the updated code.")
    apply_parser.add_argument('tag', help='Tag to which to migrate the container')
    apply_parser.set_defaults(func=patch)

    merge_parser = subparsers.add_parser('merge', help="Merges any changes that occured to adapt to the update back into the master branch of the subrepository.")
    merge_parser.add_argument('tag', help='Tag to which to migrate the container')
    merge_parser.set_defaults(func=merge)

    config_update_parser = subparsers.add_parser('update_config_template', help="Updates the configuration template with any new keys present in the config.yml file with their associated comment.")
    config_update_parser.set_defaults(func=add_to_config_template)

    migrate_parser = subparsers.add_parser('migrate',  help="")
    migrate_parser.set_defaults(func=migrate)

    match_parser = subparsers.add_parser('match', help="")
    match_parser.set_defaults(func=match)

    patch_parser = subparsers.add_parser('apply', help="")
    patch_parser.set_defaults(func=patch)

    enrich_with_config_options("./conf/config.yml", parser)


    # CLI TODO:
    # Deduce configs (some automation for the obvious things)
    # Set config (Make anything configurable from CLI)
    # Set constant
    # Expose logging change to CLI
    # (Update config template?)

    args = parser.parse_args()

    configure("./conf/config.yml", args)


    #TODO: fix
    #args.func(args.tag) if "tag" in vars(args).keys() else args.func()


if __name__ == '__main__':
    main()
