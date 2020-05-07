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
import json

from optparse import OptionParser

try:
    import requests
except ImportError:
    print("You must install requests in order to use this!")
    print("\tpip install requests")
    sys.exit(-1)

IP_LOOKUP = "http://freegeoip.net/json/%s"


def _main():
    inputc = OptionParser()
    inputc.add_option(
        "-t",
        "--target",
        dest="target",
        help="IPs/FQDNs of Targets (Comma Seperated)",
        default=None,
    )
    inputc.add_option(
        "-o", "--out", dest="output", help="Output data to file", default=None
    )
    inputc.add_option(
        "-i",
        "--in",
        dest="input",
        help="Input file with IPs/FQDN (CSV/Newline)",
        default=None,
    )
    inputc.add_option(
        "-c",
        "--csvcol",
        dest="csvcol",
        help="CSV Column to use (If CSV is used)",
        default=None,
    )
    (targs, arg) = inputc.parse_args()
    if not targs:
        print("Incorrect args!  Please use shovel.py -h")
        sys.exit(-1)
    if targs.target and targs.input:
        print("[ERROR] You must select an input using (-t) or (-i)!")
        sys.exit(-1)
    if targs.input:
        rval = targs.input
        if rval and ".csv" in rval and not targs.csvcol:
            print("[ERROR] You must sepecify a CSV Column using (-c)!")
            sys.exit(-1)
    ip_s = None
    ip_list = []
    fil_out = None
    if targs.output:
        fil_out = open(targs.output, "w+")
        fil_out.write(
            "IP Address,Country,Country Code,Region,Region Code,City,Zip,Time Zone,Longitude,Latitude\r\n"
        )
    if targs.input:
        None
    elif targs.target:
        ip_s = targs.target
        if "," in ip_s:
            ip_ts = ip_s.split(",")
            for ips in ip_ts:
                ip_list.append(ips.strip())
            ip_s = None
    if ip_s:
        _doshovel_single(ip_s, fil_out)
    elif len(ip_list) > 0:
        _doshovel_multi(ip_list, fil_out)
    else:
        print("[ERROR] Could not find a correct IP/FQDN to search!")
        sys.exit(-1)
    print("Done.")
    sys.exit(0)


def _splash():
    print(
        """
        ___
        \_/
         |
         |
         |
         |
         |
         |
         |
       __|__
      |  ^  |
      |     |
      \ \_/ /
       '._.'
       """
    )
    print("-idf 2015")
    print("shovel.py - IP Geolocation Tool")


def _doshovel_single(ip, output=None):
    if ip:
        try:
            retval = requests.get(IP_LOOKUP % ip)
            if retval and retval.status_code == 200:
                jsn = json.loads(retval.content)
                if output:
                    output.write(
                        "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\r\n"
                        % (
                            jsn["ip"],
                            jsn["country_name"],
                            jsn["country_code"],
                            jsn["region_name"],
                            jsn["region_code"],
                            jsn["city"],
                            jsn["zip_code"],
                            jsn["time_zone"],
                            jsn["latitude"],
                            jsn["longitude"],
                        )
                    )
                else:
                    print(
                        "IP: %s \t> %s %s %s %s %s (%s,%s)"
                        % (
                            jsn["ip"],
                            jsn["country_name"],
                            jsn["region_code"],
                            jsn["city"],
                            jsn["zip_code"],
                            jsn["time_zone"],
                            jsn["latitude"],
                            jsn["longitude"],
                        )
                    )
            else:
                print('Could not lookup "%s" there was an issue!')
                return None
        except Exception as Ex:
            print("Problem connecting to GeoIP provider! %s" % str(Ex))
            sys.exit(-1)


def _doshovel_multi(iplist, output=None):
    for ip in iplist:
        _doshovel_single(ip, output)


if __name__ == "__main__":
    _splash()
    _main()
