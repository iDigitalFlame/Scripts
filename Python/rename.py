#!/usr/bin/python3
#
# Copyright (C) 2022 - 2023 iDigitalFlame
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

from glob import glob
from os import rename
from sys import argv, exit
from os.path import isfile, isdir, join, basename, dirname, splitext


def _strip(p, f, sort=False):
    b = basename(f)
    if len(b) == 0:
        return f
    n, x = splitext(b)
    if sort:
        return int(n[len(p) + 1 :])
    return int(n[len(p) + 1 :]), x


if len(argv) < 4:
    print(f"{argv[0]} <prefix> <dir> <gap> [start]")
    exit(1)

start, gap = 0, int(argv[3])
dir, prefix = argv[2], argv[1]

if gap <= 0:
    print("Renamed 0 entries.")
    exit(0)

if len(argv) > 4:
    start = int(argv[4])
    if start < 0:
        start = 0

if not isdir(dir):
    print(f'directory "{dir}" does not exist!')
    exit(1)

e = glob(join(dir, "*"))
if len(e) == 0:
    print("Renamed 0 entries.")
    exit(0)

v = list()
for i in e:
    b = basename(i)
    if not b.startswith(f"{prefix}-"):
        continue
    v.append(i)
if len(v) == 0:
    print("Renamed 0 entries.")
    exit(0)
v.sort(key=lambda x: _strip(prefix, x, True), reverse=True)

r = list()
for i in v:
    x = _strip(prefix, i, True)
    if x < start:
        continue
    r.append(i)

d = dirname(dir)
for i in r:
    n, x = _strip(prefix, i)
    k = f"{prefix}-{n + gap}{x}"
    j = join(d, k)
    del k, n, x
    if isfile(j):
        raise OSError(f'not overriting existing file "{j}"')
    if not isfile(i):
        raise OSError(f'missing file "{i}"')
    print(f'"{i}" => "{j}"')
    rename(i, j)
    del j

print(f"Renamed {len(r)} entries.")
