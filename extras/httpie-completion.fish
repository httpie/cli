function __fish_httpie_styles
    printf '%s\n' abap algol algol_nu arduino auto autumn borland bw colorful default emacs friendly fruity gruvbox-dark gruvbox-light igor inkpot lovelace manni material monokai murphy native paraiso-dark paraiso-light pastie perldoc pie pie-dark pie-light rainbow_dash rrt sas solarized solarized-dark solarized-light stata stata-dark stata-light tango trac vim vs xcode zenburn
end

function __fish_httpie_mime_types
    test -r /usr/share/mime/types && cat /usr/share/mime/types
end

function __fish_httpie_print_args
    set -l arg (commandline -t)
    string match -qe H "$arg" || echo -e $arg"H\trequest headers"
    string match -qe B "$arg" || echo -e $arg"B\trequest body"
    string match -qe h "$arg" || echo -e $arg"h\tresponse headers"
    string match -qe b "$arg" || echo -e $arg"b\tresponse body"
    string match -qe m "$arg" || echo -e $arg"m\tresponse metadata"
end

function __fish_httpie_auth_types
    echo -e "basic\tBasic HTTP auth"
    echo -e "digest\tDigest HTTP auth"
    echo -e "bearer\tBearer HTTP Auth"
end

function __fish_http_verify_options
    echo -e "yes\tEnable cert verification"
    echo -e "no\tDisable cert verification"
end


# Predefined Content Types

complete -c http -s j -l json         -d 'Data items are serialized as a JSON object'
complete -c http -s f -l form         -d 'Data items are serialized as form fields'
complete -c http      -l multipart    -d 'Always sends a multipart/form-data request'
complete -c http      -l boundary  -x -d 'Custom boundary string for multipart/form-data requests'
complete -c http      -l raw       -x -d 'Pass raw request data without extra processing'


# Content Processing Options

complete -c http -s x -l compress -d 'Content compressed with Deflate algorithm'


# Output Processing

complete -c http      -l pretty           -xa "all colors format none"     -d 'Controls output processing'
complete -c http -s s -l style            -xa "(__fish_httpie_styles)"     -d 'Output coloring style'
complete -c http      -l unsorted                                          -d 'Disables all sorting while formatting output'
complete -c http      -l sorted                                            -d 'Re-enables all sorting options while formatting output'
complete -c http      -l response-charset -x                               -d 'Override the response encoding'
complete -c http      -l response-mime    -xa "(__fish_httpie_mime_types)" -d 'Override the response mime type for coloring and formatting'
complete -c http      -l format-options   -x                               -d 'Controls output formatting'


# Output Options

complete -c http -s p -l print         -xa "(__fish_httpie_print_args)" -d 'String specifying what the output should contain'
complete -c http -s h -l headers                                        -d 'Print only the response headers'
complete -c http -s m -l meta                                           -d 'Print only the response metadata'
complete -c http -s b -l body                                           -d 'Print only the response body'
complete -c http -s v -l verbose                                        -d 'Print the whole request as well as the response'
complete -c http      -l all                                            -d 'Show any intermediary requests/responses'
complete -c http -s S -l stream                                         -d 'Always stream the response body by line'
complete -c http -s o -l output        -F                               -d 'Save output to FILE'
complete -c http -s d -l download                                       -d 'Download a file'
complete -c http -s c -l continue                                       -d 'Resume an interrupted download'
complete -c http -s q -l quiet                                          -d 'Do not print to stdout or stderr'


# Sessions

complete -c http -l session           -F -d 'Create, or reuse and update a session'
complete -c http -l session-read-only -F -d 'Create or read a session without updating it'


# Authentication

complete -c http -s a -l auth         -x                               -d 'Username and password for authentication'
complete -c http -s A -l auth-type    -xa "(__fish_httpie_auth_types)" -d 'The authentication mechanism to be used'
complete -c http      -l ignore-netrc                                  -d 'Ignore credentials from .netrc'


# Network

complete -c http      -l offline          -d 'Build the request and print it but don\'t actually send it'
complete -c http      -l proxy         -x -d 'String mapping protocol to the URL of the proxy'
complete -c http -s F -l follow           -d 'Follow 30x Location redirects'
complete -c http      -l max-redirects -x -d 'Set maximum number of redirects'
complete -c http      -l max-headers   -x -d 'Maximum number of response headers to be read before giving up'
complete -c http      -l timeout       -x -d 'Connection timeout in seconds'
complete -c http      -l check-status     -d 'Error with non-200 HTTP status code'
complete -c http      -l path-as-is       -d 'Bypass dot segment URL squashing'
complete -c http      -l chunked          -d 'Enable streaming via chunked transfer encoding'


# SSL

complete -c http -l verify        -xa "(__fish_http_verify_options)" -d 'Enable/disable cert verification'
complete -c http -l ssl           -x                                 -d 'Desired protocol version to use'
complete -c http -l ciphers       -x                                 -d 'String in the OpenSSL cipher list format'
complete -c http -l cert          -F                                 -d 'Client side SSL certificate'
complete -c http -l cert-key      -F                                 -d 'Private key to use with SSL'
complete -c http -l cert-key-pass -x                                 -d 'Passphrase for the given private key'


# Troubleshooting

complete -c http -s I -l ignore-stdin      -d 'Do not attempt to read stdin'
complete -c http      -l help              -d 'Show help'
complete -c http      -l manual            -d 'Show the full manual'
complete -c http      -l version           -d 'Show version'
complete -c http      -l traceback         -d 'Prints exception traceback should one occur'
complete -c http      -l default-scheme -x -d 'The default scheme to use'
complete -c http      -l debug             -d 'Show debugging output'


# Alias for https to http

function https --wraps http
        http $argv;
end
