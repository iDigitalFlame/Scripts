#!/usr/bin/python3
# Copyright (C) 2020 iDigitalFlame
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

import sys

if len(sys.argv) <= 1:
    print("%s <file>" % sys.argv[0], file=sys.stderr)
    sys.exit(1)

try:
    rf = open(sys.argv[1], "r")
    rd = rf.read()
    rf.close()
except IOError as err:
    print(err, file=sys.stderr)
    sys.exit(1)

mx = 0
mxt = None
cm = list()
sl = list()
pl = dict()

fl = None
if len(sys.argv) == 3:
    fl = sys.argv[2]

for l in rd.split("\n"):
    if len(l) >= 1 and (l[0] == "#" or l[0] == ";"):
        cm.append(l)
    elif len(l) >= 2 and l[0] == "/" and l[1] == "/":
        cm.append(l)
    else:
        ma = None
        if "," in l and (mxt is None or mxt == ",") and (fl is None or fl == ","):
            ma = l.index(",")
            mxt = ","
        elif "=" in l and (mxt is None or mxt == "=") and (fl is None or fl == "="):
            ma = l.index("=")
            mxt = "="
        if ma is not None:
            mx = max(mx, ma)
            ps = l.split(mxt)
            if len(ps) > 0:
                pl[ps[0]] = mxt.join(ps[1:])
                sl.append(ps[0])
            else:
                sl.append(l)
        else:
            sl.append(l)

if len(sys.argv) == 2:
    sl.sort(key=len)

if mx > 0:
    mxl = (mx // 4) * 4
    if mxl < mx:
        mx = mxl + 4
    print(
        '[V] Detected delimiter "%s" with max line length of "%d"' % (mxt, mx),
        file=sys.stderr,
    )
else:
    mx = None

for k in cm:
    print(k)
for k in sl:
    if mx is not None:
        if k in pl:
            print("%s%s%s" % (k.ljust(mx), mxt, pl[k]))
        else:
            k1 = k.split(mxt)
            if len(k1) == 2:
                print("%s%s%s" % (k1[0].ljust(mx), mxt, k1[1]))
            else:
                print(k)
    else:
        print(k)
