#!/bin/bash

set -xe

rm -f httpie.spec.txt
https --download src.fedoraproject.org/rpms/httpie/raw/rawhide/f/httpie.spec -o httpie.spec.txt
