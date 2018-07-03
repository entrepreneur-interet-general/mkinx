import json
import os
import subprocess
from pathlib import Path
import re
import time
from watchdog.events import PatternMatchingEventHandler
from shutil import copyfile

from .conf import PROJECT_KEY, HTML_LOCATION, TO_REPLACE_WITH_HOME
from .conf import NEW_HOME_LINK

import fnmatch


class colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def suggest_path(func):
    def wrapper(*args, **kwds):
        try:
            func(*args, **kwds)
        except FileNotFoundError as e:
            print(e)
            print()
            print(
                '{}Are you sure you ran "{}" in the right directory?{}'.format(
                    colors.FAIL, func.__name__, colors.ENDC
                )
            )
            try:
                dir_path = Path().absolute()
                potential_projects = [
                    str(p)
                    for p in dir_path.iterdir()
                    if p.is_dir()
                    and any(["mkdocs.yml" in str(sp) for sp in p.iterdir()])
                ]
                locations = [
                    "." + p[p.find(str(dir_path)) + len(str(dir_path)) :]
                    for p in potential_projects
                ]
                print("Try in", "\n".join(locations))
            except:
                pass

    return wrapper


def overwrite_home(project, dir_path):
    """In the project's index.html built file, replace the top "source"
    link with a link to the documentation's home, which is mkdoc's home

    Args:
        project (str): project to update
        dir_path (pathlib.Path): this file's path
    """

    project_html_location = dir_path / project / HTML_LOCATION
    if not project_html_location.exists():
        return
    with open(project_html_location, "r") as index_html:
        new_html_reversed = index_html.readlines()[::-1]
    for i, l in enumerate(new_html_reversed):
        if TO_REPLACE_WITH_HOME in l:
            new_html_reversed[i] = NEW_HOME_LINK
            break
    with open(project_html_location, "w") as index_html:
        new_html = new_html_reversed[::-1]
        index_html.writelines(new_html)


def get_listed_projects():
    """Find the projects listed in the Home Documentation's
    index.md file

    Returns:
        set(str): projects' names, with the '/' in their beginings
    """
    index_path = Path().resolve() / "docs" / "index.md"
    with open(index_path, "r") as index_file:
        lines = index_file.readlines()

    listed_projects = set()
    project_section = False
    for _, l in enumerate(lines):
        idx = l.find(PROJECT_KEY)
        if idx >= 0:
            project_section = True
        if project_section:
            # Find first parenthesis after the key
            start = l.find("](")
            if start > 0:
                closing_parenthesis = sorted(
                    [m.start() for m in re.finditer(r"\)", l) if m.start() > start]
                )[0]
                project = l[start + 2 : closing_parenthesis]
                listed_projects.add(project)
        # If the Projects section is over, stop iteration.
        # It will stop before seeing ## but wainting for it
        # Allows the user to use single # in the projects' descriptions
        if len(listed_projects) > 0 and l.startswith("#"):
            return listed_projects
    return listed_projects


def set_routes():
    """Set the MKINX_ROUTES environment variable with a serialized list
    of list of routes, one route being:
        [pattern to look for, absolute location]
    """
    os.system("pwd")
    dir_path = Path(os.getcwd()).absolute()
    projects = get_listed_projects()
    routes = [
        [p if p[0] == "/" else "/" + p, str(dir_path) + "{}/build/html".format(p)]
        for p in projects
    ]
    os.environ["MKINX_ROUTES"] = json.dumps(routes)


def get_routes():
    """Parse routes from environment.

    Returns:
        list(list): list of routes, one route being:
            [pattern to look for, absolute location]
    """
    return json.loads(os.getenv("MKINX_ROUTES", "[[]]"))


class MkinxFileHandler(PatternMatchingEventHandler):
    """Class handling file changes:
        .md: The Home Documentation has been modified
            -> mkdocs build
        .rst: A project's sphinx documentation has been modified
            -> mkinx build -F -p {project}
    """

    def on_any_event(self, event):
        set_routes()

        offline = ""
        if event.src_path.split(".")[-1] == "md":
            _ = subprocess.check_output("mkdocs build > /dev/null", shell=True)
            if json.loads(os.getenv("MKINX_OFFLINE", "false")):
                make_offline()

        if event.src_path.split(".")[-1] == "rst":
            # src_path:
            # /Users/you/Documents/YourDocs/example_project/source/index.md
            # os.getcwd():
            # /Users/you/Documents/YourDocs
            # relative_path:
            # /example_project/docs/index.md
            # project: example_project

            relative_path = event.src_path.split(os.getcwd())[-1]
            project = relative_path.split("/")[1]
            if json.loads(os.getenv("MKINX_OFFLINE", "false")):
                offline = "--offline"
            os.system("mkinx build -F {} -p {} > /dev/null".format(offline, project))


def make_offline():
    """Deletes references to the external google fonts in the Home
    Documentation's index.html file
    """
    dir_path = Path(os.getcwd()).absolute()

    css_path = dir_path / "site" / "assets" / "stylesheets"
    material_css = css_path / "material-style.css"
    if not material_css.exists():
        file_path = Path(__file__).resolve().parent
        copyfile(file_path / "material-style.css", material_css)
        copyfile(file_path / "material-icons.woff2", css_path / "material-icons.woff2")

    indexes = []
    for root, _, filenames in os.walk(dir_path / "site"):
        for filename in fnmatch.filter(filenames, "index.html"):
            indexes.append(os.path.join(root, filename))
    for index_file in indexes:
        update_index_to_offline(index_file)


def update_index_to_offline(path):
    with open(path, "r") as f:
        lines = f.readlines()
    new_lines = []
    for l in lines:
        if "https://fonts" in l:
            if "icon" in l:
                new_lines.append(
                    '<link rel="stylesheet"'
                    + " href=/assets/stylesheets/material-style.css>"
                )
            elif "css" in l:
                pass
        else:
            new_lines.append(l)
    with open(path, "w") as f:
        f.writelines(new_lines)
