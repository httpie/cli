import ssl


_SSL_VERSION_ARG_MAPPING = {
    'ssl2.3': 'PROTOCOL_SSLv23',
    'ssl3': 'PROTOCOL_SSLv3',
    'tls1': 'PROTOCOL_TLSv1',
    'tls1.1': 'PROTOCOL_TLSv1_1',
    'tls1.2': 'PROTOCOL_TLSv1_2',
}


SSL_VERSION_ARG_MAPPING = dict(
    (cli_arg, getattr(ssl, ssl_constant))
    for cli_arg, ssl_constant in _SSL_VERSION_ARG_MAPPING.items()
    if hasattr(ssl, ssl_constant)
)
