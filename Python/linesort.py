#!/usr/bin/python3

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

for l in rd.split("\n"):
    if len(l) >= 1 and (l[0] == "#" or l[0] == ";"):
        cm.append(l)
    elif len(l) >= 2 and l[0] == "/" and l[1] == "/":
        cm.append(l)
    else:
        ma = None
        if ", " in l and (mxt is None or mxt == ", "):
            ma = l.index(", ")
            mxt = ", "
        elif "= " in l and (mxt is None or mxt == "= "):
            ma = l.index("= ")
            mxt = "= "
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

sl.sort(key=len)

if mx > 0:
    mxl = (mx // 4) * 4
    if mxl < mx:
        mx = mxl + 4
    print(
        '[V] Detected delim "%s" with max line length of "%d"' % (mxt, mx),
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
