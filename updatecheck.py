#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

from __future__ import unicode_literals, division, absolute_import, print_function

import re
import os
import sys
from datetime import datetime, timedelta
from pkg_resources import parse_version

def string_to_date(datestring):
    return datetime.strptime(datestring, "%Y-%m-%d %H:%M:%S.%f")

class UpdateChecker():
    '''
    self.delta              : How often to check -- in hours
    self.url                : url to github xml file
    self.lasttimechecked    : 'stringified' datetime object of last check
    self.lastonlineversion : version string of last online version retrieved/stored
    self.w                  : bk._w from plugin.py
    '''
    def __init__(self, url, lasttimechecked, lastonlineversion, w):
        self.delta = 6
        self.url = url
        self.lasttimechecked = string_to_date(lasttimechecked)  # back to datetieme object
        self.lastonlineversion = lastonlineversion
        self.w = w

    def get_online_version(self):
        _online_version = None
        _version_pattern = re.compile(r'<current-version>([^<]*)</current-version>')

        import socket
        try:
            from urllib.request import urlopen
        except ImportError:
            from urllib import urlopen
        socket.setdefaulttimeout(3)

        # get the latest version from the plugin's github page
        try:
            response = urlopen(self.url)
            the_page = response.read()
            the_page = the_page.decode('utf-8', 'ignore')
            m = _version_pattern.search(the_page)
            if m:
                _online_version = (m.group(1).strip())
        except:
            pass
        return _online_version

    def get_current_version(self):
        _version_pattern = re.compile(r'<version>([^<]*)</version>')
        _installed_version = None

        ppath = os.path.join(self.w.plugin_dir, self.w.plugin_name, "plugin.xml")
        with open(ppath,'rb') as f:
            data = f.read()
            data = data.decode('utf-8', 'ignore')
            m = _version_pattern.search(data)
            if m:
                _installed_version = m.group(1).strip()
        return _installed_version

    def is_newer(self, online_version, current_version):
        return (parse_version(online_version) > parse_version(current_version))

    def update_info(self):
        _online_version = None
        _current_version = self.get_current_version()

        # only retrieve online resource if the allotted time has passed since last check
        if (datetime.now() - self.lasttimechecked > timedelta(hours=self.delta)):
            _online_version = self.get_online_version()
            if _online_version is not None and self.is_newer(_online_version, _current_version) and _online_version != self.lastonlineversion:
                return True, _online_version, str(datetime.now())
        return False, _online_version, str(datetime.now())

def main():
    url = 'https://raw.githubusercontent.com/dougmassay/punctuationsmarten-sigil-plugin/master/checkversion.xml'
    tmedt = str(datetime.now() - timedelta(hours=7))
    version = '0.1.0'
    chk = UpdateChecker(url, tmedt, version)
    print(chk.update_info())

if __name__ == "__main__":
    sys.exit(main())
