#!/bin/bash

if [ $# -ne 1 ]; then
  printf "encrypt <file>\n"
  exit 1
fi

openssl aes-256-cbc -a -in "$1" -out "$1.enc"
