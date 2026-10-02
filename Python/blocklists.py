#!/usr/bin/python3
#
# Copyright (C) 2024 - 2026 iDigitalFlame
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

# Blocklist Downloader and Parser

from requests import get
from re import I, compile
from tarfile import TarFile
from sys import exit, stderr
from traceback import format_exc
from argparse import ArgumentParser
from urllib.request import getproxies
from os.path import expanduser, expandvars

LOCALS = [
    "::1",
    "0.0.0.0",
    "127.0.0.1",
    "255.255.255.255",
    "239.255.255.250",
    "224.0.0.251",
    "fe80::1%lo0",
    "ff00::0",
    "ff02::1",
    "ff02::2",
    "ff02::3",
    "localhost",
    "localhost.localdomain",
]
RESERVED_IPV4 = ["172.16.", "10.", "192.168.", "127.0.0.1", "169.254." "224.0"]
RESERVED_IPV6 = ["fc00:", "fe80:", "ff00:"]

AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
DNS = [
    "1.0.0.1",
    "1.1.1.1",
    "2606:4700:4700::1001",
    "2606:4700:4700::1111",
]
PROXY = getproxies()

IPV4 = compile(
    r"^([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})(/[0-9]{0,2}){0,1}$"
)
IPV6 = compile(
    r"^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]"
    r"{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|"
    r"([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|"
    r"[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}"
    r"%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|"
    r"(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}"
    r"(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))(/[0-9]{0,2}){0,1}$"
)


def _main():
    p = ArgumentParser(description="Hosts Blocklist Downloader")
    p.add_argument(
        "-r",
        "--rules",
        type=str,
        dest="rules",
        help="Rules file path.",
        action="store",
        metavar="rules",
        required=False,
    )
    p.add_argument(
        "-u",
        "--urls",
        type=str,
        dest="urls",
        help="URLs file path.",
        action="store",
        metavar="urls",
        required=True,
    )
    p.add_argument(
        "-o",
        "--output",
        type=str,
        dest="out",
        help="Output file path.",
        action="store",
        metavar="out",
        required=True,
    )
    p.add_argument(
        "-f",
        "--extra",
        type=str,
        dest="extra",
        help="Extra newline-seperated domains to add.",
        action="store",
        metavar="extra",
        required=False,
    )
    p.add_argument(
        "--ipv4",
        type=str,
        dest="ipv4",
        help="IPv4 entries output file path.",
        action="store",
        metavar="ipv4",
        required=False,
    )
    p.add_argument(
        "--ipv6",
        type=str,
        dest="ipv6",
        help="IPv6 entries output file path.",
        action="store",
        metavar="ipv6",
        required=False,
    )
    p.add_argument(
        "--no-break",
        dest="errors",
        help="Don't fail on URL download errors.",
        action="store_false",
        required=False,
    )
    a = p.parse_args()
    del p
    r, x = Rules(a.rules), Parser()
    e = x.download(a.urls, a.errors)
    x.add(a.extra)
    x.validate(r)
    del r
    x.save(a.out, a.ipv4, a.ipv6)
    del a, x
    if not e:
        print("Done, but errors occurred during download/parsing!")
        exit(2)
    print("Done!")
    del e


def _is_reserved(v, v6):
    if v6:
        for i in RESERVED_IPV6:
            if v.startswith(i):
                return True
        return False
    for i in RESERVED_IPV4:
        if v.startswith(i):
            return True
    return False


class Rules(object):
    __slots__ = ("x", "empty")

    def __init__(self, rules):
        self.x = list()
        self._load(rules)
        self.empty = len(self.x) == 0

    def check(self, v):
        if self.empty:
            return True
        for i in self.x:
            if i.fullmatch(v) is not None:
                return False
        return True

    def _load(self, rules):
        if not isinstance(rules, str) or len(rules) == 0:
            return
        v = expanduser(expandvars(rules))
        try:
            with open(v) as f:
                while True:
                    i = f.readline()
                    if len(i) == 0:
                        break
                    if len(i) == 1 or i[0] == "#":
                        continue
                    e = i.strip()
                    del i
                    if len(e) == 0 or e[0] == "#":
                        continue
                    try:
                        if "$" in e or "^" in e or "\\" in e or ")" in e or "(" in e:
                            self.x.append(compile(e, I))
                            continue
                        x = "^"
                        if e[0] == "*":
                            x, e = r"^((.+\.)?)", e[1:]  # Wildcard Rule
                        elif e[0] == "+":
                            x, e = r"^((www\.)?)", e[1:]  # Root + www Rule
                        self.x.append(compile(f"{x}{e.replace(".", "\\.")}$", I))
                        del x
                    except Exception as err:
                        raise OSError(f'cannot compile rule "{e}": {err}')
                    finally:
                        del e
        except OSError as err:
            raise OSError(f'cannot parse rules list "{v}": {err}')
        print(f'Compiled {len(self.x)} rules from "{v}"')
        del v


