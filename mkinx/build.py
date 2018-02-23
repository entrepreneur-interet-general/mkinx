from subprocess import call
import os
import sys
import re
from pathlib import Path
from shutil import copyfile, copytree
from http.server import SimpleHTTPRequestHandler
import socketserver
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import threading
import json

__VERSION__ = '0.1.4.2'

# For a directoy to be considered as a project with documentation
# It must contain this empty file:
PROJECT_MARKER = '__project__'
# Key to state that a project's hard links must be updated
PROJECT_KEY = '# Projects'
# Hard link to the index.html file to update with link to the
# Documentation's home
HTML_LOCATION = 'build/html/index.html'
# mkdocs's home file
MKDOCS_INDEX = 'docs/index.md'

# Substring marking the line to replace
TO_REPLACE_WITH_HOME = '<a href="_sources/index.rst.txt" '
# New line replacing the above one
NEW_HOME_LINK = '<h3><a href="/"> Documentation\'s Home</a></h3>'
PORT = 8443


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class MkinxFileHandler(PatternMatchingEventHandler):
    """Class handling file changes:
        .md: The Home Documentation has been modified
            -> mkdocs build
        .rst: A project's sphinx documentation has been modified
            -> mkinx build -F -p {project}
    """

    def on_modified(self, event):
        set_routes()
        if event.src_path.split('.')[-1] == 'md':
            os.system('mkdocs build > /dev/null')

        if event.src_path.split('.')[-1] == 'rst':
            # src_path:
            # /Users/you/Documents/YourDocs/example_project/source/index.md
            # os.getcwd():
            # /Users/you/Documents/YourDocs
            # relative_path:
            # /example_project/docs/index.md
            # project: example_project

            relative_path = event.src_path.split(os.getcwd())[-1]
            project = relative_path.split('/')[1]
            os.system('mkinx build -F -p {} > /dev/null'.format(project))


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
    with open(project_html_location, 'r') as index_html:
        new_html_reversed = index_html.readlines()[::-1]
    for i, l in enumerate(new_html_reversed):
        if TO_REPLACE_WITH_HOME in l:
            new_html_reversed[i] = NEW_HOME_LINK
            break
    with open(project_html_location, 'w') as index_html:
        new_html = new_html_reversed[::-1]
        index_html.writelines(new_html)


def get_listed_projects():
    """Find the projects listed in the Home Documentation's
    index.md file

    Returns:
        set(str): projects' names, with the '/' in their beginings
    """
    index_path = Path().resolve() / 'docs' / 'index.md'
    with open(index_path, 'r') as index_file:
        lines = index_file.readlines()

    listed_projects = set()
    project_section = False
    for _, l in enumerate(lines):
        idx = l.find(PROJECT_KEY)
        if idx >= 0:
            project_section = True
        if project_section:
            # Find first parenthesis after the key
            start = l.find('](')
            if start > 0:
                closing_parenthesis = sorted(
                    [m.start() for m in re.finditer(r'\)', l)
                        if m.start() > start]
                )[0]
                project = l[start + 2: closing_parenthesis]
                listed_projects.add(project)
        # If the Projects section is over, stop iteration.
        # It will stop before seeing ## but wainting for it
        # Allows the user to use single # in the projects' descriptions
        if len(listed_projects) > 0 and l.startswith('#'):
            return listed_projects
    return listed_projects


def set_routes():
    """Set the MKINX_ROUTES environment variable with a serialized list
    of list of routes, one route being:
        [pattern to look for, absolute location]
    """
    os.system('pwd')
    dir_path = Path(os.getcwd()).absolute()
    projects = get_listed_projects()
    routes = [
        [p if p[0] == '/' else '/' + p,
         str(dir_path) + '{}/build/html'.format(p)]
        for p in projects
    ]
    os.environ['MKINX_ROUTES'] = json.dumps(routes)


def get_routes():
    """Parse routes from environment.

    Returns:
        list(list): list of routes, one route being:
            [pattern to look for, absolute location]
    """
    return json.loads(os.getenv('MKINX_ROUTES', '[[]]'))


