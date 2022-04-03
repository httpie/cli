import argparse
from typing import Any, Type, List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from httpie.sessions import Session


INSECURE_COOKIE_JAR_WARNING = '''\
Outdated layout detected for the current session. Please consider updating it,
in order to not get affected by potential security problems.

For fixing the current session:

    With binding all cookies to the current host (secure):
        $ httpie cli sessions upgrade --bind-cookies {hostname} {session_id}

    Without binding cookies (leaving them as is) (insecure):
        $ httpie cli sessions upgrade {hostname} {session_id}
'''


INSECURE_COOKIE_JAR_WARNING_FOR_NAMED_SESSIONS = '''\

For fixing all named sessions:

    With binding all cookies to the current host (secure):
        $ httpie cli sessions upgrade-all --bind-cookies

    Without binding cookies (leaving them as is) (insecure):
        $ httpie cli sessions upgrade-all
'''

INSECURE_COOKIE_SECURITY_LINK = '\nSee https://pie.co/docs/security for more information.'


def pre_process(session: 'Session', cookies: Any) -> List[Dict[str, Any]]:
    """Load the given cookies to the cookie jar while maintaining
    support for the old cookie layout."""

    is_old_style = isinstance(cookies, dict)
    if is_old_style:
        normalized_cookies = [
            {
                'name': key,
                **value
            }
            for key, value in cookies.items()
        ]
    else:
        normalized_cookies = cookies

    should_issue_warning = is_old_style and any(
        cookie.get('domain', '') == ''
        for cookie in normalized_cookies
    )

    if should_issue_warning:
        warning = INSECURE_COOKIE_JAR_WARNING.format(hostname=session.bound_host, session_id=session.session_id)
        if not session.is_anonymous:
            warning += INSECURE_COOKIE_JAR_WARNING_FOR_NAMED_SESSIONS
        warning += INSECURE_COOKIE_SECURITY_LINK
        session.warn_legacy_usage(warning)

    return normalized_cookies


def post_process(
    normalized_cookies: List[Dict[str, Any]],
    *,
    original_type: Type[Any]
) -> Any:
    """Convert the cookies to their original format for
    maximum compatibility."""

    if issubclass(original_type, dict):
        return {
            cookie.pop('name'): cookie
            for cookie in normalized_cookies
        }
    else:
        return normalized_cookies


def fix_layout(session: 'Session', hostname: str, args: argparse.Namespace) -> None:
    if not isinstance(session['cookies'], dict):
        return None

    session['cookies'] = [
        {
            'name': key,
            **value
        }
        for key, value in session['cookies'].items()
    ]
    for cookie in session.cookies:
        if cookie.domain == '':
            if args.bind_cookies:
                cookie.domain = hostname
            else:
                cookie._rest['is_explicit_none'] = True
