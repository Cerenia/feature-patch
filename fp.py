from featurePatch.android.extractFeature import extract_feature
from featurePatch.android.applyFeature import match as af_match
from featurePatch.android.applyFeature import patch as af_patch
from featurePatch.util import clear_contact_points, add_to_config_template
from featurePatch.git import *
import argparse
import re

#####
#
# Configuration
#
#####

configparser: argparse.ArgumentParser


def configure(args):
    """
    Change any parameter in config.yml, will ignore any extraneous keys
    :param args: args.keys() may contain any yaml key defined in config.yml to change
    """
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
# Testing
#
####

def relink(args):
    checkout_feature(args.branch)


#####
#
# Operations
#
#####


def extract(args):
    """
    Creates an extraction branch named after 'tag' and checks it out. Then walks through all the relevant files in the
    android project and extracts the contact points of the container into the subrepository.
    :param args.tag: The version tag that is finally to be migrated to (this will determine the name of the extraction branch)
    """
    print(f"#####\n##  Extracting contact points\n#####\n")
    initialize_git_constants()
    create_feature_migration_branch(args.tag)
    checkout_feature_migration_branch(args.tag)
    extract_feature()
    push_subrepo("Extracted contact points")


def migrate(args):
    """
    Pushes the extracted contact points. Then updates the container to the specified tags and reinserts the contact
    points branch of the subrepository.
    :param args.tag: Which tag to upgrade the container to
    """
    initialize_git_constants()
    # TODO: Maybe be a bit cleaner? should this be it's own subparser??
    if args.delete_container_and_feature_migration_branch:
        delete_container_and_feature_migration_branch(args.tag)
    elif args.checkout_feature_migration_branch_only:
        # only reinsert the feature migration branchpyth
        checkout_feature_migration_branch(args.tag)
    elif args.checkout_feature_only:
        # only reinsert any feature branch
        checkout_feature(args.tag)
    else:
        print(f"#####\n##  Migrating to tag {args.tag}\n#####\n")
        upgrade_container_to(args.tag)
        checkout_feature_migration_branch(args.tag)


def match(args):
    """
    Walk through the contact points and match the corresponding container files. Log any errors.
    """
    initialize_git_constants()
    print("#####\n##  Matching contact points...\n#####\n")
    if args.branch:
        checkout_container(args.branch)
    af_match()


def patch(args):
    """
    Walk through the runtime log and attempt to patch all the container files with the contact point files.
    Log any errors. Finally remove the contact points from the subrepository folder to allow for manual cleanup.
    """
    initialize_git_constants()
    print("#####\n##  Patching container contact points...\n#####\n")
    af_patch()
    print("#####\n##  Clearing feature contact points...\n#####\n")
    clear_contact_points()


def merge(args):
    """
    Merges changes done to the migration branch of the feature back into master and checks out master for continued
    development. Only call once you are done fixing the patch.
    :param args.tag: Migration version tag.
    """
    print("#####\n##  Checking out and merging into feature main branch...\n#####\n")
    initialize_git_constants()
    print("#####\n##  Merging changes in feature to master branch\n#####\n")
    # Was barfing because of uncommited container, container is commited in checkout_feature..
    push_subrepo(f"Upgrade to {args.tag} functional.")
    checkout_feature("master")
    merge_migration_branch(f"{args.tag}")
    push_subrepo(f"Merged {args.tag} back into master.")


def update_unmodified(args):
    """"
    Update unmodified to whatever was in the tag provided in the arguments.
    Should be the same tag you are now freshly developing on.
    """
    initialize_git_constants()
    update_unmodified_branch(args.tag)


def main():
    # Revert TODO: group in test method
    # clean_subrepo()
    # _checkout_subrepo("master")
    # initialize_git_constants()
    # delete_local_migration_branch("v1.1.1")

    global configparser

    parser = argparse.ArgumentParser(description='Call the functions in the order specified in the README: ')
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
    enrich_with_config_options()

    extraction = subparsers.add_parser('extract', help="Extracts current interface and pushes it to a new branch of "
                                                       "the subrepository named after the provided tag. "
                                                       "Finally pushed the new branch to the remote subrepo.")
    extraction.add_argument('tag', help='Tag to which to migrate the container')
    extraction.set_defaults(func=extract)

    migration = subparsers.add_parser('migrate', help="Update the container to the specified tag and checkout "
                                                      "new subrepo branch containing the contact points. Extra hidden args "
                                                      "exist to facilitate debugging and branch removal, see source for details.")
    migration.add_argument('tag', help='Tag to which to migrate the container')
    # Remove the feature migration branch of the container both locally and remotely
    migration.add_argument('-d_mb', '--delete_container_and_feature_migration_branch', action='store_true', help=argparse.SUPPRESS)
    # This should only be called in abnormal operations
    migration.add_argument('-c_mb', '--checkout_feature_migration_branch_only', action='store_true', help=argparse.SUPPRESS)
    # In this case, tag is interpreted as the branch of the feature
    migration.add_argument('-c', '--checkout_feature_only', action='store_true', help=argparse.SUPPRESS)
    migration.set_defaults(func=migrate)

    matching = subparsers.add_parser('match', help="Matches up all files and creates a runtime and error log "
                                                   "documenting successes and failures.")
    matching.add_argument('--branch', help='Optionally check out container to the specified branch.')
    matching.set_defaults(func=match)

    patching = subparsers.add_parser('patch', help="Copies and patches files wherever possible, updating runtime and "
                                                   "error logs and finally removes the contact points from the "
                                                   "subrepository to allow for manual cleanup.")
    patching.set_defaults(func=patch)

    merging = subparsers.add_parser('merge', help="Merges any changes that occured to adapt to the update back into "
                                                  "the master branch of the subrepository.")
    merging.add_argument('tag', help='Tag to which to migrate the container')
    merging.set_defaults(func=merge)

    update_umdf = subparsers.add_parser('update_unmodified', help='Updates the unmodified branch to be the untouched '
                                                                        'version of the current tag we are working on, ready for '
                                                                        'the next sync.')
    update_umdf.add_argument('tag', help="The tag onto which the feature was last patched. ")
    update_umdf.set_defaults(func=update_unmodified)

    relink_feature = subparsers.add_parser('relink', help="Removes the feature and checks out the master branch of "
                                                          "the feature repository configured in config.yml")

    relink_feature.add_argument('branch', help='Which branch to check out', default='master')
    relink_feature.set_defaults(func=relink)

    # CLI still TODO:
    # Deduce configs (some automation for the obvious things, e.g., deducable Android paths)
    # Set constant
    # Expose logging change to CLI (and fix debug showing throughout INFO?)

    args = parser.parse_args()

    args.func(args)


if __name__ == '__main__':
    main()
