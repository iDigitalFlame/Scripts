#!/usr/bin/python3
# Blocklist Downloader and Parser
#
# Copyright (C) 2024 - 2025 iDigitalFlame
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

from io import BytesIO
from requests import get
from re import compile, I
from sys import stderr, exit
from traceback import format_exc
from argparse import ArgumentParser
from tarfile import open as tar_open
from urllib.request import getproxies
from os.path import exists, isfile, expanduser, expandvars

_Locals = [
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
_Reserved_IPv4 = ["172.16.", "10.", "192.168.", "127.0.0.1", "169.254." "224.0"]
_Reserved_IPv6 = ["fc00:", "fe80:", "ff00:"]

_IPv4 = compile(
    r"^([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})(/[0-9]{0,2}){0,1}$"
)
_IPv6 = compile(
    r"^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]"
    r"{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|"
    r"([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|"
    r"[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}"
    r"%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|"
    r"(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}"
    r"(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))(/[0-9]{0,2}){0,1}$"
)

_ALLOWED_DNS = [
    "1.0.0.1",
    "1.1.1.1",
    "2606:4700:4700::1001",
    "2606:4700:4700::1111",
]

PROXIES = getproxies()
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


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
        dest="no_break",
        help="Don't fail on URL download errors.",
        action="store_true",
        required=False,
    )
    a, r, q = p.parse_args(), None, None
    if isinstance(a.extra, str) and len(a.extra) > 0:
        try:
            q = _extra(expanduser(expandvars(a.extra)))
        except Exception as err:
            print(f"Error reading and parsing extra domains: {err}!", file=stderr)
            print(format_exc(limit=3), file=stderr)
            return exit(1)
    if isinstance(a.rules, str) and len(a.rules) > 0:
        try:
            r = _rules(expanduser(expandvars(a.rules)))
        except Exception as err:
            print(f"Error compiling rules: {err}!", file=stderr)
            print(format_exc(limit=3), file=stderr)
            return exit(1)
    if r is not None:
        print(f'Compiled {len(r)} rules from "{a.rules}"')
    e, i4, i6, eo = set(), set(), set(), False
    try:
        for u in _read(expanduser(expandvars(a.urls))):
            print(f'Downloading "{u}"..')
            try:
                _download(e, i4, i6, u)
            except Exception as err:
                eo = True
                if a.no_break:
                    print(
                        f"Error downloading and parsing URL {u}: {err}, skipping entry!",
                        file=stderr,
                    )
                    continue
                raise err
    except Exception as err:
        print(f"Error downloading and parsing URLs: {err}!", file=stderr)
        print(format_exc(limit=3), file=stderr)
        return exit(1)
    print(
        f"Downloaded {len(e)} Domain Names, {len(i4)} IPv4 Addresses and {len(i6)} IPv6 Addresses."
    )
    if q is not None and len(q) > 0:
        for i in q:
            e.add(i.lower())
        print(f"Added {len(q)} additional domains.")
    del q
    if r is not None:
        print(f"Checking {len(e)} Domains against ruleset..")
        o, p, m, u = list(), 0, len(e), 0
        for x, i in enumerate(e):
            p = int(round((x / m) * 100, 0))
            if p > u and p % 10 == 0 and p < 100:
                print(f"Checking {p}% ({x}/{m}) complete..")
                u = p
            if not _check(r, i):
                continue
            o.append(i)
        del p, m, u
        o.sort()
        print(f"Removed {len(e) - len(o)} Domain Names from the ruleset.")
    else:
        o = sorted(e)
    del e, r
    print(f'Writing {len(o)} Domain Names to file "{a.out}"..')
    try:
        with open(expanduser(expandvars(a.out)), "w") as f:
            for v in o:
                f.write(f"0.0.0.0 {v}\n")
    except Exception:
        print(f'Error saving output to "{a.out}"!', file=stderr)
        print(format_exc(limit=3), file=stderr)
        return exit(1)
    del o
    if a.ipv4:
        print(f'Writing {len(i4)} IPv4 Addresses to file "{a.ipv4}"..')
        try:
            with open(expanduser(expandvars(a.ipv4)), "w") as f:
                f.write("\n".join(i4))
        except Exception:
            print(f'Error saving output to "{a.ipv4}"!', file=stderr)
            print(format_exc(limit=3), file=stderr)
            return exit(1)
    if a.ipv6:
        print(f'Writing {len(i6)} IPv6 Addresses to file "{a.ipv6}"..')
        try:
            with open(expanduser(expandvars(a.ipv6)), "w") as f:
                f.write("\n".join(i6))
        except Exception:
            print(f'Error saving output to "{a.ipv6}"!', file=stderr)
            print(format_exc(limit=3), file=stderr)
            return exit(1)
    del i4, i6, a
    if eo:
        print("Done, but error occuring during runtime!")
        exit(1)
    print("Done!")


def _read(file):
    if not exists(file):
        raise OSError(f'List file path "{file}" does not exist')
    with open(file) as f:
        d = f.read()
    if d is None or len(d) == 0:
        return None
    r = set()
    for i in d.split("\n"):
        if len(i) == 0 or i[0] == "#":
            continue
        e = i.strip()
        if len(e) == 0 or e[0] == "#":
            continue
        del i
        if e in r:
            print(f'Duplicate entry "{e}" found.', file=stderr)
            continue
        if not e.startswith("http"):
            print(f'Skipping invalid entry "{e}".', file=stderr)
            continue
        r.add(e)
        del e
    del d
    return sorted(r)


