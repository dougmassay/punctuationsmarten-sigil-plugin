# -*- coding: utf-8 -*-
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

import sys
import os
import re
import inspect

import socket
from datetime import datetime, timedelta
import html.entities as htmlentitydefs

url = 'https://raw.githubusercontent.com/dougmassay/punctuationsmarten-sigil-plugin/master/checkversion.xml'
delta = 12

SCRIPT_DIR = os.path.normpath(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
PLUGIN_NAME = os.path.split(SCRIPT_DIR)[-1]
HOME_URL = 'http://www.mobileread.com/forums/showthread.php?t=247088'


gui_selections = {
    'educateQuotes'   : 1,
    'dashes'          : 1,
    'educateEllipses' : 1,
    'useFile'         : 0,
    'useFilePath'     : '',
    'useUnicodeChars' : 1,
}

miscellaneous_settings = {
    'windowGeometry' : None,
    'lastDir'        : os.path.expanduser('~'),
}

update_settings = {
    'last_time_checked'   : str(datetime.now() - timedelta(hours=7)),
    'last_online_version' : '0.1.0',
}


def setupPrefs(prefs):
    if 'gui_selections' not in prefs:
        prefs['gui_selections'] = gui_selections
    if 'miscellaneous_settings' not in prefs:
        prefs['miscellaneous_settings'] = miscellaneous_settings
    if 'update_settings' not in prefs:
        prefs['update_settings'] = update_settings
    return prefs


def unescape(text):
    """Removes HTML or XML character references
      and entities from a text string.
    @param text The HTML (or XML) source text.
    @return The plain text, as a Unicode string, if necessary.
    from Fredrik Lundh
    2008-01-03: input only unicode characters string.
    http://effbot.org/zone/re-sub.htm#unescape-html
    """
    def fixup(m):
        text = m.group(0)
        if text[:2] == '&#':
            # character reference
            try:
                if text[:3] == '&#x':
                    return chr(int(text[3:-1], 16))
                else:
                    return chr(int(text[2:-1]))
            except ValueError:
                print('Value Error')
                pass
        else:
            # named entity
            # reescape the reserved characters.
            try:
                if text[1:-1] == 'amp':
                    text = '&amp;amp;'
                elif text[1:-1] == 'gt':
                    text = '&amp;gt;'
                elif text[1:-1] == 'lt':
                    text = '&amp;lt;'
                else:
                    text = chr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                print('KeyError')
                pass
        return text  # leave as is
    return re.sub(r"""&#?\w+;""", fixup, text)


def string_to_date(datestring):
    return datetime.strptime(datestring, "%Y-%m-%d %H:%M:%S.%f")


def tuple_version(v):
    # No aplha characters in version strings allowed here!
    return tuple(map(int, (v.split("."))))


class UpdateChecker():
    '''
    self.delta              : How often to check -- in hours
    self.url                : url to github xml file
    self.lasttimechecked    : 'stringified' datetime object of last check
    self.lastonlineversion  : version string of last online version retrieved/stored
    self.w                  : bk._w from plugin.py
    '''
    def __init__(self, lasttimechecked, lastonlineversion, w):
        self.delta = delta
        self.url = url
        self.lasttimechecked = string_to_date(lasttimechecked)  # back to datetieme object
        self.lastonlineversion = lastonlineversion
        self.w = w

    def is_connected(self):
        try:
            # connect to the host -- tells us if the host is reachable
            # 8.8.8.8 is a Google nameserver
            sock = socket.create_connection(('8.8.8.8', 53), 1)
            sock.close()
            return True
        except Exception:
            pass
        return False

    def get_online_version(self):
        _online_version = None
        _version_pattern = re.compile(r'<current-version>([^<]*)</current-version>')

        try:
            from urllib.request import urlopen
        except ImportError:
            from urllib2 import urlopen

        # get the latest version from the plugin's github page
        if self.is_connected():
            try:
                response = urlopen(self.url, timeout=2)
                the_page = response.read()
                the_page = the_page.decode('utf-8', 'ignore')
                m = _version_pattern.search(the_page)
                if m:
                    _online_version = (m.group(1).strip())
            except Exception:
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

    def update_info(self):
        _online_version = None
        _current_version = self.get_current_version()

        # only retrieve online resource if the allotted time has passed since last check
        if (datetime.now() - self.lasttimechecked > timedelta(hours=self.delta)):
            _online_version = self.get_online_version()
            # if online version is newer, make sure it hasn't been seen already
            if _online_version is not None and tuple_version(_online_version) > tuple_version(_current_version) and _online_version != self.lastonlineversion:
                return True, _online_version, str(datetime.now())
        return False, _online_version, str(datetime.now())

def main():
    '''Used to test outside of Sigil'''
    class w():
        def __init__(self):
            w.plugin_name = 'PunctuationSmarten'
            w.plugin_dir = '/home/dmassay/.local/share/sigil-ebook/sigil/plugins'

    tmedt = str(datetime.now() - timedelta(hours=delta+1))
    version = '0.1.0'
    sim_w = w()
    chk = UpdateChecker(tmedt, version, sim_w)
    print(chk.update_info())
    print(tuple_version('0.80.3'))
    print(tuple_version('0.80.3') > tuple_version('0.80.1'))
    print(tuple_version('0.80.3') > tuple_version('0.80.30'))


if __name__ == "__main__":
    sys.exit(main())
