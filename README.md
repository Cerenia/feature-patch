# feature-patch
Utility to facilitate patching a dangling feature onto evolving Codebases.

This project uses the [git-subrepo](https://github.com/ingydotnet/git-subrepo) library to manage nested repositories, please refer to their installation instructions. The scripts of feature-patch thus expect to be run in a **bash** shell with an accessible [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git), and git-subrepo installation in the path.

The project was tested with the following shells:
- Windows:
  - Git-bash
  - WLS Ubuntu 22.04.3 LTS (TODO)
- Linux (TODO)

## Terminology



## Installation

Install the dependencies (preferably in a [Python virtualenv](https://docs.python.org/3/library/venv.html)) by running:

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


TODO: Keep updating README