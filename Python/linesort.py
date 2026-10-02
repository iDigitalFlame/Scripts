#!/usr/bin/python3
#
# Copyright (C) 2020 - 2026 iDigitalFlame
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

from glob import glob
from sys import stdout
from io import StringIO
from subprocess import PIPE, Popen
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile
from os.path import isdir, expanduser, expandvars


def _is_comment(v):
    return (
        v.startswith("//")
        or v.startswith("#")
        or v.startswith(";")
        or v.startswith("--")
    )


def _get_sep(v):
    a, b, c, d = v.find(" "), v.find("="), v.find(","), v.find(":")
    if a == -1:
        a = len(v)
    if b == -1:
        b = len(v)
    if c == -1:
        c = len(v)
    if d == -1:
        d = len(v)
    i = min(a, b, c, d)
    del a, b, c, d
    if i < len(v):
        return v[i]
    del i
    if " " in v:
        return " "
    return None


class Sort(object):
    __slots__ = ("pad", "header", "sections")

    def __init__(self, file):
        self.pad = 0
        self.header = list()
        self.sections = list()
        self._fill(file)

    def _fill(self, file):
        with open(file) as f:
            d = f.read().split("\n")
        if len(d) == 0:
            return
        n = 0
        while n < len(d):
            if len(d[n]) == 0:
                n += 1
                continue
            if _is_comment(d[n]):
                self.header.append(d[n])
            else:
                break
            n += 1
        while n < len(d):
            v = Section()
            i, p = v._fill(d[n:])
            if i == -1:
                break
            if p > 0 and p > self.pad:
                self.pad = p
            self.sections.append(v)
            n += i
            del i, p, v
        for i in self.sections:
            if self.pad > i.pad:
                i.pad = self.pad

    def _print(self, buf, alpha, pad, sort):
        if len(self.header) > 0:
            buf.write(f'{"\n".join(self.header)}\n\n')
        if sort:
            self.sections.sort(key=lambda x: x.head)
        for v in range(0, len(self.sections)):
            if v > 0:
                buf.write("\n")
            i = self.sections[v]
            i.sort(alpha)
            if pad and i.sep != " ":
                a = 1
            else:
                a = 0
            if i.head is not None and len(i.head) > 0:
                if _is_comment(i.head):
                    buf.write(f"{i.head}\n")
                else:
                    buf.write(f"[{i.head}]\n")
            for x in i.lines:
                x.print(buf, i.pad + a if pad else None, i.sep)
            del i
        del a

    def print(self, output=None, alpha=False, pad=True, sort=False):
        if not isinstance(output, str) or len(output) == 0:
            return self._print(stdout, alpha, pad, sort)
        with open(expanduser(expandvars(output)), "w") as f:
            self._print(f, alpha, pad, sort)


class Section(object):
    __slots__ = ("pad", "sep", "head", "lines")

    def __init__(self):
        self.pad = -1
        self.sep = None
        self.head = ""
        self.lines = list()

    def _fill(self, b):
        n = 0
        if b[0].startswith("[") and b[0].endswith("]"):
            self.head = b[0][1:-1]
            n = 1
        elif _is_comment(b[0]):
            self.head = b[0]
            n = 1
        while n < len(b):
            if len(b[n]) == 0:
                n += 1
                break
            if b[n].startswith("[") and b[n].endswith("]"):
                break
            if _is_comment(b[n]):
                n += 1
                continue
            if self.sep is None:
                self.sep = _get_sep(b[n])
            if self.sep is None:
                self.lines.append(SectionLine(b[n]))
            else:
                v = SectionLine(b[n], self.sep)
                if len(v.key) > self.pad:
                    self.pad = len(v.key)
                self.lines.append(v)
                del v
            n += 1
        return n, self.pad

    def sort(self, alpha_only=False):
        self.lines.sort(key=lambda x: x.sort(alpha_only), reverse=False)


