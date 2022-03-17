#!/bin/bash

set -xe

rm -f httpie.rb
http --download https://raw.githubusercontent.com/Homebrew/homebrew-core/master/Formula/httpie.rb
