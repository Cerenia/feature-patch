# feature-patch
Python utility facilitating patching a dangling feature onto evolving codebases.

This utility is targeted at researchers working with open source projects they may not have direct influence on. 

It aims to automate the process of upgrading to a new version of the upstream codebase and eliminating the need to traverse any intermediate steps encountered in traditional rebasing. The code is instead patched onto the, relevant revision of the upstream codebase.

This project uses the [git-subrepo](https://github.com/ingydotnet/git-subrepo) library to manage nested repositories, please refer to their installation instructions to install this requirement. The scripts of feature-patch expect to be run in a **bash** shell with an accessible [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git), and git-subrepo installation in it's path.

The project was tested with the following shells:
- Windows:
  - Git-Bash
  - WLS Ubuntu 22.04.3 LTS (TODO)
- Linux (TODO)

We ultimately strive for a modular implementation which lends itself to be extended to various codebases and welcome contributions. 

The first use-case was an Android project and there is thus currently a bias towards preexisting structures (e.g., folder hierarchies) found in this environment.

# Table of Contents <!-- omit from toc -->
- [feature-patch](#feature-patch)
  - [Terminology and Design Principles](#terminology-and-design-principles)
    - [Prerequisites](#prerequisites)
    - [Extraction](#extraction)
    - [Migration](#migration)
    - [Application](#application)
      - [Matching](#matching)
      - [Patching](#patching)
    - [Merging](#merging)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Tutorial \& Testing](#tutorial--testing)
    - [1. Fork the container](#1-fork-the-container)
    - [2. Checkout the `modified` branch](#2-checkout-the-modified-branch)
    - [3. Create and configure `config.yml`](#3-create-and-configure-configyml)
    - [4. Go through the testing workflow](#4-go-through-the-testing-workflow)
    - [Still TODO:](#still-todo)


## Terminology and Design Principles

This utility expects two repositories. The evolving Codebase, which is out of control of the feature developers, will be called the `container` in the documentation. The nested repository, in turn, will be called `feature`.

The `container`, a forked repository, will maintain an untouched `main` branch, which can be upgraded easily through a fetch. 
Each version of the 

To facilitate the migration process, interfaces between the `feature` and the `container` should be minimal. Specifically, any addition to files of the container, which may change on upgrades, should have a small `feature` footstep. This implies designing well defined interfaces wherever possible and factoring any logic out of the `container` files. Any additional logic should be accumulated in the `feature` subrepository.

### Prerequisites

In order to have a clear labeling, any code inserted into the `container` which calls `feature` logic, or adds elements, should be enclosed by comments containing a pseudorandom `marker` string (which must be consitent throughout the feature) and the words `start` and `end`, acting as `marker-brackets`. 

For example: 
```
//xP0w1dFQZBvxSHALdyEU MyGreatFeature start

myFeatureMethodCall(c: ContainerArg);

//xP0w1dFQZBvxSHALdyEU MyGreatFeature end
```

This facilitates the extraction of the interface before a migration and additionally allows for easy external auditing of any components that were added to the `container` for the feature.

Any added logic shoud be cleanly factored out to  the `feature` subrepository.

Sometimes (e.g, when adding new UI elements) a new file must be added to the contaner. Then, the file should contain a `marker-bracket` pair without any content.

For example:
```
<!--xP0w1dFQZBvxSHALdyEU MyGreatFeature start-->
<!--xP0w1dFQZBvxSHALdyEU MyGreatFeature end-->
```

### Extraction

Before a `container` upgrade feature-patch will extract the interface. 

For this a feature `migration-branch` will be created and checked out, consisting of the current state of the `feature`. Then the interface will be extracted into a folder inside the `feature` subrepository called `contact-points` whose internal structure encodes information on where in the container the files were found. The interface consists of any file that contains the marker. 

Here, a sanity check w.r.t `marker-bracket` matchings is performed and any noncompliant files are recorded in an error log in the working directory. 

Check and fix these files manually before continuing to the migration and application stages.

### Migration

After pushing the interface to the new branch, the `main` branch of the `container` is upgraded to the desired tag and a new branch for the reapplication and continuous development of this version is created. There, the feature `migration-branch`, which now includes the contact points are reinserted into the new `container` branch.

### Application

#### Matching

From there feature-patch will first attempt to match any contact point file in the `feature` with a corresponding file in the updated `container` repository. Any found match or contact point files that were marked as *new* (see [Prerequisites](#prerequisites)) will be recorded in the runtime log. Any files left in the contact points will be recorded in the error log in a human friendly [json](https://docs.python.org/3/library/json.html) format. You may manually edit these files or fix errors and rerun this step before moving on to the application.

#### Patching

After the creation of the runtime log the utility will attempt to diff and merge any matched files and replace the corresponding files in the `container`. Pure copy files will simply be copied into the corresponding location in the `container`. Finally the contact-points folder of the subrepository is removed to allow the developer to iron out any bugs.

### Merging

Once the application is updated back to a functional point, the merging of the now updated `feature` repository can be run. This will simply merge the current migration branch back into master and check master back out into the `container` repository. Development can now continue 'normally' on the `container` branch that was newly created for this version, without needing to worry about the subrepository until the next migration.

## Installation

Install [git-subrepo](https://github.com/ingydotnet/git-subrepo) and [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) according to the instructions for your platform and make sure to add the executables to your path. 

Install the python dependencies (preferably in a [Python virtualenv](https://docs.python.org/3/library/venv.html)) by running:

```
pip install -r requirements.txt
```

## Configuration


The `config_template.yml` file in the `conf` folder show all the system specific configuration parameters.
Copy the template into a file called `config.yml` and fill in all the fields. The comments document their purpose. If `config.yml` is placed in the `conf` folder, git will ignore the file (configured in .gitignore), avoiding your credentials to be pushed to github :)

The utility can also be configured with the CLI:

```
python fp.py configure --<flag> <value>
```

The script will try to find the configuration template file at: `./conf/config_template.yml`. If this fails, it attempts to find the absolute path of `config_template.yml` in the environment variable `FP_CONFIGURATION_TEMPLATE_PATH`.

```
python fp.py configure --help
```

Will list all the configurable flags and the documenting comments.

If a flag is added during development, calling:

```
python fp.py update_config_template
```

Will add it to the template preserving the documenting comment above the field and with `TODO` as a value. Please keep the template up to date.

## Tutorial & Testing

We host two example repositories to test the flow of the utility. 
The container is a simple medication reminder app with an embedded separate feature.

### 1. Fork the [container](https://github.com/Cerenia/Simpill)

**Make sure to include all the branches in your fork and not just `main`.** 

Then clone the fork to your machine:

```
git clone <fork_url>
```

The repository has two branches, `main` and `modified`, and two tags marking commits on the `main` branch. 
You can check this by navigating into the `Simpill` directory and running:
```
git branch -a
```
Note that only the main branch was replicated locally, and both branches exist in the remote.
The `modified` branch is based on tag `v1.1.0` and includes the embedded [feature](https://github.com/Cerenia/Simpill-subrepo). The `main` container branch has some simple additions to the code and is tagged with `v1.1.1`.

You can list the tags with:
```
git tag
```


### 2. Checkout the `modified` branch

```
git checkout -b modified origin/modified
```

Navigate to the source folder of the container:
`<container_root>\app\src\main\java\com\example\simpill`

The feature code is in the `ext` folder, indicated by the `.gitrepo` file, which also records which branch of the subrepository is currently checked out. This should currently be `master`.

Any interface code of the feature in the container is delimited by the marker:

`IXwDmcyAEZEUvkES0IXy144JB SimPillAddOn`

You can observe this in the following files:
```
<container_root>\app\src\main\java\com\example\simpill\ MainActivity.java
<container_root>\app\src\res\layout\app_main.xml
<container_root>\app\src\res\layout\log_view.xml
```

Both `MainActivity.java` and `app_main.xml` were adapted from the container and have inserts that are framed by two markers and the words `start` and `end`.

`log_view.xml` is a file that was added to the container. This is marked by the same brackets without any code inbetween.

### 3. Create and configure `config.yml`

Simply copy and rename the template file in the `conf` folder of your copy of the `feature-patch` repository, and fill in the configuration according to the comments for each field. You can also use the CLI directly.

For example to update the marker:

```
python fp.py configure --marker "IXwDmcyAEZEUvkES0IXy144JB SimPillAddOn"
```

### 4. Go through the testing workflow

a) `python fp.py extract v1.1.1`

=> contact points extracted and new branch created

b) `python fp.py migrate v1.1.1`

=> container updated and contact points pushed to new subrepo branch

### Still TODO:

- Figure out clean way to fork subrepository to allow non-collaborators to run the tests

