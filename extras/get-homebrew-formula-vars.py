#!/usr/bin/env python
"""
Generate URLs and file hashes to be included in the Homebrew formula
after a new release of HTTPie is published on PyPi.

https://github.com/Homebrew/homebrew-core/blob/master/Formula/httpie.rb

"""
import hashlib
import requests


PACKAGES = [
    'httpie',
    'requests',
    'pygments',
]


def get_info(package_name):
    api_url = 'https://pypi.python.org/pypi/{}/json'.format(package_name)
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
        raise RuntimeError(
            '{}: download not found: {}'.format(package_name, resp))


packages = {
    package_name: get_info(package_name) for package_name in PACKAGES
}


httpie_info = packages.pop('httpie')
print("""
  url "{url}"
  sha256 "{sha256}"
""".format(**httpie_info))


for package_info in packages.values():
    print("""
  resource "{name}" do
    url "{url}"
    sha256 "{sha256}"
  end""".format(**package_info))
