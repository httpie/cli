from httpie.manager.tasks.sessions import cli_sessions
from httpie.manager.tasks.export_args import cli_export_args
from httpie.manager.tasks.plugins import cli_plugins
from httpie.manager.tasks.check_updates import cli_check_updates

CLI_TASKS = {
    'sessions': cli_sessions,
    'export-args': cli_export_args,
    'plugins': cli_plugins,
    'check-updates': cli_check_updates
}
