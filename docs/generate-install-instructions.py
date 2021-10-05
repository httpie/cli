import sys
from pathlib import Path
from typing import Dict

import yaml

# Types
Database = Dict[str, str]

# Files
HERE = Path(__file__).parent
DTB_FILE = HERE / 'packaging.yml'
DOC_FILE = HERE / 'README.md'

# Database keys
DTB_KEY_DOC_STRUCTURE = 'docs-structure'
DTB_KEY_TOOLS = 'tools'

# Markers in-between content will be put.
MARKER_START = '<!-- Auto-generation on -->'
MARKER_END = '<!-- Auto-generation off -->'

# Mardown templates
MD_SECTION_TPL = '''### {section}

'''
MD_TOOL_TPL = '''#### {name}

HTTPie can be installed *via* [{tool}]({tool_url}):

```bash
{cmds_install}
```

And to upgrade to the latest available version:

```bash
{cmds_upgrade}
```

'''


def generate_documentation() -> str:
    database = load_database()
    content = []
    for section in database[DTB_KEY_DOC_STRUCTURE]:
        content.append(generate_documentation_section(section, database))
    return ''.join(content)


def generate_documentation_section(section, database: Database) -> str:
    content = MD_SECTION_TPL.format(section=section)
    for tool in database[DTB_KEY_DOC_STRUCTURE][section]:
        details = database[DTB_KEY_TOOLS][tool]
        tool_url = (
            details['links'].get('installation')
            or details['links'].get('project')
            or details['links']['homepage']
        )
        content += MD_TOOL_TPL.format(
            name=details['title'],
            cmds_install='\n'.join(f'$ {cmd}' for cmd in details['commands']['install']),
            cmds_upgrade='\n'.join(f'$ {cmd}' for cmd in details['commands']['update']),
            tool=details['name'],
            tool_url=tool_url,
        )
    return content


def load_database() -> Database:
    return yaml.safe_load(DTB_FILE.read_text(encoding='utf-8'))


def load_doc_file() -> str:
    return DOC_FILE.read_text(encoding='utf-8')


def save_doc_file(content: str) -> bool:
    current_doc = load_doc_file()
    marker_start = current_doc.find(MARKER_START) + len(MARKER_START) + 2
    marker_end = current_doc.find(MARKER_END, marker_start)
    updated_doc = (
        current_doc[:marker_start]
        + content
        + current_doc[marker_end:]
    )
    if current_doc != updated_doc:
        DOC_FILE.write_text(updated_doc, encoding='utf-8')
        return True
    return False


def main() -> int:
    content = generate_documentation()
    return int(save_doc_file(content))


if __name__ == '__main__':
    sys.exit(main())
