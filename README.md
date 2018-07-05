[![PyPI version](https://badge.fury.io/py/mkinx.svg)](https://badge.fury.io/py/mkinx)

# About

`mkinx` allows you to integrate several `sphinx` documentation projects into one Home Documentation listing them and allowing you to have cross projects documentation with `mkdocs`. 

Any `sphinx` module can be used as long as `make html` works and the built code is in `your_project/build`.

`mkinx` comes with an example project and a standalone documention so you can already get started!

Default settings are that the Home Documentation will use a Material Design theme and Project Documentations will use Read The Docs's theme, to better distinguish the hierarchy. You can change that (in respectively `mkdocs.yml` and `conf.py`).

# Install

```
pip install mkinx
```

# Getting Started

Start your Home Documentation with:

```
mkinx init your_project
```

Start the server with 

```
mkinx serve
```

Optionnaly you can specify a port with `mkinx serve -s your_port`

Build the documentation with 

```
mkinx build [FLAGS]
```

Flags being:

```
  -v, --verbose                             verbose flag (Sphinx will stay verbose)
  -A, --all                                 Build doc for all projects
  -F, --force                               force the build, no verification asked
  -o, --only_index                          only build projects listed in the Documentation's Home
  -p, --projects [PROJECTS [PROJECTS ...]]  list of projects to build
```

# Usage

The package comes with a thorough documentation by default, which you'll see by running `mkinx serve` after a proper `init`. A Read The Docs-hosted version may arrive at some point. 

The built in documentation is there to help you but is in no way necessary, you can overwrite or delete everything. **There are however 2 mandatory things:**

**1**-> You have to keep this structure:

```
your_home_documentation/
    mkdocs.yml
    docs/ # your home documentation, listing sphinx docs
        index.md # mandatory file -> mkdocs's index
    site/
    your_project_1/
        build/ # sphinx's build directory
        source/ # sphinx's documentation source directory
        your_package_1_1/
        your_package_1_2/
        ...
    your_project_2/
        build/
        source/
        your_package_2_1/
        your_package_2_2/
        ...
    ...
```

**2** -> `mkdocs`'s `index.md` file must have a `# Projects` section listing them as in the example

Also, remember to run commands from your Home Documenation's root folder (in `your_home_documentation/` in the example above) otherwise you may get errors saying `mkinx` can't find a file.

## Adding a Python project

`mkinx` comes with a useful `autodoc` command helping you easily add a new python project to your documentation.

All you have to do is put the documented (Google-style docstrings) code along the documentation in `your_home_documentation/`. Say it's called `your_project_3`. Then you just need to go there and use `autodoc`:

```
$ cp -r path/to/your_project_3 path/to/doc/your_home_documentation/
$ cd your_home_documentation/your_project_3/
$ mkinx autodoc
```

Under the hood, `mkinx autodoc` runs `sphinx-quickstart`, updates default values to be compatible to the `mkinx` setting, builds the documentation with `mkinx build` and updated the Home Documentation's `index.md` file to list `your_project_3`.

If `mkinx autodoc`'s default values for the `sphinx` documentation don't suit you, do update `your_project_3/conf.py`.

## Customization

You may use any other theme for instance. To use `mkdocs-nature` just:

```
pip install mkdocs-nature
```

Then change this in `mkdocs.yaml` : `theme: nature` and finally:

```
mkdocs build
```