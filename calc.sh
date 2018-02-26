#!/bin/bash
HEADER=$(head -n 1 $1)
BRANCHES=$(echo $HEADER | cut -d ' ' -f 2)
TAKEN=$(($(sort -u $1 | wc -l)-1))
RATIO=$(echo "print $TAKEN/$BRANCHES." | python)
echo "Total Branches: $BRANCHES"
echo "Branches Taken: $TAKEN"
echo "Coverage Ratio: $RATIO"

