def precise(lexer, precise_token, parent_token):
    # Due to a pygments bug*, custom tokens will look bad
    # on outside styles. Until it is fixed on upstream, we'll
    # convey whether the client is using pie style or not
    # through precise option and return more precise tokens
    # depending on it's value.
    #
    # [0]: https://github.com/pygments/pygments/issues/1986
    if precise_token is None or not lexer.options.get("precise"):
        return parent_token
    else:
        return precise_token
