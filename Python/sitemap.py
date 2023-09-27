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
from requests import get
from os.path import exists
from sys import stderr, argv
from bs4 import BeautifulSoup
from datetime import datetime
from xml.etree import ElementTree
from json import loads, dumps, JSONDecodeError


def _parse(url):
    u = url.replace("http://", "").replace("https://", "").lower()
    if "#" not in u:
        return u
    return u[: u.find("#")]


def _gen_sitemap(base, sitemap, mapped):
    h = ElementTree.Element("urlset")
    h.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    h.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    h.set(
        "xsi:schemaLocation",
        "http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd",
    )
    for v in mapped.values():
        u = ElementTree.SubElement(h, "url")
        e = ElementTree.SubElement(u, "loc")
        e.text = v["url"]
        m = ElementTree.SubElement(u, "lastmod")
        m.text = v["modified"]
        p = ElementTree.SubElement(u, "priority")
        r = v["url"].replace(base, "").replace("http://", "").replace("https://", "")
        if len(r) == 0:
            p.text = "1.00"
            continue
        if r[0] == "/":
            r = r[1:]
        p.text = f"{((100.00 - float(len(r))) / 100.00):.2f}"
    x = ElementTree.ElementTree(h)
    x.write(sitemap)
    del h
    del x


class Page(object):
    def __init__(self, url, full_url, valid, links=None, data=None):
        self.url = url
        self.hash = None
        self.links = links
        self.valid = valid
        self.full = full_url
        if data is not None:
            h = md5()
            h.update(data)
            self.hash = h.hexdigest()
            del h

    @staticmethod
    def get(full_url):
        u = _parse(full_url)
        try:
            with get(full_url, stream=True, timeout=5) as p:
                if p.status_code != 200:
                    return Page(u, full_url, False)
                c = p.headers.get("Content-Type", None)
                if c is None or "html" not in c:
                    return Page(u, full_url, False)
                v = BeautifulSoup(p.content, "lxml")
                return Page(u, full_url, True, v.find_all("a"), p.content)
        except (UnicodeDecodeError, ValueError, IOError) as err:
            print(f'Error processing "{full_url}": {err}', file=stderr)
        return Page(u, full_url, False)


class Scanner(object):
    def __init__(self, url):
        self.url = url
        self.scanned = dict()
        self.base = _parse(url)

    def _in_scope(self, url):
        if len(url) == 0:
            return False
        if url[0] == "/":
            return True
        return url.startswith(self.base)

    def _map_urls(self, last):
        c = dict()
        for v in self.scanned.values():
            if not v.valid or v.hash is None:
                continue
            if v.url in last:
                if last[v.url].get("hash", None) == v.hash:
                    c[v.url] = {
                        "url": v.full,
                        "hash": v.hash,
                        "modified": last[v.url].get(
                            "modified",
                            datetime.now()
                            .astimezone()
                            .replace(microsecond=0)
                            .isoformat(),
                        ),
                    }
                    continue
            c[v.url] = {
                "url": v.full,
                "hash": v.hash,
                "modified": datetime.now()
                .astimezone()
                .replace(microsecond=0)
                .isoformat(),
            }
        return c

    def _is_scanned(self, url):
        return url in self.scanned

    def _scan(self, full_url, limit):
        p = Page.get(full_url)
        self.scanned[p.url] = p
        if len(self.scanned) > limit:
            return
        if not p.valid or not isinstance(p.links, list):
            return
        for e in p.links:
            v = e.get("href")
            if v is None or len(v) == 0:
                continue
            u = _parse(v)
            if not self._in_scope(u):
                continue
            if self._is_scanned(u):
                continue
            del u
            self._scan(v, limit)
            del v

    def scan(self, sitemap=None, db=None, limit=512):
        try:
            self._scan(self.url, limit)
        except Exception as err:
            raise OSError(f"Error during scanning: {err}")
        if sitemap is None:
            return self.scanned
        v = dict()
        if isinstance(db, str) and len(db) > 0 and exists(db):
            try:
                with open(db) as f:
                    v = loads(f.read())
            except (JSONDecodeError, OSError) as err:
                raise OSError(f'Error when attempting to read "{db}": {err}')
        if not isinstance(v, dict):
            v = dict()
        m = self._map_urls(v)
        del v
        if isinstance(db, str) and len(db) > 0:
            try:
                with open(db, "w") as f:
                    f.write(dumps(m))
            except OSError as err:
                raise OSError(f'Error when attempting to write "{db}": {err}')
        try:
            _gen_sitemap(self.base, sitemap, m)
        except Exception as err:
            raise OSError(f'Error writing XML sitemap to "{sitemap}": {err}')
        finally:
            del m


if __name__ == "__main__":
    if len(argv) != 4:
        print(f"{argv[0]} <url> <database> <sitemap>")
        exit(1)
    try:
        Scanner(argv[1]).scan(argv[3], argv[2])
    except OSError as err:
        print(str(err), file=stderr)
        exit(1)
