#!/usr/bin/python3
#
# Copyright (C) 2016 - 2026 iDigitalFlame
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

from sys import argv, exit, stderr, stdout


def split(d, file):
    r = dict()
    for i in d.split("\n"):
        if i.strip().startswith("//"):
            continue
        if len(i) < 4 or '"' not in i or ";" not in i or "," not in i:
            continue
        n = i.lower().find('pref("')
        if n is None or n < 4:
            continue
        v = i.find('"', n + 6)
        if v is None or v < n:
            continue
        c = i.find(",", v + 1)
        if c is None or c < v:
            continue
        e = i.find(");", c + 1)
        if e is None or e < c:
            continue
        k = i[n + 6 : v].strip()
        if k == "_user.js.parrot":
            continue
        if k in r:
            raise ValueError(f'duplicate value "{k}" in "{file}"')
        r[k] = (i.strip()[0].lower() == "l", k, i[c + 1 : e].strip())
        del n, v, c, e, k
    return r


def output(p, file):
    n, d = None, dict(sorted(p.items()))
    for k, v in d.items():
        if v[0]:
            continue
        if n is not None and n != k.split(".")[0].lower():
            print("", file=file)
        print("defaultPref(", file=file, end="")
        print(('"' + k + '"').ljust(88), file=file, end="")
        print(f", {v[2]});", file=file)
        n = k.split(".")[0].lower()
    print("", file=file)
    n = None
    for k, v in d.items():
        if not v[0]:
            continue
        if n is not None and n != k.split(".")[0].lower():
            print("", file=file)
        print("lockPref(", file=file, end="")
        print(('"' + k + '"').ljust(91), file=file, end="")
        print(f", {v[2]});", file=file)
        n = k.split(".")[0].lower()
    del n


if __name__ == "__main__":
    if len(argv) < 3:
        print(f"{argv[0]} [-m] <base> <compare>", file=stderr)
        exit(2)

    if len(argv) >= 4 and argv[1] == "-m":
        pass

    try:
        with open(argv[1]) as b, open(argv[2]) as c:
            g, h = split(b.read(), argv[1]), split(c.read(), argv[2])

        for k, v in h.items():
            if k not in g:
                g[k] = v
                print(f'Adding missing key "{k}" to Base.', file=stderr)
                continue
            i = g[k]
            if k in g and v != i:
                print(
                    (
                        f'Values "{k}" differ: Base ({"lockPref" if i[0] else "defaultPref"}) = '
                        f'{i[2]} vs Compare ({"lockPref" if v[0] else "defaultPref"}) = {v[2]}'
                    ),
                    file=stderr,
                )
            del i
        print("", file=stderr)
        output(g, stdout)
    except KeyError as err:
        print(f'Duplicate key: "{err}"')
        exit(1)
    except Exception as err:
        print(f"Error: {err}")
        exit(1)
