from http import cookiejar


_LOCALHOST = 'localhost'
_LOCALHOST_SUFFIX = '.localhost'


class HTTPieCookiePolicy(cookiejar.DefaultCookiePolicy):
    def return_ok_secure(self, cookie, request):
        """Check whether the given cookie is sent to a secure host."""

        is_secure_protocol = super().return_ok_secure(cookie, request)
        if is_secure_protocol:
            return True

        # The original implementation of this method only takes secure protocols
        # (e.g., https) into account, but the latest developments in modern browsers
        # (chrome, firefox) assume 'localhost' is also a secure location. So we
        # override it with our own strategy.
        return self._is_local_host(cookiejar.request_host(request))

    def _is_local_host(self, hostname):
        # Implements the static localhost detection algorithm in firefox.
        # <https://searchfox.org/mozilla-central/rev/d4d7611ee4dd0003b492b865bc5988a4e6afc985/netwerk/dns/DNS.cpp#205-218>
        return hostname == _LOCALHOST or hostname.endswith(_LOCALHOST_SUFFIX)
