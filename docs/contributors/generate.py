"""
Generate snippets to copy-paste.
"""
import sys

from jinja2 import Template

from fetch import HERE, load_awesome_people

TPL_FILE = HERE / 'snippet.jinja2'

HTTPIE_TEAM = {
    'claudiatd',
    'jakubroztocil',
    'jkbr',
    'isidentical'
}

BOT_ACCOUNTS = {
    'dependabot-sr'
}

IGNORE_ACCOUNTS = HTTPIE_TEAM | BOT_ACCOUNTS


def generate_snippets(release: str) -> str:
    people = load_awesome_people()
    contributors = {
        name: details
        for name, details in people.items()
        if details['github'] not in IGNORE_ACCOUNTS
        and (release in details['committed'] or release in details['reported'])
    }

    template = Template(source=TPL_FILE.read_text(encoding='utf-8'))
    output = template.render(contributors=contributors, release=release)
    print(output)
    return 0


if __name__ == '__main__':
    ret = 1
    try:
        ret = generate_snippets(sys.argv[1])
    except (IndexError, TypeError):
        ret = 2
        print(f'''
Generate snippets for contributors to a release.

Usage:
    python {sys.argv[0]} {sys.argv[0]} <RELEASE>
''')
    sys.exit(ret)