class SectionLine(object):
    __slots__ = ("key", "value")

    def __init__(self, line, sep=None):
        if sep is None:
            self.key, self.value = line.strip(), None
        else:
            v = line.find(sep)
            self.key, self.value = line[:v].strip(), line[v + 1 :].strip()
            del v

    def sort(self, alpha):
        v = 0
        if self.value is not None:
            v = len(self.value)
        if alpha:
            return (self.key, v)
        return ((len(self.key), self.key), v)

    def print(self, buf, pad, sep):
        if pad is None:
            if self.value is None:
                return buf.write(f"{self.key}\n")
            if sep == "=":
                if self.value is None or len(self.value) == 0:
                    return buf.write(f"{self.key} =\n")
                return buf.write(f"{self.key} = {self.value}\n")
            return buf.write(f"{self.key}{sep}{self.value}\n")
        n = (pad - len(self.key)) * " "
        if self.value is None:
            v = ""
        else:
            v = self.value
        if sep is None:
            buf.write(f"{self.key}\n")
        elif sep == " ":
            buf.write(f"{self.key}{n} {v}\n")
        elif sep == ":":
            buf.write(f"{self.key}:{n} {v}\n")
        elif sep == ",":
            buf.write(f"{self.key}{n}, {v}\n")
        elif self.value is None or len(self.value) == 0:
            buf.write(f"{self.key}{n}{sep}\n")
        else:
            buf.write(f"{self.key}{n}{sep} {v}\n")
        del n, v


def _main():
    p = ArgumentParser(description="Linesort")
    p.add_argument(
        "-a",
        "--alpha",
        dest="alpha",
        help="Don't sort with length, sort by alpha only",
        action="store_true",
        required=False,
    )
    p.add_argument(
        "-p",
        "--pad",
        dest="pad",
        help="Pad the sorting output",
        action="store_true",
        required=False,
    )
    p.add_argument(
        "-d",
        "--diff",
        dest="diff",
        help="Run diff and produce output",
        action="store_true",
        required=False,
    )
    p.add_argument(
        "-q",
        "--quick",
        dest="quick",
        help="Don't run diff, just indicate if files are different",
        action="store_true",
        required=False,
    )
    p.add_argument(
        "-r",
        "--replace",
        dest="replace",
        help="Replace the old file contents with the updated data",
        action="store_true",
        required=False,
    )
    p.add_argument(
        "-o",
        "--output",
        dest="out",
        help="File to output to, omit to output to stdout",
        type=str,
        action="store",
        required=False,
    )
    p.add_argument(
        "-z",
        "--sort-sections",
        dest="sort",
        help="Sort sections alphabetically",
        action="store_true",
        required=False,
    )
    p.add_argument(
        nargs=1, dest="file", help="The file to parse.", type=str, action="store"
    )
    a = p.parse_args()
    v = glob(a.file[0], recursive=True, include_hidden=False)
    del p
    if len(v) == 1:
        return _process(v[0], a.diff, a.alpha, a.pad, a.quick, a.out, a.replace, a.sort)
    for i in v:
        if isdir(i):
            continue
        _process(i, a.diff, a.alpha, a.pad, a.quick, None, a.replace, a.sort)


def _process(file, diff, alpha, pad, quick, out, replace, sort):
    p = expanduser(expandvars(file))
    v = Sort(p)
    if not diff:
        if replace and out is None:
            return v.print(p, alpha, pad, sort)
        return v.print(out, alpha, pad, sort)
    b = StringIO()
    v._print(b, alpha, pad, sort)
    r = b.getvalue()
    b.close()
    del b
    with open(p) as f:
        if f.read() == r:
            if quick:
                return
            return print(f"{p} is properly formatted!")
    if quick:
        return print(f"{p} needs updating!")
    t = NamedTemporaryFile("w")
    t.write(r)
    del r
    t.flush()
    v = Popen(
        ["/usr/bin/diff", "-ry", p, t.name],
        text=True,
        shell=False,
        stdout=PIPE,
        stderr=PIPE,
        universal_newlines=True,
    )
    o, _ = v.communicate()
    print(f"< {p} | > Updated\n{'=' * 65}\n{o}")
    f.close()
    del f, o, p, v


if __name__ == "__main__":
    _main()
