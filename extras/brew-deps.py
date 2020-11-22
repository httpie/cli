#!/usr/bin/env python3
"""
Generate Ruby code with URLs and file hashes for packages from PyPi
(i.e., httpie itself as well as its dependencies) to be included
in the Homebrew formula after a new release of HTTPie has been published
on PyPi.

<https://github.com/Homebrew/homebrew-core/blob/master/Formula/httpie.rb>

"""
import hashlib
import requests


PACKAGES = [
    'httpie',
    'Pygments',
    'requests',
    'requests-toolbelt',
    'certifi',
    'urllib3',
    'idna',
    'chardet',
    'PySocks',
]


def get_package_meta(package_name):
    api_url = f'https://pypi.python.org/pypi/{package_name}/json'
    resp = requests.get(api_url).json()
    hasher = hashlib.sha256()
    for release in resp['urls']:
        download_url = release['url']
        if download_url.endswith('.tar.gz'):
            hasher.update(requests.get(download_url).content)
            return {
                'name': package_name,
                'url': download_url,
                'sha256': hasher.hexdigest(),
            }
    else:
        raise RuntimeError(f'{package_name}: download not found: {resp}')


def main():
    package_meta_map = {
        package_name: get_package_meta(package_name)
        for package_name in PACKAGES
    }
    httpie_meta = package_meta_map.pop('httpie')
    print()
    print('  url "{url}"'.format(url=httpie_meta['url']))
    print('  sha256 "{sha256}"'.format(sha256=httpie_meta['sha256']))
    print()
    for dep_meta in package_meta_map.values():
        print('  resource "{name}" do'.format(name=dep_meta['name']))
        print('    url "{url}"'.format(url=dep_meta['url']))
        print('    sha256 "{sha256}"'.format(sha256=dep_meta['sha256']))
        print('  end')
        print('')


if __name__ == '__main__':
    main()
