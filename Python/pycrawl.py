#!/usr/bin/python3

"""
    PyCrawl
      Python Site Scanner

      Very modular and customizable.

    @iDigitalFlame
"""


import DNS
import time
import requests
import threading


from bs4 import BeautifulSoup


class PyCrawlPage:
    def __init__(self, url, size):
        self.url = url
        self.size = size


class PyCrawl(threading.Thread):

    """
        VARS


        HOOKS

        onget  - on url get (pycrawl, url) replaced by on find          >>
        onfind - on page find (pycrzwl, url, referurl)
        onsearch - on page text search (pycrawl, url, pagetext)
        onfail - on page failure (pycrawl, fail)                        >>
        onerror - on page error (pycrawl, url, exception)
        onpass - on page before search (pycrawl, url, pagetext)         >>
        onstart - on program start (pycrawl)                            >>
        onend - on program end (pycrawl)
        oncheck - on page check for valid (pycrawl, url, pagetext)      >>

    """

    def __init__(
        self,
        searchurl,
        searchsubs=None,
        debug=2,
        searchdns=None,
        searchmax=0,
        onget=None,
        onfind=None,
        onsearch=None,
        onfail=None,
        onerror=None,
        onpass=None,
        onstart=None,
        onend=None,
        oncheck=None,
        stoponerror=False,
        searchthreads=0,
        timeout=16,
    ):
        threading.Thread.__init__(self, group=None)
        self.__error = []
        self.__search = []
        self.session = None
        self.__debug = debug
        self.__onend = onend
        self.__siteip = None
        self.__onget = onget
        self.__pages = dict()
        self.__zones = dict()
        self.__url = searchurl
        self.__dns = searchdns
        self.__onfind = onfind
        self.__onfail = onfail
        self.__onpass = onpass
        self.__limit = searchmax
        self.__subs = searchsubs
        self.__onerror = onerror
        self.__onstart = onstart
        self.__oncheck = oncheck
        self.__onsearch = onsearch
        self.__urlname = searchurl
        self.__threads = searchthreads
        self.__errorstop = stoponerror
        self.__search.append(searchurl)
        if "://" in searchurl:
            slindex = searchurl.find("://")
            self.__urlname = searchurl[(slindex + 3) :]
        if ":" in self.__urlname:
            sidnx = self.__urlname.find(":")
            self.__urlname = self.__urlname[:sidnx]
        if "/" in self.__urlname:
            slindex = self.__urlname.find("/")
            self.__urlname = self.__urlname[:slindex]
        if self.__dns:
            self.__siteip = _dnslookup(self.__urlname, self.__dns)
            self.out(1, "Found IP '%s' for '%s'" % (self.__siteip, self.__urlname))

    def run(self):
        self.out(1, "Starting up PyCrawl")
        if self.__onstart:
            self.out(0, "Running 'onstart' hook")
            try:
                self.__onstart(self)
            except:
                self.out(2, "'on start' failed to run!")
        while len(self.__search) > 0 and (
            self.__limit == 0 or len(self.__pages) < self.__limit
        ):
            surl = self.__search.pop()
            self.out(0, "Begining search on '%s'" % surl)
            res = self.valid(surl)
            if res:
                print("URL:// + %s" % res)
                if self.__onpass:
                    self.out(0, "Running 'onpass' hook")
                    try:
                        self.__onpass(self, surl)
                    except:
                        self.out(2, "'onpass' failed to run!")
                if surl and self.__isrdy(surl):
                    self.out(0, "'%s' passed, searching!" % surl)
                    res2 = self.__getpage(surl, res)
                    if res2 and isinstance(res2, list):
                        for urll in res2:
                            self.__search.append(urll)
            else:
                if self.__onfail:
                    self.out(0, "Running 'onfail' hook")
                    try:
                        self.__onfail(self, surl)
                    except:
                        self.out(2, "'omfail' failed to run!")

    def __getpage(self, url, urlhead):
        if not url:
            self.out(3, "The url given is invalid!")
            return None
        if self.__onget:
            self.out(0, "Running 'onget' hook")
            ret = self.__onget(self, url)
            if ret and ret is False:
                self.out(1, "'onget' hook blocked url '%s'" % url)
                return None
        pageurl = url
        if self.__dns and urlhead in self.__zones:
            pageurl.replace(urlhead, self.__zones[urlhead])
            self.out(
                0,
                "Replacing DNS Hostname '%s' with '%s'"
                % (urlhead, self.__zones[urlhead]),
            )
        try:
            result = None
            if self.session and isinstance(self.session, requests.sessions.Session):
                result = self.session.get()
            None
        except Exception as ErrorMessage:
            None
        return url

    def __isrdy(self, url):
        if url in self.__search:
            return False
        if url in self.__error:
            return False
        return True

    def valid(self, url):
        self.out(0, "Validating url '%s'" % url)
        if url.startswith("mailto"):
            self.out(0, "Got mail address")
            return None
        if self.__oncheck:
            self.out(0, "Running 'oncheck' hook")
            try:
                ret = self.__oncheck(self, url)
            except:
                self.out(2, "'on hook' failed to run!")
                ret = None
            if not ret is None and ret is False:
                self.out(1, "'oncheck' hook blocked url '%s'" % url)
                return None
        searchurl = url
        self.out(0, "Splicing up url")
        if "://" in url:
            slindex = url.find("://")
            searchurl = url[(slindex + 3) :]
        if ":" in searchurl:
            sidnx = searchurl.find(":")
            searchurl = searchurl[:sidnx]
        if "/" in searchurl:
            slindex = searchurl.find("/")
            searchurl = searchurl[:slindex]
        if not searchurl.endswith(self.__urlname):
            self.out(2, "Url '%s' is not in scope! (Incorrect domain)" % searchurl)
            return None
        searchurl = searchurl.replace(self.__urlname, "")
        if len(searchurl) > 0:
            if searchurl[len(searchurl) - 1] == ".":
                searchurl = searchurl[: (len(searchurl) - 1)]
            self.out(0, "Found sub '%s', testing!" % searchurl)
            if isinstance(self.__subs, list):
                self.out(0, "Searching aganist sub list")
                for sub in self.__subs:
                    if _strc(sub, searchurl):
                        if (
                            not ("%s.%s" % (sub, self.__urlname)) in self.__zones
                            and self.__dns
                        ):
                            subip = _dnslookup(
                                ("%s.%s" % (sub, self.__urlname)), self.__dns
                            )
                            if subip:
                                self.out(
                                    0,
                                    "Found ip address '%s' for subnet '%s.%s'"
                                    % (subip, sub, self.__urlname),
                                )
                                self.__zones[("%s.%s" % (sub, self.__urlname))] = subip
                        return "%s.%s" % (searchurl, self.__urlname)
            elif isinstance(self.__subs, str):
                self.out(0, "Searching aganist sub")
                if _strc(self.__subs, searchurl):
                    if (
                        not ("%s.%s" % (searchurl, self.__urlname)) in self.__zones
                        and self.__dns
                    ):
                        subip = _dnslookup(
                            ("%s.%s" % (searchurl, self.__urlname)), self.__dns
                        )
                        if subip:
                            self.out(
                                0,
                                "Foun ip address '%s' for subnet '%s.%s'"
                                % (subip, searchurl, self.__urlname),
                            )
                            self.__zones[
                                ("%s.%s" % (searchurl, self.__urlname))
                            ] = subip
                    return "%s.%s" % (searchurl, self.__urlname)
            elif not self.__subs:
                self.out(0, "Url '%s' failed! (Sub Issue)" % url)
                return None
            self.out(0, "Url '%s' failed! (Sub Issue)" % url)
            return None
        self.out(0, "Url '%s' passed!" % url)
        return self.__urlname

    def out(self, level, log):
        if self.__debug <= level:
            lvl = "Info"
            if level == 0:
                lvl = "Debug"
            elif level == 2:
                lvl = "Warning"
            elif level == 3:
                lvl = "Error"
            elif level == 4:
                lvl = "Severe"
            print(
                "[*] PyCrawl(%s) [%s>%s]: %s"
                % (self.__urlname, time.strftime("%I:%M:%S"), lvl, log)
            )

    def __pagecheck(self, url):
        None


def _strc(string1, string2):
    if string1 and string2:
        return string1.lower() == string2.lower()


def _dnslookup(name, dnsserver):
    # Ceck for null values
    if name and dnsserver:
        try:
            # Use PyDNS to lookup ip address
            dnsr = DNS.DnsRequest(
                name, qtype="A", server=[dnsserver], protocol="udp", timeout=30
            )
            # Process our request
            request = dnsr.req()
            # Go through the responses
            for dnsans in request.answers:
                if dnsans["data"]:
                    # Return our IP addr
                    return dnsans["data"]
        except:
            return None
    return None


def test(tesrss="aa"):
    print(tesrss)


def test1(test, url):
    print("lol %s" % url)
    return True


if __name__ == "__main__":
    a = PyCrawl(
        "losynth.com",
        searchsubs=["mail", "www"],
        debug=0,
        onstart=test,
        searchdns="8.8.8.8",
        oncheck=test1,
    )
    a.start()
    a.valid("https://www.losynth.com/")
