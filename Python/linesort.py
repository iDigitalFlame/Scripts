#!/usr/bin/python3
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

from sys import exit, stderr, argv


def _sort(contents, out=None):
    d = contents.split("\n")
    c, e = list(), list()
    s, m = None, 0
    v = dict()
    k = False
    for x in d:
        r = x.strip()
        if len(r) == 0:
            continue
        if k:
            c.append(r)
            if len(r) >= 2 and r[-1] == "/" and r[-2] == "*":
                k = False
            continue
        if len(r) >= 1 and (r[0] == "#" or r[0] == ";"):
            c.append(r)
            continue
        if len(r) >= 2 and r[0] == "/" and r[1] == "/":
            c.append(r)
            continue
        if len(r) >= 2 and r[0] == "/" and r[1] == "*":
            c.append(r)
            k = True
            continue
        if s is None:
            if "," in r:
                print('[+] Auto-detected seperator as ",".', file=stderr)
                s = ","
            elif "=" in r:
                print('[+] Auto-detected seperator as "=".', file=stderr)
                s = "="
            elif ":" in r:
                print('[+] Auto-detected seperator as ":".', file=stderr)
                s = ":"
        i = r.find(s)
        if i is None or i < 0 or i + 1 >= len(r):
            e.append(r.strip())
            continue
        m = max(i, m)
        n = r[0:i].strip()
        v[n] = r[i + 1 :].strip()
        e.append(n)
        del i, n, r
    del k, d
    e.sort(key=lambda i: (i, len(i)))
    p = 0
    if m > 0:
        p = (m // 4) * 4
        if p < m:
            m = p + 4
        print(f'[+] Using delimiter "{s}" with max line length of "{m}"', file=stderr)
    for x in c:
        print(x, file=out)
    for x in e:
        if s is None or x not in v:
            print(x, file=out)
            continue
        print(f"{x.ljust(p)}{s} {v[x]}", file=out)
    del v, s, e, c, p, m


if __name__ == "__main__":
    if len(argv) < 2:
        print(f"{argv[0]} <file> [output]", file=stderr)
        exit(2)

    try:
        with open(argv[1]) as f:
            d = f.read()
    except OSError as err:
        print(f'Error reading file "{argv[1]}": {err}!', file=stderr)
        exit(1)
    if len(d) == 0:
        print(f'File "{argv[1]}" is empty!', file=stderr)
        exit(1)

    try:
        if len(argv) == 3:
            with open(argv[2], "w") as f:
                _sort(d, f)
        else:
            _sort(d)
    except Exception as err:
        print(f"Error processing file: {err}", file=stderr)
        exit(1)
