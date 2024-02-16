# feature-patch
Python utility facilitating patching a dangling feature onto evolving codebases.

This utility is targeted at researchers working with open source projects they may not have direct influence on. 

It aims to automate the process of upgrading to a new version of the codebase as much as possible, such that the focus of the developers can be concentrated on the final state of the codebase, instead of intermediate steps that would come up in traditional rebasing which may ultimately not be of importance. 

(TODO: Do we need a more extensive intro?)

This project uses the [git-subrepo](https://github.com/ingydotnet/git-subrepo) library to manage nested repositories, please refer to their installation instructions to install this requirement. The scripts of feature-patch expect to be run in a **bash** shell with an accessible [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git), and git-subrepo installation in it's path.

The project was tested with the following shells:
- Windows:
  - Git-Bash
  - WLS Ubuntu 22.04.3 LTS (TODO)
- Linux (TODO)

We ultimately strive for a modular implementation which lends itself to be extended to various codebases and welcome contributions. 

The first use-case was an Android project and there is thus currently a bias towards preexisting structures (e.g., folder hierarchies) found in these environments.

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

After pushing the interface to the new branch, the `main` branch of the `container` is upgraded to the desired tag and a new branch for the reapplication and continuous development of this version is created (named after the new tag). There, the feature `migration-branch` which now includes the contact points are reinserted into the new `container` branch.

## Installation

Install [git-subrepo](https://github.com/ingydotnet/git-subrepo) and [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) according to the instructions for your platform and make sure to add the executables to your path. 

Install the python dependencies (preferably in a [Python virtualenv](https://docs.python.org/3/library/venv.html)) by running:

```
pip install -r requirements.txt
```

## Configuration

The utility can be configured with the cli with the following command:

```

```

Which will 

## Testing

- Document Simpill and Simpill-subrepo

## Prerequisites

- Mark any code you insert with the marker
- Whole files to be inserted should have a marker pair as the first comment of the file
- The smaller you can keep the interface the better