class Parser(object):
    __slots__ = ("ip4", "ip6", "entries")

    def __init__(self):
        self.ip4, self.ip6, self.entries = set(), set(), set()

    def _add(self, v):
        if len(v) == 1:
            return self._entry(v[0])
        if len(v) == 2:
            return self._entry(v[1])
        for i in v:
            self._entry(i)

    def _get(self, url):
        with get(url, stream=True, headers={"User-Agent": AGENT}, proxies=PROXY) as r:
            if r.status_code != 200:
                raise OSError(f"non-OK status code {r.status_code}")
            if not url.endswith(".tar.gz"):
                return self._parse(Reader(r))
            return self._parse_tar(url, r.raw)

    def _entry(self, v):
        if len(v) == 0 or v in LOCALS:
            return
        if "|" in v:
            for i in v.split("|"):
                self._entry(i)
            return
        if IPV4.fullmatch(v) is not None:
            if v in DNS or _is_reserved(v, False):
                return
            return self.ip4.add(v)
        if ":" in v and IPV6.fullmatch(v) is not None:
            if v in DNS or _is_reserved(v, True):
                return
            return self.ipv6.add(v)
        self.entries.add(v.lower())

    def _parse(self, f):
        while True:
            v = f.readline()
            if len(v) == 0:
                break
            if len(v) == 1:
                continue
            if len(v) == 0 or v[0] == "#" or v[0] == ";" or v[0] == "!":
                continue
            i = v.strip()
            del v
            if len(i) == 0 or i[0] == "#" or i[0] == ";" or i[0] == "!":
                continue
            r = i.find("#")
            if r == -1:
                r = i.find(";")
            if r > 0 and r < len(i):
                i = i[:r]
            del r
            if len(i) < 3 or "http:" in i or "https:" in i or "." not in i or "/" in i:
                continue
            if i[0] == "|" and i[1] == "|":
                i = i[2:]
            if i[-1] == "^":
                i = i[:-1]
            if i[-1] == "/":
                i = i[:-1]
            if "\\" in i:
                i = i.replace("\\", "")
            v = i.lower().split()
            del i
            if len(v) == 0:
                continue
            if len(v) > 1:
                self._add(v[1:])
            else:
                self._add(v)
            del v

    def add(self, extras):
        if not isinstance(extras, str) or len(extras) == 0:
            return
        n, v = 0, expanduser(expandvars(extras))
        try:
            with open(v) as f:
                while True:
                    i = f.readline()
                    if len(i) == 0:
                        break
                    if len(i) == 1 or i[0] == "#":
                        continue
                    e = i.strip()
                    del i
                    if len(e) == 0 or e[0] == "#":
                        continue
                    self._entry(e)
                    n += 1
                    del e
        except OSError as err:
            raise OSError(f'cannot parse extras list "{v}": {err}')
        print(f'Added {n} additional domains from "{v}".')
        del n, v

    def validate(self, rules):
        self.entries = list(self.entries)
        if not isinstance(rules, Rules):
            return
        print(f"Checking {len(self.entries)} Domains against rulesets..")
        c, n, r = 0, len(self.entries), 0
        for x, i in enumerate(self.entries):
            v = int(round((x / n) * 100, 0))
            if v > c and v % 10 == 0 and v < 100:
                print(f"Checking {v}% ({x}/{n}) complete..")
                c = v
            del v
            if rules.check(i):
                continue
            r += 1
            self.entries[x] = None
        del c, n
        print(f"Removed {r} Domains.")
        del r

    def _parse_tar(self, url, raw):
        try:
            n = url[url.rfind("/") + 1 :]
        except (IndexError, TypeError):
            n = None
        with TarFile.open(mode="r|*", fileobj=raw) as f:
            p = None
            while True:
                v = f.next()
                if v is None:
                    break
                if v.name.endswith("/domains") or (n and v.name.endswith(n)):
                    with f.extractfile(v) as e:
                        return self._parse(Decoder(e))
                p = v
                del v
            try:
                with f.extractfile(p):
                    return self._prase(v)
            finally:
                del p

    def download(self, urls, errors=True):
        u, v = set(), expanduser(expandvars(urls))
        try:
            with open(v) as f:
                while True:
                    i = f.readline()
                    if len(i) == 0:
                        break
                    if len(i) == 1 or i[0] == "#":
                        continue
                    e = i.strip()
                    del i
                    if len(e) == 0 or e[0] == "#":
                        continue
                    if e in u:
                        print(f'Duplicate URL entry "{e}" found.', file=stderr)
                        continue
                    if not e.startswith("http"):
                        if errors:
                            raise OSError(f'invalid URL entry "{e}"')
                        print(
                            f'WARNING: Skipping invalid URL entry "{e}".', file=stderr
                        )
                        continue
                    u.add(e)
                    del e
        except OSError as err:
            raise OSError(f'cannot parse URLs list "{v}": {err}')
        print(f'Read {len(u)} URLs from "{v}".')
        del v
        if len(u) == 0:
            return
        e = True
        for i in sorted(u):
            print(f'Downloading "{i}"..')
            try:
                self._get(i)
            except OSError as err:
                if errors:
                    raise OSError(f'cannot download and parse URL "{i}": {err}')
                print(
                    f'WARNING: Failed to download and parse URL "{i}": {err}',
                    file=stderr,
                )
                e = False
        del u
        print(
            f"Downloaded {len(self.entries)} Domain Names, {len(self.ip4)} IPv4 Addresses "
            f"and {len(self.ip6)} IPv6 Addresses."
        )
        return e

    def save(self, out, ip4=None, ip6=None):
        v = expanduser(expandvars(out))
        print(f'Writing {len(self.entries)} Domain Names to "{v}"..')
        try:
            with open(v, "w") as f:
                for i in self.entries:
                    if i is None:
                        continue
                    f.write(f"0.0.0.0 {i}\n")
        except Exception as err:
            raise OSError(f'cannot write domains to "{v}": {err}')
        del v
        if isinstance(ip4, str) and len(ip4) > 0:
            v = expanduser(expandvars(ip4))
            print(f'Writing {len(self.ip4)} IPv4 Addresses to "{v}"..')
            try:
                with open(v, "w") as f:
                    for i in self.ip4:
                        f.write(f"{i}\n")
            except Exception as err:
                raise OSError(f'cannot write IPv4 addresses to "{v}": {err}')
            del v
        if not isinstance(ip6, str) or len(ip6) == 0:
            return
        v = expanduser(expandvars(ip6))
        print(f'Writing {len(self.ip6)} IPv6 Addresses to "{v}"..')
        try:
            with open(v, "w") as f:
                for i in self.ip6:
                    f.write(f"{i}\n")
        except Exception as err:
            raise OSError(f'cannot write IPv6 addresses to "{v}": {err}')
        del v


class Reader(object):
    __slots__ = ("_x",)

    def __init__(self, v):
        self._x = v.iter_lines(decode_unicode=True)

    def readline(self):
        try:
            v = self._x.__next__()
            if len(v) == 0:
                return "\n"
            if isinstance(v, bytes):
                return v.decode("UTF-8")
            return v
        except StopIteration:
            return str()


class Decoder(object):
    __slots__ = ("_x",)

    def __init__(self, v):
        self._x = v

    def readline(self):
        return self._x.readline().decode("UTF-8")


if __name__ == "__main__":
    try:
        _main()
    except KeyboardInterrupt:
        print("Interrupted!", file=stderr)
        exit(3)
    except Exception as err:
        print(f"Error: {err}!", file=stderr)
        print(format_exc(limit=5), file=stderr)
        exit(1)
