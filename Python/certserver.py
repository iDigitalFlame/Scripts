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
# On the Windows CA Side, use the PowerShell script:
#
# try {
#   Invoke-WebRequest http://<target>/<key> -Method POST -Body ((certutil -view csv) -join '`n') -Content 'text/plain'
# } catch {}
#
# to operate
# It's easiest to run this in a repeating task daily/weekly.
#

import threading

from json import loads
from html import escape
from io import StringIO
from smtplib import SMTP
from signal import SIGINT
from csv import DictReader
from os.path import isfile
from os import getpid, kill
from datetime import datetime
from sys import argv, stderr, exit
from socketserver import TCPServer
from collections import namedtuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from http.server import BaseHTTPRequestHandler

Record = namedtuple("Record", ["serial", "name", "end", "days"])


def _thread_except(args):
    print(f"Received an uncaught Thread error {args.exc_type} ({args.exc_value})!")
    kill(getpid(), SIGINT)


class CertServer(object):
    def __init__(self, config):
        if not isinstance(config, str) or len(config) == 0:
            raise ValueError('Empty or invalid "config" value!')
        if not isfile(config):
            raise OSError(f'Config path "{config}" does not exist!')
        try:
            with open(config) as f:
                c = loads(f.read())
        except Exception as err:
            raise OSError(f'Could not parse "{config}": {err}!') from err
        if not isinstance(c, dict) or len(c) == 0:
            raise ValueError(f'Config file "{config}" is empty!')
        if "key" not in c:
            raise ValueError(f'Config file "{config}" is missing the "key" value!')
        if "listen" not in c:
            raise ValueError(f'Config file "{config}" is missing the "listen" value!')
        if "mail" not in c:
            raise ValueError(f'Config file "{config}" is missing the "key" value!')
        if not isinstance(c["key"], str) or len(c["key"]) == 0:
            raise ValueError(f'Config file "{config}" value "key" is empty or invalid!')
        self.key = c["key"]
        if not isinstance(c["mail"], dict) or len(c["mail"]) == 0:
            raise ValueError(
                f'Config file "{config}" value "mail" is empty or invalid!'
            )
        if not isinstance(c["listen"], str) or len(c["listen"]) == 0:
            raise ValueError(
                f'Config file "{config}" value "listen" is empty or invalid!'
            )
        if ":" not in c["listen"]:
            raise ValueError(
                f'Config file "{config}" value "listen" must be in "host:port" format!'
            )
        v = c["listen"].find(":")
        self.host = c["listen"][:v]
        try:
            self.port = int(c["listen"][v + 1 :])
        except ValueError as err:
            raise ValueError(
                f'Config file "{config}" value "listen" has no port or it is invalid: {err}!'
            ) from err
        del v
        if "to" not in c["mail"]:
            raise ValueError(f'Config file "{config}" is missing the "mail.to" value!')
        if not isinstance(c["mail"]["to"], str) or len(c["mail"]["to"]) == 0:
            raise ValueError(
                f'Config file "{config}" value "mail.to" is empty or invalid!'
            )
        if "from" not in c["mail"]:
            raise ValueError(
                f'Config file "{config}" is missing the "mail.from" value!'
            )
        if not isinstance(c["mail"]["from"], str) or len(c["mail"]["from"]) == 0:
            raise ValueError(
                f'Config file "{config}" value "mail.from" is empty or invalid!'
            )
        if "user" not in c["mail"]:
            raise ValueError(
                f'Config file "{config}" is missing the "mail.user" value!'
            )
        if not isinstance(c["mail"]["user"], str) or len(c["mail"]["user"]) == 0:
            raise ValueError(
                f'Config file "{config}" value "mail.user" is empty or invalid!'
            )
        if "server" not in c["mail"]:
            raise ValueError(
                f'Config file "{config}" is missing the "mail.server" value!'
            )
        if not isinstance(c["mail"]["server"], str) or len(c["mail"]["server"]) == 0:
            raise ValueError(
                f'Config file "{config}" value "mail.server" is empty or invalid!'
            )
        if "password" not in c["mail"]:
            raise ValueError(
                f'Config file "{config}" is missing the "mail.password" value!'
            )
        if (
            not isinstance(c["mail"]["password"], str)
            or len(c["mail"]["password"]) == 0
        ):
            raise ValueError(
                f'Config file "{config}" value "mail.password" is empty or invalid!'
            )
        if "port" not in c["mail"]:
            raise ValueError(
                f'Config file "{config}" is missing the "mail.port" value!'
            )
        try:
            self.mail = {"port": int(c["mail"]["port"])}
        except ValueError as err:
            raise ValueError(
                f'Config file "{config}" value "mail.port" is empty or invalid: {err}!'
            ) from err
        self.mail["to"] = c["mail"]["to"]
        self.mail["from"] = c["mail"]["from"]
        self.mail["user"] = c["mail"]["user"]
        self.mail["server"] = c["mail"]["server"]
        self.mail["password"] = c["mail"]["password"]
        self.mail["tls"] = c["mail"].get("tls", False)
        del c

    def run(self):
        try:
            with TCPServer((self.host, self.port), self._spawn) as h:
                h.serve_forever()
        except KeyboardInterrupt:
            pass
        except Exception as err:
            raise OSError(f"Error running server: {err}!") from err

    def _notify(self, e):
        b, h = StringIO(), StringIO()
        for i in e:
            if b.tell() > 0:
                b.write("\n")
            b.write(f"- {i.name} [{i.serial[-6:]}] on {i.end}")
            h.write(
                f"<tr><td>{escape(i.name)}</td><td>{escape(i.serial[-6:])}</td>"
                f"<td>{escape(i.end)}"
            )
            if i.days >= 0:
                b.write(f" ({i.days} day")
                h.write(f" ({escape(i.days)} day")
                if i.days != 1:
                    b.write("s")
                    h.write("s")
                b.write(")")
                h.write(")")
            h.write("</td></tr>")
        v, r = b.getvalue(), h.getvalue()
        b.close()
        h.close()
        del b, h
        m = MIMEMultipart("alternative")
        m["Subject"] = "Certificate Expiry Notification"
        m["From"] = self.mail["from"]
        m["To"] = self.mail["to"]
        m.attach(
            MIMEText(
                f"Hello,\n\nThe following certificates will expire soon:\n"
                f"{v}\n\nTo ensure that no service interruptions occur, "
                "please renew them.\n\n- Certificate Services\n",
                "plain",
            )
        )
        m.attach(
            MIMEText(
                "<html><head></head><body><div>Hello,</div><br/>"
                "<div>The following certificates will expire soon:</div><br/>"
                "<table><tr><th>Name</th><th>Serial</th><th>Expire Date</th></tr>"
                f"<tbody>{r}</tbody></table><br/<br/><div>To ensure that no service"
                "interruptions occur, please <b>renew</b> them.</div><br/><div>"
                "- Certificate Services</div>",
                "html",
            )
        )
        del v, r
        try:
            with SMTP(self.mail["server"], self.mail["port"]) as s:
                if self.mail.get("tls", False):
                    s.starttls()
                s.login(self.mail["user"], self.mail["password"])
                s.ehlo()
                s.sendmail(self.mail["from"], [self.mail["to"]], m.as_string())
        except Exception as err:
            print(f"Error sending email: {err}!", file=stderr)
        del m

    def process(self, d):
        o, n, r = list(), datetime.now(), DictReader(d.split("\n"))
        for i in r:
            if i["Revocation Reason"] != "EMPTY":
                continue
            if i["Serial Number"] == "EMPTY" or i["Issued Common Name"] == "EMPTY":
                continue
            if i["Certificate Effective Date"] == "EMPTY":
                continue
            if i["Certificate Expiration Date"] == "EMPTY":
                continue
            if "SSL Certificate" not in i["Certificate Template"]:
                continue
            try:
                e = datetime.strptime(
                    i["Certificate Expiration Date"], "%m/%d/%Y %I:%M %p"
                )
            except ValueError as err:
                print(
                    f'Certificate {i["Serial Number"]}/{i["Serial Number"]} "Expiration Date" is invalid: {err}!'
                )
                continue
            if e < n:
                o.append(
                    Record(
                        i["Serial Number"],
                        i["Issued Common Name"],
                        i["Certificate Expiration Date"],
                        -1,
                    )
                )
                del e
                continue
            d = (e - n).days
            if d > 30:
                continue
            o.append(
                Record(
                    i["Serial Number"],
                    i["Issued Common Name"],
                    i["Certificate Expiration Date"],
                    d,
                )
            )
            del e, d
        del n, r
        if len(o) == 0:
            return
        self._notify(o)
        del o

    def _spawn(self, req, address, server):
        return _HTTPServer(self, req, address, server)