def serve(args):
    """Start a server which will watch .md and .rst files for changes.
    If a md file changes, the Home Documentation is rebuilt. If a .rst
    file changes, the updated sphinx project is rebuilt

    Args:
        args (ArgumentParser): flags from the CLI
    """
    # Sever's parameters
    port = args.serve_port or PORT
    host = '0.0.0.0'

    # Current working directory
    dir_path = Path().absolute()
    web_dir = dir_path / 'site'

    # Update routes
    set_routes()

    class MkinxHTTPHandler(SimpleHTTPRequestHandler):
        """Class routing urls (paths) to projects (resources)
        """

        def translate_path(self, path):
            # default root -> cwd
            location = str(web_dir)
            route = location

            if len(path) != 0 and path != '/':
                for key, loc in get_routes():
                    if path.startswith(key):
                        location = loc
                        path = path[len(key):]
                        break

            if location[-1] == '/' or not path or path[0] == '/':
                route = location + path
            else:
                route = location + '/' + path

            # print(location)
            # print(path)
            # print(route.split('?')[0])
            return route.split('?')[0]

    # Serve as deamon thread
    httpd = socketserver.TCPServer((host, port), MkinxHTTPHandler)
    httpd.allow_reuse_address = True
    print("\nServing at http://{}:{}\n".format(host, port))
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()

    # Watch for changes
    event_handler = MkinxFileHandler(patterns=['*.rst', '*.md'])
    observer = Observer()
    observer.schedule(event_handler, path=str(dir_path), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        httpd.server_close()
    observer.join()


def build(args):
    """Build the documentation for the projects specified in the CLI.
    It will do 4 different things for each project the
    user asks for (see flags):
        1. Update mkdocs's index.md file with links to project
           documentations
        2. Build these documentations
        3. Update the documentations' index.html file to add a link
           back to the home of all documentations
        4. Build mkdoc's home documentation

    Args:
        args (ArgumentParser): parsed args from an ArgumentParser
    """
    # Proceed?
    go = False

    # Current working directory
    dir_path = Path().resolve()

    # Set of all available projects in the dir
    # Projects must contain a PROJECT_MARKER file.
    all_projects = {m for m in os.listdir(dir_path)
                    if os.path.isdir(m) and
                    PROJECT_MARKER in os.listdir(dir_path / m)}

    if args.all and args.projects:
        raise ValueError("Can't use both the 'projects' and 'all' flags")

    if not args.all and not args.projects:
        raise ValueError("You have to specify at least one project (or all)")

    if args.force:
        go = True
        projects = all_projects if args.all else all_projects.intersection(
            set(args.projects))

    elif args.projects and 'y' in input(
        'You are about to build the docs for: \
        \n- {}\nContinue? (y/n) '.format(
            '\n- '.join(args.projects)
        )
    ):
        go = True
        projects = all_projects.intersection(
            set(args.projects))
    elif args.all and 'y' in input(
            "You're about to build the docs for ALL projects.\
            \nContinue? (y/n) "
    ):
        go = True
        projects = all_projects

    if go:
        # Update projects links
        listed_projects = get_listed_projects()

        # Don't update projects which are not listed in the Documentation's
        # Home if the -o flag was used
        if args.only_index:
            projects = listed_projects.intersection(projects)

        for project_to_build in projects:
            # Re-build documentation
            if args.verbose:
                os.system("cd {} && make clean && make html".format(
                    dir_path / project_to_build
                ))
            else:
                os.system(
                    "cd {} && make clean && make html > /dev/null".format(
                        dir_path / project_to_build
                    ))

            # Add link to Documentation's Home
            overwrite_home(project_to_build, dir_path)

            if args.verbose:
                print('\n>>>>>> Done {}\n\n\n'.format(
                    project_to_build
                ))
        # Build Documentation
        if args.verbose:
            os.system("mkdocs build")
            print('\n\n>>>>>> Build Complete.')
        else:
            os.system("mkdocs build > /dev/null")


def init(args):
    """Initialize a Home Documentation's folder

    Args:
        args (ArgumentParser): Flags from the CLI

    Raises:
        ValueError: Project name should be just strings, not a path
        ValueError: Project should not already exist
    """
    # working directory
    dir_path = Path().absolute()

    if not args.project_name or args.project_name.find('/') >= 0:
        raise ValueError('You should specify a valid project name')

    project_path = dir_path / args.project_name

    # Create the Home Documentation's directory
    if not project_path.exists():
        project_path.mkdir()
    else:
        raise ValueError('This project already exists')

    # Directory with the Home Documentation's source code
    home_doc_path = project_path / 'docs'
    home_doc_path.mkdir()

    file_path = Path(__file__).resolve().parent

    # Add initial files
    copyfile(file_path / 'documentation.md',
             home_doc_path / 'documentation.md')
    copyfile(file_path / 'index.md',
             home_doc_path / 'index.md')

    with open(file_path/'mkdocs.yml', 'r') as f:
        lines = f.readlines()

    lines[0] = 'site_name: {}\n'.format(args.project_name)

    with open(project_path/'mkdocs.yml', 'w') as f:
        f.writelines(lines)

    os.system('cd {} && mkdocs build > /dev/null'.format(
        args.project_name
    ))

    # User may want to include a showcase project as tutorial
    example_project = False
    if 'y' in input('Include example project showcasing Sphinx\
                     and autodocs? (y/n) '):
        example_project = True
        copytree(file_path / 'example_project',
                 project_path / 'example_project')
        static = project_path / 'example_project' / 'source'
        static /= '_static'
        static.mkdir()
        os.system(
            'cd {} && mkinx build -F -p example_project > /dev/null'.format(
                args.project_name
            ))
        print(
            '\n\n  The "RuntimeWarning: numpy.dtype size changed [...]"',
            'warning is expected')
        print(bcolors.OKBLUE,
              ' {}/{} created as a showcase of how mkinx works'.format(
                  args.project_name, 'example_project'
              ),
              bcolors.ENDC)
    if not example_project:
        print('\n')
    print('\n', bcolors.OKGREEN, 'Succes!', bcolors.ENDC,
          'You can now start your Docs in ./{}\n'.format(args.project_name),
          bcolors.HEADER, '$ cd ./{}'.format(
              args.project_name
          ), bcolors.ENDC)
    print('  Start the server from within your Docs to see them \n  (default',
          'port is 8443 but you can change it with the -s flag):')
    print(bcolors.HEADER, ' {} $ mkinx serve\n'.format(args.project_name),
          bcolors.ENDC)


def version(args):
    if args.version:
        print(__VERSION__)
