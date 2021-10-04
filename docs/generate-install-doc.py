import sys
from pathlib import Path
from typing import Dict

import yaml
from yaml.cyaml import CDumper

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
MD_SECTION_FORMAT = '''### {section}

'''
MD_TOOL_FORMAT = '''#### {name}

```bash
{cmds_install}
```

'''


def generate_documentation() -> str:
    """"""
    database = load_database()
    content = []
    for section in database[DTB_KEY_DOC_STRUCTURE]:
        content.append(generate_documentation_section(section, database))
    return ''.join(content)


def generate_documentation_section(section, database: Database) -> str:
    """"""
    content = MD_SECTION_FORMAT.format(section=section)
    for tool in database[DTB_KEY_DOC_STRUCTURE][section]:
        details = database[DTB_KEY_TOOLS][tool]
        name = details['name']
        if ' — ' in name:
            name = name.split(' — ')[1]
        content += MD_TOOL_FORMAT.format(
            name=name,
            cmds_install='\n'.join(f'$ {cmd}' for cmd in details['commands']['install']))
    return content


def load_database() -> Database:
    """"""
    return yaml.safe_load(DTB_FILE.read_text(encoding='utf-8'))


def load_doc_file() -> str:
    """"""
    return DOC_FILE.read_text(encoding='utf-8')


def save_doc_file(content: str) -> None:
    """"""
    current_doc = load_doc_file()
    marker_start = current_doc.find(MARKER_START) + len(MARKER_START) + 2
    marker_end = current_doc.find(MARKER_END, marker_start)
    updated_doc = (
        current_doc[:marker_start]
        + content
        + current_doc[marker_end:]
    )
    return DOC_FILE.write_text(updated_doc, encoding='utf-8')


def main() -> int:
    """"""
    content = generate_documentation()
    save_doc_file(content)
    return 0


if __name__ == '__main__':
    sys.exit(main())
