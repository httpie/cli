# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *


class Httpie(PythonPackage):
    """Modern command line HTTP client."""

    homepage = "https://httpie.io/"
    pypi = "httpie/httpie-2.5.0.tar.gz"

    version('2.5.0', sha256='fe6a8bc50fb0635a84ebe1296a732e39357c3e1354541bf51a7057b4877e47f9')
    version('0.9.9', sha256='f1202e6fa60367e2265284a53f35bfa5917119592c2ab08277efc7fffd744fcb')
    version('0.9.8', sha256='515870b15231530f56fe2164190581748e8799b66ef0fe36ec9da3396f0df6e1')

    variant('socks', default=True,
            description='Enable SOCKS proxy support')

    depends_on('py-setuptools', type=('build', 'run'))
    depends_on('py-defusedxml', type=('build', 'run'))
    depends_on('py-pygments', type=('build', 'run'))
    depends_on('py-requests', type=('build', 'run'))
    depends_on('py-requests-toolbelt', type=('build', 'run'))
    depends_on('py-pysocks', type=('build', 'run'), when="+socks")
    # Concretization problem breaks this.  Unconditional for now...
    # https://github.com/spack/spack/issues/3628
    # depends_on('py-argparse@1.2.1:', type=('build', 'run'),
    #            when='^python@:2.6,3.0:3.1')
    depends_on('py-argparse@1.2.1:', type=('build', 'run'), when='^python@:2.6')
