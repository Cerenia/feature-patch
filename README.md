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

To facilitate the migration process, the interfaces between the feature and the container should be minimized. Specifically, any addition to files of the container, which may change on upgrades, should have minimal code which belongs to the feature. This implies designing well defined interfaces wherever possible and factoring any logic out of the container files. The logic should be accumulated in one place, which in our case will be in the feature subrepository.

In order to have a clear labeling, any code inserted into the container which calls feature logic 



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

