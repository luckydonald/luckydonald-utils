try:
    from gitinfo_values import __all__
except:
    __all__ = ["GIT_COMMIT", "GIT_COMMIT_SHORT", "GIT_DIRTY_PROJECT", "GIT_DIRTY_GLOBAL", "GIT_MESSAGE",
               "GIT_AUTHOR", "GIT_DATE", "GIT_HEAD", "GIT_BRANCHES", "GIT_TAGS", "VERSION_STR",
               "GIT_MODIFIED_FILES", "GIT_MODIFIED_FILES_STR"]
# end try

try:
    from gitinfo_values import GIT_COMMIT
except:
    GIT_COMMIT = None
# end try

try:
    from gitinfo_values import GIT_DIRTY_PROJECT
except:
    GIT_DIRTY_PROJECT = None
# end try

try:
    from gitinfo_values import GIT_DIRTY_GLOBAL
except:
    GIT_DIRTY_GLOBAL = None
# end try

try:
    from gitinfo_values import GIT_COMMIT_SHORT
except:
    GIT_COMMIT_SHORT = None
# end try

try:
    from gitinfo_values import GIT_MESSAGE
except:
    GIT_MESSAGE = None
# end try

try:
    from gitinfo_values import GIT_AUTHOR
except:
    GIT_AUTHOR = None
# end try

try:
    from gitinfo_values import GIT_AUTHOR
except:
    GIT_AUTHOR = None
# end try

try:
    from gitinfo_values import GIT_DATE
except:
    GIT_DATE = None
# end try

try:
    from gitinfo_values import GIT_HEAD
except:
    GIT_HEAD = None
# end try

try:
    from gitinfo_values import GIT_BRANCHES
except:
    GIT_BRANCHES = []
# end try

try:
    from gitinfo_values import GIT_TAGS
except:
    GIT_TAGS = []
# end try

try:
    from gitinfo_values import VERSION_STR
except:
    VERSION_STR = "unknown"
# end try

try:
    from gitinfo_values import GIT_MODIFIED_FILES
except:
    GIT_MODIFIED_FILES = {"added": [], "copied": [], "deleted": [], "modified": [], "renamed": [], "type_changed": [],
                          "unmerged": [], "unknown": [], "broken": [], "by_file": {}}
# end try

try:
    from gitinfo_values import GIT_MODIFIED_FILES_STR
except:
    GIT_MODIFIED_FILES_STR = ""
# end try

try:
    from teleflask.messages import HTMLMessage
    from teleflask import TBlueprint

    version_tbp = TBlueprint(__name__)


    @version_tbp.command('version')
    def cmd_version(update, text):
        return HTMLMessage('<code>{version}</code>'.format(version=escape(VERSION_STR)))
    # end def
except ImportError:
    pass
# end try

try:
    from html import escape
    from flask import Blueprint

    version_bp = Blueprint('version', __name__)


    @version_bp.route('/version/')
    def route_version():
        return VERSION_STR
    # end def
except ImportError:
    pass
# end try
