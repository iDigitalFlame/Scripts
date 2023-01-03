#!/usr/bin/python3
# Copyright (C) 2021 - 2023 iDigitalFlame
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
from bs4 import BeautifulSoup
from sys import argv, exit, stderr

USER_AGENTS = "https://botsvsbrowsers.org/recent/listings/index.html"


def agents(url):
    c = get(url)
    if c.status_code != 200:
        raise ValueError(f"Received a non-200 status code: {c.status_code}!")
    h = BeautifulSoup(c.content, features="lxml")
    c.close()
    del c
    u = h.find_all(attrs={"class": "uaList"})
    del h
    if not isinstance(u, list) or len(u) != 1:
        raise ValueError("Unable to parse User-Agent list!")
    x = 0
    a = list()
    for e in u[0].find_all("li"):
        if len(e.text) < 5:
            continue
        v = e.text.strip()
        if len(v) == 0:
            continue
        if " ad " in v.lower():
            continue
        if v.lower().startswith("wget"):
            continue
        if v.lower().startswith("curl"):
            continue
        if v.lower().startswith("python"):
            continue
        if v.lower().startswith("requests"):
            continue
        x += 1
        if "(iPod" in v or "(iPhone" in v or "(iPad" in v:
            a.append(f"iOS ({x}) [Mobile]: {v}")
            continue
        if "; Android " in v:
            a.append(f"Android ({x}) [Mobile]: {v}")
            continue
        o = "Unknown"
        if " (X11; " in v:
            o = "Linux"
        elif "(Windows NT" in v:
            o = "Windows"
        elif "(Macintosh" in v or "macOS" in v:
            o = "MacOS"
        a.append(f"{o} ({x}) [{o}]: {v}")
        del v
        del o
    del u
    a.sort()
    return a


if __name__ == "__main__":
    u = USER_AGENTS

    if len(argv) > 1:
        if argv[1] == "-h" or argv[1] == "--help":
            print(f"{argv[0]} [url]", file=stderr)
            exit(2)
        u = argv[1]

    try:
        for a in agents(u):
            print(a)
    except Exception as err:
        print(f"[!] Error: {err}", file=stderr)
        exit(1)

    del u
