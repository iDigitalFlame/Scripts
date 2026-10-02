#!/usr/bin/python3
#
# Copyright (C) 2026 iDigitalFlame
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

# Image Hash Renamer
#  Takes a glob pattern and will rename the target images as their image dhash
#  value. Will *not* overrite any previous files if they exist.
#
# Usage:
#  python image_hash.py '~/Directory/*.jpg'

from PIL import Image
from glob import glob
from imagehash import dhash
from os import getcwd, rename
from sys import argv, exit, stderr
from os.path import join, exists, isfile, dirname, splitext, expanduser, expandvars


def _main():
    if len(argv) < 2:
        print(f"{argv[0]} [--dry] <patten>", file=stderr)
        exit(2)
    p, d = argv[1], False
    if len(argv) == 3:
        if argv[1] == "--dry":
            p, d = argv[2], True
        elif argv[2] == "--dry":
            d = True
    if d:
        print("[Dry Run] Nothing will be changed..")
    try:
        _move(_map(p), d)
    except Exception as err:
        print(f"Error: {err}", file=stderr)
        exit(1)
    finally:
        del d, p
    exit(0)


def _map(pat):
    if pat == ".":
        v = glob(join(getcwd(), "*"), recursive=True)
    else:
        v = glob(expandvars(expanduser(pat)), recursive=True)
    if len(v) == 0:
        return print(f'Nothing with pattern "{pat}" found!', file=stderr)
    print(f"Found {len(v)} entries..")
    e = dict()
    for i in v:
        if not isfile(i):
            continue
        try:
            with Image.open(i) as f:
                r = str(dhash(f, hash_size=8))
            if r not in e:
                e[r] = list()
            e[r].append(i)
            del r
        except Exception as err:
            print(f'Error processing image file "{i}": {err}!', file=stderr)
    return e


def _move(ent, dry):
    if ent is None or len(ent) == 0:
        return
    for k, v in ent.items():
        if len(v) == 0:
            continue
        if len(v) == 1:
            _rename(v[0], k, dry)
            continue
        print(f'Detected {len(v)} duplicates of "{k}"!')
        for x in range(0, len(v)):
            _rename(v[x], f"{k}-{x}", dry)


def _rename(v, n, dry):
    f = dirname(v)
    b, e = splitext(v)
    if len(e) > 0 and e[0] != ".":
        e = f".{e}"
    if b == n:
        return
    d = join(f, f"{n}{e}")
    del b, e, f
    if dry:
        return print(f'Rename "{v}" to "{d}".')
    try:
        if exists(d):
            raise OSError(f'file "{d}" already exists')
        rename(v, d)
    finally:
        del d


if __name__ == "__main__":
    _main()
