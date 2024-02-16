# feature-patch
Utility to facilitate patching a dangling feature onto evolving Codebases.

This utility is targeted at researchers working with open source projects they may not have direct influence on. 
It aims to automate the process of upgrading to a new version of the codebase as much as possible, such that the focus of the developers can be concentrated on the final state of the codebase, instead of intermediate steps that would come up in traditional rebasing and may ultimately not be of importance. 

(TODO: Do we need a more extensive intro?)

This project uses the [git-subrepo](https://github.com/ingydotnet/git-subrepo) library to manage nested repositories, please refer to their installation instructions to install this requirement. The scripts of feature-patch expect to be run in a **bash** shell with an accessible [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git), and git-subrepo installation in it's path.

The project was tested with the following shells:
- Windows:
  - Git-Bash
  - WLS Ubuntu 22.04.3 LTS (TODO)
- Linux (TODO)

## Terminology and Principle

This utility expects two repositories. The evolving Codebase, which is out of control of the feature developers, will be called the `container` in the documentation. The nested repository, in turn, will be called `feature`.

For optimal efficacy



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

