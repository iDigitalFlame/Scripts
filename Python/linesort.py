#!/usr/bin/python3
# Copyright (C) 2020 - 2022 iDigitalFlame
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

from sys import exit, stderr, argv, stdout


if len(argv) < 2:
    print(f"{argv[0]} <file> [output]", file=stderr)
    exit(1)


with open(argv[1], "r") as f:
    data = f.read()
if not isinstance(data, str) or len(data) == 0:
    print(f'File "{argv[1]}" is empty.')
    exit(0)

out = stdout
if len(argv) == 3:
    out = open(argv[2], "w")

sep = None
length = 0
padding = 0
values = dict()
entries = list()
comments = list()

mx = 0
mxt = None
cm = list()
sl = list()
pl = dict()


for line in data.split("\n"):
    e = line.strip()
    if len(e) == 0:
        continue
    if len(e) >= 1 and (e[0] == "#" or e[0] == ";"):
        comments.append(e)
        continue
    if len(e) >= 2 and e[0] == "/" and e[1] == "/":
        comments.append(e)
        continue
    if sep is None:
        if "," in e:
            print('[+] Set seperator to ",".', file=stderr)
            sep = ","
        elif "=" in e:
            print('[+] Set seperator to "=".', file=stderr)
            sep = "="
    i = e.find(sep)
    if i is None or i < 0:
        entries.append(e)
        continue
    p = e.split(sep)
    if p is None or len(p) == 0:
        entries.append(p)
        continue
    length = max(i, length)
    n = p[0].strip()
    values[n] = sep.join(p[1:]).strip()
    entries.append(n)
    del n
    del p
    del i
    del e

entries.sort(key=lambda item: (item, len(item)))

if length > 0:
    padding = (length // 4) * 4
    if padding < length:
        length = padding + 4
    print(
        f'[+] Detected delimiter "{sep}" with max line length of "{length}"',
        file=stderr,
    )

for n in comments:
    print(comments, file=out)

for n in entries:
    if sep is None:
        print(n, file=out)
        continue
    if n not in values:
        v = n.split(sep)
        if v is None or len(v) < 2:
            print(n, file=out)
            continue
        print(f"{v[0].ljust(padding)}{sep} {sep.join(v[1:])}", file=out)
        continue
    print(f"{n.ljust(padding)}{sep} {values[n]}", file=out)

out.close()