def _rules(file):
    if not isfile(file):
        raise OSError(f'Rules file path "{file}" does not exist')
    with open(file) as f:
        d = f.read()
    if d is None or len(d) == 0:
        return None
    r = list()
    for i in d.split("\n"):
        if len(i) == 0 or i[0] == "#":
            continue
        e = i.strip()
        if len(e) == 0 or e[0] == "#":
            continue
        del i
        try:
            r.append(compile(e, I))
        except Exception as err:
            raise OSError(f'Regex rule "{e}" failed to compile: {err}') from err
        del e
    del d
    if len(r) == 0:
        return None
    return r


def _extra(file):
    if not exists(file):
        raise OSError(f'Extra file path "{file}" does not exist')
    with open(file) as f:
        d = f.read()
    if d is None or len(d) == 0:
        return None
    r = list()
    for i in d.split("\n"):
        if len(i) == 0 or i[0] == "#":
            continue
        e = i.strip()
        if len(e) == 0 or e[0] == "#":
            continue
        del i
        r.append(e)
        del e
    del d
    if len(r) == 0:
        return None
    r.sort()
    return r


def _check(rules, e):
    if rules is None:
        return True
    for i in rules:
        if i.fullmatch(e) is not None:
            return False
    return True


def _is_reserved(v, v6):
    if v6:
        for i in _Reserved_IPv6:
            if v.startswith(i):
                return True
        return False
    for i in _Reserved_IPv4:
        if v.startswith(i):
            return True
    return False


def _download_parse(url, data):
    if not url.endswith(".tar.gz"):
        return data.decode("UTF-8")
    b = BytesIO(data)
    f, d = tar_open(fileobj=b), None
    try:
        n = url[url.rfind("/") + 1 :]
    except (IndexError, TypeError):
        n = None
    for i in f.getmembers():
        if i.name.endswith("/domains") or (
            isinstance(n, str) and len(n) > 0 and i.name.endswith(n)
        ):
            d = f.extractfile(i).read().decode("UTF-8")
            break
    if not isinstance(d, str) or len(d) == 0:
        m = f.getmembers()
        if len(m) > 0:
            d = f.extractfile(m[0]).read().decode("UTF-8")
            if "\n" not in d:
                d = None
        del m
    f.close()
    b.close()
    del b, f
    if not isinstance(d, str) or len(d) == 0:
        raise OSError(f'URL "{url}" tar entry is not valid or is empty')
    return d


def _add_entry(res, ip4, ip6, v):
    if len(v) == 0:
        return
    if len(v) == 1:
        if v[0] in _Locals:
            return
        if "|" in v[0]:
            return _add_entry(res, ip4, ip6, v[0].split("|"))
        if _IPv4.fullmatch(v[0]) is not None:
            if v[0] in _ALLOWED_DNS or _is_reserved(v[0], False):
                return
            return ip4.add(v[0])
        if ":" in v[0] and _IPv6.fullmatch(v[0]) is not None:
            if v[0] in _ALLOWED_DNS or _is_reserved(v[0], True):
                return
            return ip6.add(v[0])
        return res.add(v[0].lower())
    if len(v) == 2:
        if v[1] in _Locals:
            return
        if "|" in v[1]:
            return _add_entry(res, ip4, ip6, v[1].split("|"))
        if _IPv4.fullmatch(v[1]) is not None:
            if v[1] in _ALLOWED_DNS or _is_reserved(v[1], False):
                return
            return ip4.add(v[1])
        if ":" in v[1] and _IPv6.fullmatch(v[1]) is not None:
            if v[1] in _ALLOWED_DNS or _is_reserved(v[1], True):
                return
            return ip6.add(v[1])
        return res.add(v[1].lower())
    for i in v:
        if i in _Locals:
            continue
        if "|" in i:
            _add_entry(res, ip4, ip6, i.split("|"))
            continue
        if _IPv4.fullmatch(i) is not None:
            if i in _ALLOWED_DNS or _is_reserved(i, False):
                continue
            ip4.add(i)
            continue
        if ":" in i and _IPv6.fullmatch(i) is not None:
            if i in _ALLOWED_DNS or _is_reserved(i, True):
                continue
            ip6.add(i)
            continue
        res.add(i.lower())


def _download(res, ip4, ip6, url):
    with get(
        url, stream=True, headers={"User-Agent": USER_AGENT}, proxies=PROXIES
    ) as r:
        if r.status_code != 200:
            raise OSError(f'URL "{url}" returned non-OK status code {r.status_code}')
        d = _download_parse(url, r.content)
        r.close()
    for i in d.split("\n"):
        if len(i) == 0 or i[0] == "#" or i[0] == ";":
            continue
        e = i.strip()
        del i
        if len(e) == 0 or e[0] == "#" or e[0] == ";":
            continue
        v = e.find("#")
        if v == -1:
            v = e.find(";")
        if v > 0 and v < len(e):
            e = e[:v]
        del v
        if len(e) == 0:
            continue
        n = e.split()
        del e
        if len(n) == 0:
            continue
        if len(n) > 1:
            n = n[1:]
        _add_entry(res, ip4, ip6, n)
        del n
    del d


if __name__ == "__main__":
    try:
        _main()
    except KeyboardInterrupt:
        print("Interrupted!", file=stderr)
        exit(3)
