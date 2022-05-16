import stat
import subprocess
from pathlib import Path
from typing import Iterator, Tuple

BUILD_DIR = Path(__file__).parent
HTTPIE_DIR = BUILD_DIR.parent.parent.parent

EXTRAS_DIR = HTTPIE_DIR / 'extras'
MAN_PAGES_DIR = EXTRAS_DIR /  'man'

SCRIPT_DIR = BUILD_DIR / Path('scripts')
HOOKS_DIR = SCRIPT_DIR / 'hooks'

DIST_DIR = BUILD_DIR / 'dist'

TARGET_SCRIPTS = {
    SCRIPT_DIR / 'http_cli.py': [],
    SCRIPT_DIR / 'httpie_cli.py': ['--hidden-import=pip'],
}


def build_binaries() -> Iterator[Tuple[str, Path]]:
    for target_script, extra_args in TARGET_SCRIPTS.items():
        subprocess.check_call(
            [
                'pyinstaller',
                '--onefile',
                '--noupx',
                '-p',
                HTTPIE_DIR,
                '--additional-hooks-dir',
                HOOKS_DIR,
                *extra_args,
                target_script,
            ]
        )

    for executable_path in DIST_DIR.iterdir():
        if executable_path.suffix:
            continue
        stat_r = executable_path.stat()
        executable_path.chmod(stat_r.st_mode | stat.S_IEXEC)
        yield executable_path.stem, executable_path


def build_packages(http_binary: Path, httpie_binary: Path) -> None:
    import httpie

    # Mapping of src_file -> dst_file
    files = [
        (http_binary, '/usr/bin/http'),
        (http_binary, '/usr/bin/https'),
        (httpie_binary, '/usr/bin/httpie'),
    ]
    files.extend(
        (man_page, f'/usr/share/man/man1/{man_page.name}')
        for man_page in MAN_PAGES_DIR.glob('*.1')
    )

    # A list of additional dependencies
    deps = [
        'python3 >= 3.7',
        'python3-pip'
    ]

    processed_deps = [
        f'--depends={dep}'
        for dep in deps
    ]
    processed_files = [
        '='.join([str(src.resolve()), dst]) for src, dst in files
    ]
    for target in ['deb', 'rpm']:
        subprocess.check_call(
            [
                'fpm',
                '--force',
                '-s',
                'dir',
                '-t',
                target,
                '--name',
                'httpie',
                '--version',
                httpie.__version__,
                '--description',
                httpie.__doc__.strip(),
                '--license',
                httpie.__licence__,
                *processed_deps,
                *processed_files,
            ],
            cwd=DIST_DIR,
        )


def main():
    binaries = dict(build_binaries())
    build_packages(binaries['http_cli'], binaries['httpie_cli'])

    # Rename http_cli/httpie_cli to http/httpie
    binaries['http_cli'].rename(DIST_DIR / 'http')
    binaries['httpie_cli'].rename(DIST_DIR / 'httpie')



if __name__ == '__main__':
    main()
