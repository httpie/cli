from httpie.manager.tasks.sessions import cli_sessions
from httpie.manager.tasks.export_args import cli_export_args
from httpie.manager.tasks.plugins import cli_plugins

CLI_TASKS = {
    'sessions': cli_sessions,
    'export-args': cli_export_args,
    'plugins': cli_plugins,
}
