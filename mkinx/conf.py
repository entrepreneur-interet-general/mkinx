# Version string
__VERSION__ = '0.1.6'

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
