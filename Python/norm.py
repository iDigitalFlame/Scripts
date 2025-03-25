#!/usr/bin/python3
#
# Copyright (C) 2020 - 2025 iDigitalFlame
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
from re import compile
from sys import argv, exit, stderr
from os.path import isdir, basename, join, isfile, splitext, abspath, exists, dirname


def _scan(src, prefix=""):
    g = glob(join(abspath(src), "**"), recursive=False)
    if len(prefix) > 0:
        r = compile(f"^{prefix}(?P<num>[0-9]+)\\..*$")
    else:
        r = compile("^(?P<num>[0-9]+)\\..*$")
    e = list()
    for f in g:
        if f.endswith("desktop.ini"):
            continue
        v = r.match(basename(f))
        if v is None:
            continue
        e.append((int(v.group("num")), f))
        del v
    del g
    e.sort(key=lambda x: x[0])
    for x in range(0, len(e)):
        if x + 1 != e[x][0]:
            return (x + 1, e[x:])
    return (None, None)


def _move(idx, ent, prefix=""):
    m = ent[0][0] - idx
    for i, f in ent:
        if not isfile(f):
            continue
        _, e = splitext(basename(f))
        n = join(dirname(f), f"{prefix}{i - m}{e.lower()}")
        del e
        if exists(n):
            raise IOError(f'not overriting existing file "{n}"')
        print(f'Moving "{f}" to "{n}"..')
        rename(f, n)
        del n
    del m


if __name__ == "__main__":
    if len(argv) < 2:
        print(f"{argv[0]} [prefix] <path> ")
        exit(2)

    if len(argv) >= 3:
        prefix, target = f"{argv[1]}-", argv[2]
    else:
        prefix, target = "", argv[1]

    if not isdir(target):
        print(f'Path "{target}" does not exist or is not a directory!', file=stderr)
        exit(1)

    try:
        while True:
            i, e = _scan(target, prefix)
            if i is None or e is None:
                break
            print(f"Broken Chain at Index {i} Found!")
            _move(i, e, prefix)
    except OSError as err:
        print(f"Error during move: {err}!", file=stderr)
        exit(1)
