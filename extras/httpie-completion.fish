function __fish_httpie_auth_types
  echo "basic"\t"Basic HTTP auth"
  echo "digest"\t"Digest HTTP auth"
end

function __fish_httpie_styles
  echo "autumn"
  echo "borland"
  echo "bw"
  echo "colorful"
  echo "default"
  echo "emacs"
  echo "friendly"
  echo "fruity"
  echo "igor"
  echo "manni"
  echo "monokai"
  echo "murphy"
  echo "native"
  echo "paraiso-dark"
  echo "paraiso-light"
  echo "pastie"
  echo "perldoc"
  echo "rrt"
  echo "solarized"
  echo "tango"
  echo "trac"
  echo "vim"
  echo "vs"
  echo "xcode"
end

complete -x -c http -s s -l style        -d 'Output coloring style (default is "monokai")' -A -a '(__fish_httpie_styles)'
complete    -c http -s f -l form         -d 'Data items from the command line are serialized as form fields'
complete    -c http -s j -l json         -d '(default) Data items from the command line are serialized as a JSON object'
complete -x -c http      -l pretty       -d 'Controls output processing' -a "all colors format none" -A
complete -x -c http -s p -l print        -d 'String specifying what the output should contain'
complete    -c http -s v -l verbose      -d 'Print the whole request as well as the response'
complete    -c http -s h -l headers      -d 'Print only the response headers'
complete    -c http -s b -l body         -d 'Print only the response body'
complete    -c http -s S -l stream       -d 'Always stream the output by line'
complete    -c http -s o -l output       -d 'Save output to FILE'
complete    -c http -s d -l download     -d 'Do not print the response body to stdout'
complete    -c http -s c -l continue     -d 'Resume an interrupted download'
complete -x -c http      -l session      -d 'Create, or reuse and update a session'
complete -x -c http -s a -l auth         -d 'If only the username is provided (-a username), HTTPie will prompt for the password'
complete -x -c http      -l auth-type    -d 'The authentication mechanism to be used' -a '(__fish_httpie_auth_types)' -A
complete -x -c http      -l proxy        -d 'String mapping protocol to the URL of the proxy'
complete    -c http      -l follow       -d 'Allow full redirects'
complete -x -c http      -l verify       -d 'SSL cert verification'
complete    -c http      -l cert         -d 'SSL cert'
complete    -c http      -l cert-key     -d 'Private SSL cert key'
complete -x -c http      -l timeout      -d 'Connection timeout in seconds'
complete    -c http      -l check-status -d 'Error with non-200 HTTP status code'
complete    -c http      -l ignore-stdin -d 'Do not attempt to read stdin'
complete    -c http      -l help         -d 'Show help'
complete    -c http      -l version      -d 'Show version'
complete    -c http      -l traceback    -d 'Prints exception traceback should one occur'
complete    -c http      -l debug        -d 'Show debugging information'
