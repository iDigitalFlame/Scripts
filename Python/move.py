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

from glob import glob
from os import rename
from re import compile
from sys import argv, exit, stderr
from os.path import isdir, basename, join, isfile, splitext, abspath, exists, dirname


def _move(src, prefix=""):
    g = glob(join(abspath(src), "**"), recursive=False)
    if len(prefix) > 0:
        r = compile(f"^{prefix}(?P<num>[0-9]+)\\..*$")
    else:
        r = compile("^(?P<num>[0-9]+)\\..*$")
    u, m = list(), list()
    for f in g:
        v = r.match(basename(f))
        if v is None:
            m.append(f)
            continue
        u.append(int(v.group("num")))
    del r
    u.sort()
    i = 0
    for f in m:
        while i in u:
            i += 1
        if not isfile(f):
            continue
        _, e = splitext(basename(f))
        n = join(dirname(f), f"{prefix}{i}{e.lower()}")
        if exists(n):
            raise IOError(f'not overriting existing file "{n}"')
        print(f'Moving "{f}" to "{n}"..')
        rename(f, n)
        i += 1
        del e, n
    del u, m


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
        _move(target, prefix)
    except OSError as err:
        print(f"Error during move: {err}!", file=stderr)
        exit(1)
