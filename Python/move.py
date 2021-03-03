#!/usr/bin/python3
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

from glob import glob
from os import rename
from sys import argv, exit, stderr
from os.path import isdir, basename, join, isfile, splitext, abspath

if __name__ == "__main__":
    if len(argv) < 2:
        print(f"usage {argv[0]} <path> [prefix]")
        exit(2)

    if not isdir(argv[1]):
        print(f'Path "{argv[1]} does not exist or is not a directory!', file=stderr)
        exit(1)

    inc = 0
    prefix = ""
    if len(argv) >= 3:
        prefix = f"{argv[2]}-"
    for f in glob(join(abspath(argv[1]), "**")):
        if not isfile(f):
            continue
        _, e = splitext(basename(f))
        r = f"{prefix}{inc}{e.lower()}"
        try:
            print(f'Moving "{f}" to "{r}"...')
            rename(f, r)
        except OSError as err:
            print(f'Cannot move "{f}" to "{r}": {err}!', file=stderr)
            exit(1)
        inc += 1
