#!/usr/bin/python3
#
# Copyright (C) 2023 iDigitalFlame
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

from requests import get
from os.path import exists, isdir
from sys import argv, stderr, exit


def parse(file, dir):
    if not isdir(dir):
        print(f'Directory path "{dir}" is not valid!', file=stderr)
        return False
    if not exists(file):
        print(f'List file path "{file}" does not exist!', file=stderr)
        return False
    try:
        with open(file) as f:
            d = f.read()
    except OSError as err:
        print(f'Could not open file "{file}": {err}!', file=stderr)
        return False
    if d is None or len(d) == 0:
        return True
    c = dict()
    for u in d.split("\n"):
        if len(u) == 0 or u[0] == "#":
            continue
        x = u.strip()
        if len(x) == 0 or x[0] == "#":
            continue
        i = u.index(":")
        if i <= 0:
            print(f'Skipping invalid entry "{u}": missing seperator!', file=stderr)
            continue
        n = u[:i].strip()
        v = u[i + 1 :].strip()
        if len(n) == 0 or len(v) == 0:
            print(
                f'Skipping invalid entry "{u}": empty name or URL value!', file=stderr
            )
            continue
        if n.lower() in c:
            print(f'Invalid entry "{n}" is a duplicate name!', file=stderr)
            return False
        c[n] = True
        if not v.startswith("http"):
            print(f'Skipping invalid entry "{u}": invalid URL value!', file=stderr)
            continue
        try:
            download(v, f"{dir}/{n}.txt")
        except (OSError, UnicodeDecodeError) as err:
            print(f'Could not download/parse "{v}" to "{n}": {err}!', file=stderr)
            return False
    return True


def download(url, name):
    with get(url, stream=True, timeout=5, headers={"User-Agent": "curl/7.73.0"}) as r:
        if r.status_code != 200:
            raise OSError(f"non-OK status code {r.status_code}")
        d = r.content.decode("UTF-8")
    with open(name, "w") as o:
        o.write(f"# Original file: {url}\n")
        for e in d.split("\n"):
            if len(e) == 0 or e[0] == "#":
                continue
            if " " not in e:
                o.write(f"0.0.0.0 {e}\n")
                continue
            i = e.index(" ")
            if i <= 6:
                o.write(f"0.0.0.0 {e}\n")
                continue
            if "#" in e[i + 1 :].strip():
                o.write(f"0.0.0.0 {e[:i]}\n")
                continue
            v = e[:i].strip()
            if v == "0.0.0.0" or v == "127.0.0.1":
                o.write(f"{e}\n")
                continue
            o.write(f"0.0.0.0 {e[i+1:].strip()}\n")
        o.flush()
    del o


if __name__ == "__main__":
    if len(argv) != 3:
        print(f"{argv[0]} <config> <directory>", file=stderr)
        exit(2)
    if not parse(argv[1], argv[2]):
        exit(1)
    exit(0)
