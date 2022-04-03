from typing import Any, Type, List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from httpie.sessions import Session


OLD_HEADER_STORE_WARNING = '''\
Outdated layout detected for the current session. Please consider updating it,
in order to use the latest features regarding the header layout.

For fixing the current session:

    $ httpie cli sessions upgrade {hostname} {session_id}
'''

OLD_HEADER_STORE_WARNING_FOR_NAMED_SESSIONS = '''\

For fixing all named sessions:

    $ httpie cli sessions upgrade-all
'''

OLD_HEADER_STORE_LINK = '\nSee $INSERT_LINK for more information.'


def pre_process(session: 'Session', headers: Any) -> List[Dict[str, Any]]:
    """Serialize the headers into a unified form and issue a warning if
    the session file is using the old layout."""

    is_old_style = isinstance(headers, dict)
    if is_old_style:
        normalized_headers = list(headers.items())
    else:
        normalized_headers = [
            (item['name'], item['value'])
            for item in headers
        ]

    if is_old_style:
        warning = OLD_HEADER_STORE_WARNING.format(hostname=session.bound_host, session_id=session.session_id)
        if not session.is_anonymous:
            warning += OLD_HEADER_STORE_WARNING_FOR_NAMED_SESSIONS
        warning += OLD_HEADER_STORE_LINK
        session.warn_legacy_usage(warning)

    return normalized_headers


def post_process(
    normalized_headers: List[Dict[str, Any]],
    *,
    original_type: Type[Any]
) -> Any:
    """Deserialize given header store into the original form it was
    used in."""

    if issubclass(original_type, dict):
        # For the legacy behavior, preserve the last value.
        return {
            item['name']: item['value']
            for item in normalized_headers
        }
    else:
        return normalized_headers


def fix_layout(session: 'Session', *args, **kwargs) -> None:
    from httpie.sessions import materialize_headers

    if not isinstance(session['headers'], dict):
        return None

    session['headers'] = materialize_headers(session['headers'])
