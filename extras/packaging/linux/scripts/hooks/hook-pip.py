from pathlib import Path
from PyInstaller.utils.hooks import collect_all

def hook(hook_api):
    for pkg in [
        'pip',
        'setuptools',
        'distutils',
        'pkg_resources'
    ]:
        datas, binaries, hiddenimports = collect_all(pkg)
        hook_api.add_datas(datas)
        hook_api.add_binaries(binaries)
        hook_api.add_imports(*hiddenimports)
