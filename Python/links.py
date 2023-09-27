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

from time import sleep
from io import StringIO
from json import loads, dumps
from requests import post, get
from os.path import isdir, join, isfile
from datetime import datetime, timedelta
from sys import argv, stderr, stdin, stdout, exit


def bookmarks_to_xml(auth, dir):
    if not isdir(dir):
        raise ValueError(f'directory path "{dir}" is not valid')
    r = get(
        "https://mail.zoho.com/api/links/me",
        headers={"Authorization": f"Bearer {auth.token()}"},
    )
    try:
        j = r.json()
    finally:
        r.close()
        del r
    if "error" in j:
        raise ValueError(j["error"])
    elif "data" not in j or "list" not in j["data"]:
        raise ValueError("api/links/me: returned an invalid response")
    e = dict()
    for i in j["data"]["list"]:
        k = i["collectionName"].lower()
        if k not in e:
            e[k] = list()
        e[k].append((i["title"], i["link"], i["summary"], i["entityId"]))
    del j
    for k, v in e.items():
        if len(v) == 0:
            continue
        b = StringIO()
        b.write(
            f'<rss version="2.0"><channel><title><![CDATA[{k.title()}]]></title><link></link><language>en-us</language>'
        )
        for i in v:
            b.write(
                f"<item><title><![CDATA[{i[0]}]]></title><link><![CDATA[{i[1]}]]></link><guid><![CDATA[{i[3]}]]></guid>"
                + f"<description><![CDATA[{i[2]}]]></description></item>"
            )
        b.write("</channel></rss>")
        p = join(dir, f"{k}.xml")
        try:
            with open(p, "w") as f:
                f.write(b.getvalue())
            print(f'Wrote {len(v)} entries to "{p}".')
        finally:
            b.close()
            del b, p
    del e


class Auth(object):
    __slots__ = (
        "_token",
        "_expires",
        "scope",
        "client_id",
        "client_secret",
        "refresh_token",
    )

    def __init__(
        self,
        scope,
        client_id,
        client_secret,
        refresh_token=None,
        token=None,
        token_expires=None,
    ):
        if refresh_token is not None:
            if not isinstance(refresh_token, str):
                raise ValueError("refresh_token is invalid")
            elif len(refresh_token) == 0:
                self.refresh_token = None
            else:
                self.refresh_token = refresh_token
        else:
            self.refresh_token = None
        if isinstance(scope, list) and len(scope) > 0:
            if not isinstance(scope[0], str):
                raise ValueError("scope list must only contain string values")
            self.scope = ",".join(scope)
        elif isinstance(scope, str):
            self.scope = scope
        elif scope is None:
            self.scope = None
        else:
            raise ValueError("scope is invalid")
        if not isinstance(client_id, str) or len(client_id) == 0:
            raise ValueError("client_id is invalid or empty")
        if not isinstance(client_secret, str) or len(client_secret) == 0:
            raise ValueError("client_secret is invalid or empty")
        if token is not None:
            if not isinstance(token, str):
                raise ValueError("token is invalid")
            if len(token) == 0:
                self._token = None
                self._expires = None
            else:
                if token_expires is None:
                    raise ValueError(
                        "token_expires cannot be invalid or empty when supplying a token"
                    )
                if not isinstance(token_expires, (str, datetime)):
                    raise ValueError("token_expires is invalid")
                elif isinstance(token_expires, str):
                    if len(token_expires) == 0:
                        raise ValueError("token_expires is empty")
                    self._expires = datetime.fromisoformat(token_expires)
                else:
                    self._expires = token_expires
                self._token = token
            if self._expires < datetime.now():
                self._token = None
                self._expires = None
        else:
            self._token = None
            self._expires = None
        self.client_id = client_id
        self.client_secret = client_secret

    def token(self):
        try:
            if self._token is None:
                if self.refresh_token is not None:
                    self._refresh_token()
                else:
                    self._create_token()
            elif self._expires is not None and self._expires > datetime.now():
                pass
            else:
                if self.refresh_token is not None:
                    self._refresh_token()
                else:
                    self._create_token()
        except OSError as err:
            raise ValueError(err) from err
        return self._token

    def token_details(self):
        self.token()
        if isinstance(self._expires, str):
            return (self._token, self._expires)
        elif not isinstance(self._expires, datetime):
            raise ValueError("token_expires was not populated")
        return (self._token, self._expires.isoformat())

    def _create_token(self):
        if not stdin.isatty() or not stdout.isatty():
            raise OSError(
                "cannot register an initial token without an interactive console"
            )
        q = (
            "https://accounts.zoho.com/oauth/v3/device/code?grant_type=device_request&client_id="
            + self.client_id
            + "&access_type=offline"
        )
        if self.scope is not None:
            q += f"&scope={self.scope}"
        try:
            r = post(q)
        finally:
            del q
        try:
            j = r.json()
        finally:
            r.close()
            del r
        if "error" in j:
            raise ValueError(j["error"])
        elif "device_code" not in j or "verification_uri_complete" not in j:
            raise ValueError("oauth/v3/device/code: returned an invalid response")
        print(
            f'Please use your browser to access "{j["verification_uri_complete"]}" to authorize the application.',
            file=stdout,
        )
        q = (
            "https://accounts.zoho.com/oauth/v3/device/token?grant_type=device_token&client_id="
            + self.client_id
            + "&client_secret="
            + self.client_secret
            + "&code="
            + j["device_code"]
        )
        try:
            for _ in range(0, 20):
                print("Waiting to check..", file=stdout)
                sleep(35)
                r = post(q)
                try:
                    o = r.json()
                finally:
                    r.close()
                    del r
                if "error" in o and o["error"] != "authorization_pending":
                    raise ValueError(o["error"])
                if "error" in o and o["error"] == "authorization_pending":
                    del o
                    print("Authorization still pending..", file=stdout)
                    continue
                if "access_token" not in o or "refresh_token" not in o:
                    raise ValueError(
                        "oauth/v3/device/code: returned an invalid response"
                    )
                print("Received authorization!", file=stdout)
                self._token = o["access_token"]
                self.refresh_token = o["refresh_token"]
                self._expires = datetime.now() + timedelta(seconds=o["expires_in"])
                del o
                break
            if self._token is None:
                raise ValueError("timeout waiting for token authorization")
        finally:
            del q

    def _refresh_token(self):
        r = post(
            "https://accounts.zoho.com/oauth/v2/token?grant_type=refresh_token&redirect_uri=localhost&refresh_token="
            + self.refresh_token
            + "&client_id="
            + self.client_id
            + "&client_secret="
            + self.client_secret
        )
        try:
            j = r.json()
        finally:
            r.close()
            del r
        if "error" in j:
            raise ValueError(j["error"])
        if "access_token" not in j:
            raise ValueError("oauth/v3/device/code: returned an invalid response")
        self._token = j["access_token"]
        self._expires = datetime.now() + timedelta(seconds=j["expires_in"])
        del j


