METHODS=("GET" "POST" "PUT" "DELETE" "HEAD" "OPTIONS" "PATCH" "TRACE" "CONNECT" )
NORMARG=1 # TO-DO: dynamically calculate this?

_http_complete() {
    local cur_word=${COMP_WORDS[COMP_CWORD]}
    local prev_word=${COMP_WORDS[COMP_CWORD - 1]}

    if [[ "$cur_word" == -* ]]; then
        _http_complete_options "$cur_word"
    else
        if (( COMP_CWORD == NORMARG + 0 )); then
            _http_complete_methods "$cur_word"
        fi
        if (( COMP_CWORD == NORMARG + 0 )); then
            _http_complete_url "$cur_word"
        fi
        if (( COMP_CWORD == NORMARG + 1 )) && [[ " ${METHODS[*]} " =~ " ${prev_word} " ]]; then
            _http_complete_url "$cur_word"
        fi
        if (( COMP_CWORD >= NORMARG + 2 )); then
            _httpie_complete_request_item "$cur_word"
        fi
        if (( COMP_CWORD >= NORMARG + 1 )) && ! [[ " ${METHODS[*]} " =~ " ${prev_word} " ]]; then
            _httpie_complete_request_item "$cur_word"
        fi
        
    fi
}

complete -o default -F _http_complete http httpie.http httpie.https https

_http_complete_methods() {
    local cur_word=$1
    local options="GET POST PUT DELETE HEAD OPTIONS PATCH TRACE CONNECT"
    COMPREPLY+=( $( compgen -W "$options" -- "$cur_word" ) )
}

_http_complete_url() {
    local cur_word=$1
    local options="http:// https://"
    COMPREPLY+=( $( compgen -W "$options" -- "$cur_word" ) )
}

_httpie_complete_request_item() {
    local cur_word=$1
    COMPREPLY+=("==" "=" ":=" ":=@")
}

_http_complete_options() {
    local cur_word=$1
    local options="--json -j --form -f --multipart --boundary --raw --compress -x --pretty --style -s --unsorted --sorted --response-charset --response-mime --format-options --print -p --headers -h --meta -m --body -b --verbose -v --all --stream -S --output -o --download -d --continue -c --quiet -q --session --session-read-only --auth -a --auth-type -A --ignore-netrc --offline --proxy --follow -F --max-redirects --max-headers --timeout --check-status --path-as-is --chunked --verify --ssl --ciphers --cert --cert-key --cert-key-pass --ignore-stdin -I --help --manual --version --traceback --default-scheme --debug "
    COMPREPLY=( $( compgen -W "$options" -- "$cur_word" ) )
}