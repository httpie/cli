#!/usr/bin/env bash


_http_complete() {
    local cur_word=${COMP_WORDS[COMP_CWORD]}
    local prev_word=${COMP_WORDS[COMP_CWORD - 1]}

    if [[ "$cur_word" == -*  ]]; then
        _http_complete_options "$cur_word"
    fi
}

complete -o default -F _http_complete http

_http_complete_options() {
    local cur_word=$1
    local options="-j --json -f --form --pretty -s --style -p --print
    -v --verbose -h --headers -b --body -S --stream -o --output -d --download
    -c --continue --session --session-read-only -a --auth --auth-type --proxy
    --follow --verify --cert --cert-key --timeout --check-status --ignore-stdin
    --help --version --traceback --debug"
    COMPREPLY=( $( compgen -W "$options" -- "$cur_word" ) )
}
