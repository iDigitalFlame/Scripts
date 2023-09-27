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

from hashlib import md5
from sys import argv, exit
from os import listdir, remove
from os.path import isfile, abspath, join


def hash_file(path):
    g = md5()
    with open(path, "rb") as f:
        while True:
            b = f.read(4096)
            if not b:
                break
            g.update(b)
    h = g.hexdigest()
    del g
    return h


def identify(path, delete):
    p = abspath(path)
    x = listdir(path)
    x.sort()
    m = dict()
    for e in x:
        f = join(p, e)
        if not isfile(e) or not isfile(f):
            continue
        h = hash_file(f)
        if h not in m:
            m[h] = e
            del f
            del h
            continue
        if delete:
            print(f'Deleting duplicate file "{e}" of "{m[h]}"..')
            remove(f)
        else:
            print(f'Duplicate file "{e}" of "{m[h]}"')
        del h
        del f


if __name__ == "__main__":
    if len(argv) < 2:
        print(f"{argv[0]} [--delete] <dir>")
        exit(2)

    if len(argv) == 3 and argv[1] == "--delete":
        identify(argv[2], True)
    else:
        identify(argv[1], False)
