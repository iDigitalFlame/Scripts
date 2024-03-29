#!/bin/bash
# Copyright (C) 2016 - 2023 iDigitalFlame
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

# Enable Strict Mode
set -euo pipefail
IFS=$'\n\t'

if [ $# -ne 1 ]; then
    echo "Usage: pfx2pem <pfx>"
    exit 1
fi

c="$1"
printf "Password for PFX: "
read -r -s cpa
printf "\n"

openssl pkcs12 -in "$c" -nocerts -out "/tmp/$c.pem" -nodes -password file:<(printf "%s" "$cpa")
openssl pkcs12 -in "$c" -nokeys -out "$c.pem" -password file:<(printf "%s" "$cpa")
openssl rsa -in "/tmp/$c.pem" -out "$c.key"

rm "/tmp/$c.pem" 2> /dev/null
exit 0
