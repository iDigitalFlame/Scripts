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

from json import dumps
from bs4 import BeautifulSoup
from mastodon import Mastodon
from os.path import isdir, join
from sys import argv, stderr, exit

ALLOWED_TAGS = ["a", "br", "span", "p", "div"]
ALLOWED_ATTRS = ["class", "href"]


def _check_html(e):
    for c in e:
        if c.name is None:
            continue
        if c.name.lower() not in ALLOWED_TAGS:
            c.decompose()
            continue
        _check_html(c)
        if not isinstance(c.attrs, dict) or len(c.attrs) == 0:
            continue
        x = c.attrs.copy()
        for k, v in c.attrs.items():
            n = k.lower()
            if n == "rel":
                x[n] = ["nofollow", "noopener", "noreferrer"]
                continue
            if n not in ALLOWED_ATTRS:
                del x[k]
                continue
            if not k.islower():
                x[n] = v
        c.attrs = x
        del x


def _parse_entry(entry):
    a, b = entry["account"]["acct"], False
    if entry["reblog"] is not None:
        a, b = entry["reblog"]["account"]["acct"], True
        entry = entry["reblog"]
    v = BeautifulSoup(entry["content"], features="html.parser")
    _check_html(v)
    r = {
        "url": entry["url"],
        "user": "@" + a,
        "boost": b,
        "media": list(),
        "content": str(v),
    }
    del v, a
    if not isinstance(entry["media_attachments"], list):
        return r
    if len(entry["media_attachments"]) == 0:
        return r
    for i in entry["media_attachments"]:
        if i["type"] != "image":
            continue
        u = i["preview_url"]
        if not isinstance(u, str) or len(u) == 0:
            u = i["url"]
        r["media"].append(u)
    return r


def user_feed(server, username, limit=20):
    m = Mastodon(api_base_url=server)
    u = m.account_lookup(username)
    if u is None:
        raise ValueError(f'username "{username}" not found')
    e = m.account_statuses(
        u["id"],
        limit=limit,
        pinned=False,
        only_media=False,
        exclude_replies=True,
        exclude_reblogs=False,
    )
    r = list()
    for i in e:
        r.append(_parse_entry(i))
    del e, u, m
    return r


if __name__ == "__main__":
    if len(argv) != 3:
        print(f"{argv[0]} <users.conf> <output_dir>", file=stderr)
        exit(2)
    if not isdir(argv[2]):
        print(f'Directory path "{argv[2]}" is not valid!', file=stderr)
        exit(1)
    try:
        with open(argv[1], "r") as f:
            u = f.read().split("\n")
    except OSError as err:
        print(f'Users config file "{argv[1]}" cannot be opened: {err}!', file=stderr)
        exit(1)
    if not isinstance(u, list) or len(u) == 0:
        print(f'No users entries found in "{argv[1]}"!', file=stderr)
        exit(1)
    for e in u:
        if len(e) == 0:
            continue
        i = e.rfind("/")
        if i <= 0:
            print(f'User entry "{e}" is invalid!', file=stderr)
            exit(1)
        s = e[:i]
        u = e[i + 1 :]
        if len(s) == 0 or len(u) <= 1:
            print(f'User entry "{e}" is invalid!', file=stderr)
            exit(1)
        if u[0] == "@":
            u = u[1:]
        if " " in u:
            n = u.rfind(" ")
            if n <= 0:
                print(f'User entry "{e}" is invalid!', file=stderr)
                exit(1)
            f = u[n + 1 :]
            u = u[:n]
        else:
            f = u
        print(f'Downloading entries for "{u}" from "{s}"..')
        try:
            r = user_feed(s, u)
        except Exception as err:
            print(f'User entry "{u}" from "{s}" retrival error: {err}', file=stderr)
            exit(1)
        try:
            with open(join(argv[2], f"{f}.json"), "w") as x:
                x.write(dumps(r, indent="    ", sort_keys=False))
        except Exception as err:
            print(f'User entry file "{f}" write error: {err}', file=stderr)
            exit(1)
        print(f'Parsed "{s}/{u}" to "{f}.json".')
    print("Done.")
    exit(0)
