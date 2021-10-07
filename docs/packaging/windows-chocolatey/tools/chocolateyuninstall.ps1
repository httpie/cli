$ErrorActionPreference = 'Stop';
py -m pip uninstall -y $env:ChocolateyPackageName --disable-pip-version-check
