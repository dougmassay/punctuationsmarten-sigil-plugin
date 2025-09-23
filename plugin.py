#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import os
import sys
import codecs

from uuid import uuid4
from newsmartypants import smartyPants

from utilities import unescape

from plugin_utils_light import PluginApplication
from plugin_utils_light import iswindows

from dialogs import guiMain

DEBUG = 0

AMPERSAND = 'ampersand'+str(uuid4())


def parseExceptionsFile(filename):
    safename = filename
    words_list = []
    snippet = min(32, os.path.getsize(safename))
    raw = open(safename, 'rb').read(snippet)
    if raw.startswith(codecs.BOM_UTF8):
        enc = 'utf-8-sig'
    else:
        encodings = ['utf-8', 'utf-16' 'windows-1252', 'windows-1250']
        for e in encodings:
            try:
                fh = open(safename, 'r', encoding=e)
                fh.readlines()
                fh.seek(0)
            except UnicodeDecodeError:
                print(f'Got unicode error with {e}, trying different encoding')
            else:
                break
        enc = e
    try:
        with open(safename, 'r', encoding=enc) as fd:
            words_list = [line.rstrip() for line in fd]
        # words_list = filter(None, words_list)
        words_list = [_f for _f in words_list if _f]
        print(f'Parsing apostrophe exception file {filename}')
    except Exception:
        print(f'Error parsing apostrophe exception file {filename}: ignoring')
        words_list = []
    return words_list

def run(bk):
    mdp = True if iswindows else False
    app = PluginApplication(sys.argv, bk, match_dark_palette=mdp)
    w = guiMain()  # noqa F841
    app.exec()

    # Get the criteria needed to run SmartyPants on each file selected
    CRITERIA = app.app_results

    NO_CHANGE = True
    if len(CRITERIA):
        if DEBUG:
            print(CRITERIA)
        apos_words_list = []
        if CRITERIA['apos_exception_file'] is not None:
            apos_words_list = parseExceptionsFile(CRITERIA['apos_exception_file'])

        if len(CRITERIA['files']):
            for html_file in CRITERIA['files']:
                id = bk.href_to_id(html_file)
                html = bk.readfile(id)

                if not isinstance(html, str):
                    html = str(html, 'utf-8')

                html_orig = html

                # Slightly mangle all preexisting entities so HTMLParser
                # ignores them. We'll put them all back at the end.
                html = html.replace('&', AMPERSAND)

                html = smartyPants(html, CRITERIA['smarty_attr'], AMPERSAND, apos_words_list)

                if CRITERIA['use_unicode']:
                    # Convert the entities we created to unicode characters
                    html = unescape(html)
                # Unmangle the pre-existing entities
                html = html.replace(AMPERSAND, '&')
                if not html == html_orig:
                    NO_CHANGE = False
                    bk.writefile(id, html)
                    print(f'Changes made to {html_file}')
                else:
                    print(f'No changes made to {html_file}')

        if NO_CHANGE:
            print('No files were altered')

    return 0

def main():
    print('I reached main when I should not have\n')
    return -1


if __name__ == "__main__":
    sys.exit(main())
