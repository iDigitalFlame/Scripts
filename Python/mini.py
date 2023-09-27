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
# Copyright (C) 2020 - 2023 iDigitalFlame
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

from io import StringIO
from sys import exit, argv, stderr


def _file(path, max_len=80, output=None):
    r, k = None, False
    if isinstance(output, str) and len(output) > 0:
        t1, t2 = f' > "{output}"', f' >> "{output}"'
    else:
        t1, t2 = "", ""
    try:
        with open(path, "r") as f:
            r = f.read()
    except UnicodeDecodeError:
        y = StringIO()
        with open(path, "rb") as f:
            for c in f.read():
                y.write(f"\\x{hex(c).upper()[2:].zfill(2)}")
        r, k = y.getvalue(), True
        y.close()
        del y
    if not isinstance(r, str) or len(r) == 0:
        return print(f'printf ""{t1}')
    i = 0
    o = StringIO()
    if len(t1) > 0:
        e = [f'printf ""{t1}']
    else:
        e = list()
    for c in r:
        if i >= max_len:
            e.append(f"printf '{o.getvalue()}'{t2}")
            o.truncate(0)
            o.seek(0)
            o.flush()
            i = 0
        if c == "\n":
            o.write("\\n")
            i += 1
        elif c == "\t":
            o.write("\\t")
            i += 1
        elif c == "\\" and not k:
            o.write("\\\\")
            i += 1
        elif c == "'":
            o.write("'\\''")
            i += 3
        elif c == "%":
            o.write("%%")
            i += 1
        else:
            o.write(c)
        i += 1
    if o.tell() > 0:
        e.append(f"printf '{o.getvalue()}'{t2}")
    del t1, t2
    print("\n".join(e))
    del o, k, r, e, i


if __name__ == "__main__":
    if len(argv) < 3:
        print(f"{argv[0]} <len> <file> [target]")
        exit(2)

    try:
        m = int(argv[1])
    except ValueError:
        print(f'Invalid length value "{argv[1]}"!', file=stderr)
        exit(1)

    try:
        _file(argv[2], m, argv[3] if len(argv) == 4 else None)
    except OSError as err:
        print(f"Error processing file: {err}", file=stderr)
        exit(1)
