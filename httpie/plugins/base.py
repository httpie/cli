class AuthPlugin(object):
    """
    Base auth plugin class.

    See <https://github.com/jkbr/httpie-ntlm> for an example auth plugin.

    """

    # The value that should be passed to --auth-type
    # to use this auth plugin. Eg. "my-auth"
    auth_type = None

    # The name of the plugin, eg. "My auth".
    name = None

    # Optional short description. Will be be shown in the help
    # under --auth-type.
    description = None

    # This be set automatically once the plugin has been loaded.
    package_name = None

    def get_auth(self, username, password):
        """
        Return a ``requests.auth.AuthBase`` subclass instance.

        """
        raise NotImplementedError()
