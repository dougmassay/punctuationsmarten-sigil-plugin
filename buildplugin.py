#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

import os
import sys
import re
import glob
import shutil
import inspect
import zipfile


SCRIPT_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
PLUGIN_NAME = 'PunctuationSmarten'
TEMP_DIR = os.path.join(SCRIPT_DIR, PLUGIN_NAME)

PLUGIN_FILES = ['newsmartypants.py',
            'plugin.py',
            'plugin.xml',
            'utilities.py']

def findVersion():
    _version_pattern = re.compile(r'<version>([^<]*)</version>')
    with open('plugin.xml', 'r') as fd:
        data = fd.read()
    match = re.search(_version_pattern, data)
    if match is not None:
        return '{}'.format(match.group(1))
    return '0.X.X'

# Find version info from plugin.xml and build zip file name from it
VERS_INFO =  findVersion()
ARCHIVE_NAME = os.path.join(SCRIPT_DIR, '{}_v{}.zip'.format(PLUGIN_NAME, VERS_INFO))


# recursive zip creation support routine
def zipUpDir(myzip, tdir, localname):
    currentdir = tdir
    if localname != "":
        currentdir = os.path.join(currentdir,localname)
    dir_contents = os.listdir(currentdir)
    for entry in dir_contents:
        afilename = entry
        localfilePath = os.path.join(localname, afilename)
        realfilePath = os.path.join(currentdir, entry)
        if os.path.isfile(realfilePath):
            myzip.write(realfilePath, localfilePath, zipfile.ZIP_DEFLATED)
        elif os.path.isdir(realfilePath):
            zipUpDir(myzip, tdir, localfilePath)

def removePreviousTmp(rmzip=False):
    # Remove temp folder and contents if it exists
    if os.path.exists(TEMP_DIR) and os.path.isdir(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

    if rmzip:  # Remove zip file if indicated
        print ('Removing any current zip file ...')
        if os.path.exists(ARCHIVE_NAME):
            os.remove(ARCHIVE_NAME)

if __name__ == "__main__":
    print('Removing any previous build leftovers ...')
    removePreviousTmp(rmzip=True)

    # Copy everything to temp directory
    print ('Creating temp build directory ...')
    os.mkdir(TEMP_DIR)

    files = os.listdir(SCRIPT_DIR)

    print ('Copying plugin files to temporary build directory ...')
    try:
        for entry in PLUGIN_FILES:
            shutil.copy2(os.path.join(SCRIPT_DIR, entry), os.path.join(TEMP_DIR, entry))
    except:
        sys.exit('Couldn\'t copy necessary plugin files!')

    print ('Creating {} ...'.format(os.path.basename(ARCHIVE_NAME)))
    outzip = zipfile.ZipFile(ARCHIVE_NAME, 'w')
    zipUpDir(outzip, SCRIPT_DIR, os.path.basename(TEMP_DIR))
    outzip.close()

    print ('Plugin successfully created!')

    print('Removing temp build directory ...')
    removePreviousTmp()
