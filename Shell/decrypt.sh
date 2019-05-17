#!/bin/bash

if [ $# -ne 1 ]; then
    printf "decrypt <file>\n"
    exit 1
fi

openssl aes-256-cbc -d -a -in "$1" -out "new-$1"
