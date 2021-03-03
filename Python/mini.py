#!/usr/bin/python3
# Minifies files into printf statements for easy transport and scripting.
#
# Usage:
#   ./mini.py <max_len> <target_file> [print_output]
#
# Example:
#   ./mini.py 25 mycomplexscript.sh
#   ./mini.py 80 /etc/systemd/journald.conf /opt/journald.conf
#
# Copyright (C) 2020 iDigitalFlame
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

from sys import exit, argv, stderr

if len(argv) < 3:
    print("%s <len> <file> [pipe>]" % argv[0])
    exit(1)

try:
    delim = int(argv[1])
except ValueError as err:
    print(str(err), file=stderr)
    exit(1)

try:
    source_handle = open(str(argv[2]), "r")
    source = source_handle.read()
    source_handle.close()
    del source_handle
except OSError as err:
    print(str(err), file=stderr)
    exit(1)

if len(argv) >= 4:
    output = ' >> "%s"' % str(argv[3])
else:
    output = ""

last = None
current = 0
block = list()
result = list()

for c in source:
    if current >= delim:
        result.append("".join(block))
        block.clear()
        current = 0
    if c == "\n":
        block.append("\\n")
    elif c == "\t":
        block.append("\\t")
    elif c == "\\":
        block.append("\\\\")
    elif c == "'":
        block.append("'\\''")
    elif c == "%":
        block.append("%%")
    else:
        block.append(c)
    current += 1
    last = c

if len(block) > 0:
    result.append("".join(block))

del last
del block
del current

for b in result:
    print(f"printf '{b}'{output}")

exit(0)