class _HTTPServer(BaseHTTPRequestHandler):
    def __init__(self, svc, req, address, server):
        self._svc = svc
        BaseHTTPRequestHandler.__init__(self, req, address, server)

    def do_POST(self):
        if not isinstance(self.path, str) or len(self.path) == 0:
            self.send_error(404)
            return self.end_headers()
        if self.path[1:] != self._svc.key:
            self.send_error(403)
            return self.end_headers()
        n = self.headers.get("Content-Length")
        if not isinstance(n, str) or len(n) == 0:
            self.send_error(411)
            return self.end_headers()
        try:
            x = int(n, 10)
        except ValueError:
            self.send_error(411)
            return self.end_headers()
        if x <= 0:
            self.send_error(411)
            return self.end_headers()
        try:
            d = self.rfile.read(x)
        except OSError as err:
            print(f"Could not read body: {err}!", file=stderr)
            self.send_error(500)
            return self.end_headers()
        del x
        try:
            self._svc.process(d.decode("UTF-8"))
        except Exception as err:
            print(f"Could not process body: {err}!", file=stderr)
            self.send_error(500)
            return self.end_headers()
        finally:
            del d
        self.send_response(200)
        self.wfile.write("OK".encode("UTF-8"))
        self.end_headers()


if __name__ == "__main__":
    if len(argv) <= 1:
        print(f"{argv[0]} <config>", file=stderr)
        exit(2)
    threading.excepthook = _thread_except
    try:
        CertServer(argv[1]).run()
    except Exception as err:
        print(err, file=stderr)
        exit(2)
    exit(0)