if __name__ == "__main__":
    if len(argv) != 4:
        print(f"{argv[0]} <config_file> <state_file> <dir>", file=stderr)
        exit(2)

    if not isfile(argv[1]):
        print(f'Config file "{argv[1]}" does not exist!', file=stderr)
        exit(1)
    if not isdir(argv[3]):
        print(f'Directory path "{argv[3]}" is invalid!', file=stderr)
        exit(1)
    try:
        with open(argv[1]) as f:
            d = loads(f.read())
    except Exception as err:
        print(f'Could not read config file "{argv[1]}": {err}!', file=stderr)
        exit(1)
    if not isinstance(d, dict) or len(d) == 0:
        print(f'Config file "{argv[1]}" is invalid!', file=stderr)
        exit(1)
    if "client_id" not in d:
        print(f'Config file "{argv[1]}" is missing value "client_id"!', file=stderr)
        exit(1)
    if "client_secret" not in d:
        print(f'Config file "{argv[1]}" is missing value "client_secret"!', file=stderr)
        exit(1)
    if isfile(argv[2]):
        try:
            with open(argv[2]) as f:
                s = loads(f.read())
        except Exception as err:
            print(f'Could not read state file "{argv[2]}": {err}!', file=stderr)
            exit(1)
    else:
        s = dict()

    try:
        a = Auth(
            "ZohoMail.links.READ",
            d["client_id"],
            d["client_secret"],
            s.get("refresh_token"),
            s.get("token"),
            s.get("token_expires"),
        )
        t, e = a.token_details()
    except Exception as err:
        print(f"Could not setup authentication: {err}!", file=stderr)
        exit(1)
    del s, d
    try:
        v = dumps(
            {
                "token": t,
                "token_expires": e,
                "refresh_token": a.refresh_token,
            }
        )
        with open(argv[2], "w") as f:
            f.write(v)
        del v
    except Exception as err:
        print(f"Could not save authentication state: {err}!", file=stderr)
        exit(1)
    del t
    try:
        bookmarks_to_xml(a, argv[3])
    except Exception as err:
        print(f"Could not download/save bookmarks: {err}!", file=stderr)
        exit(1)
