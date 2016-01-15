#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
from __future__ import unicode_literals, division, absolute_import, print_function

import os
import sys
import inspect
import ntpath
import codecs
import re

from uuid import uuid4
from newsmartypants import smartyPants


from compatibility_utils import PY2, unicode_str, utf8_str
import unipath
from unipath import pathof
from utilities import expanduser, file_open

if PY2:
    import htmlentitydefs
    import Tkinter as tkinter
    import ttk as tkinter_ttk
    import Tkconstants as tkinter_constants
    import tkFileDialog as tkinter_filedialog
    text_type = unicode
    characterize = unichr
else:
    import html.entities as htmlentitydefs
    import tkinter
    import tkinter.ttk as tkinter_ttk
    import tkinter.constants as tkinter_constants
    import tkinter.filedialog as tkinter_filedialog
    text_type = str
    characterize = chr

SCRIPT_DIR = os.path.normpath(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
PLUGIN_NAME = os.path.split(SCRIPT_DIR)[-1]

gui_selections = {
    'educateQuotes': 1,
    'dashes': 1,
    'educateEllipses': 1,
    'useFile': 0,
    'useFilePath': '',
    'useUnicodeChars': 1,
}

miscellaneous_settings = {
    'windowGeometry': None,
    'lastDir': expanduser('~'),
}


AMPERSAND = 'ampersand'+str(uuid4())
START = 'comment-start-'+str(uuid4())
STOP = 'comment-stop-'+str(uuid4())

CRITERIA = {}
prefs = {}


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
                    return characterize(int(text[3:-1], 16))
                else:
                    return characterize(int(text[2:-1]))
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
                    text = characterize(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                print('KeyError')
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

class guiMain(tkinter.Frame):
    def __init__(self, parent, bk):
        tkinter.Frame.__init__(self, parent, border=5)
        self.parent = parent
        self.bk = bk

        self.gui_prefs = prefs['gui_selections']
        self.misc_prefs = prefs['miscellaneous_settings']

        if self.misc_prefs['windowGeometry'] is None:
            # Sane geometry defaults
            # Limit the windowflash to the first time run
            self.parent.update_idletasks()
            w = self.parent.winfo_screenwidth()
            h = self.parent.winfo_screenheight()
            rootsize = (400, 425)
            x = w/2 - rootsize[0]/2
            y = h/2 - rootsize[1]/2
            self.misc_prefs['windowGeometry'] = ('%dx%d+%d+%d' % (rootsize + (x, y)))

        self.initUI()
        parent.protocol('WM_DELETE_WINDOW', self.quitApp)

    def initUI(self):
        """ Build the GUI and assign variables and handler functions to elements. """
        self.parent.title(PLUGIN_NAME)

        body = tkinter.Frame(self)
        body.pack(fill=tkinter_constants.BOTH, expand=True)

        chk_frame2 = tkinter.Frame(body)
        self.edu_quotes = tkinter.StringVar()
        quote_checkbox = tkinter.Checkbutton(chk_frame2, text="'Educate' quotes", command=self.edu_quotesActions, variable=self.edu_quotes, onvalue='q', offvalue='')
        quote_checkbox.pack(side=tkinter_constants.LEFT, fill=tkinter_constants.BOTH)
        chk_frame2.pack(side=tkinter_constants.TOP, fill=tkinter_constants.BOTH)
        if self.gui_prefs['educateQuotes']:
            quote_checkbox.select()

        chk_frame7 = tkinter.Frame(body)
        self.use_file = tkinter.IntVar()
        self.file_checkbox = tkinter.Checkbutton(chk_frame7, text="Use apostrophe exception file", command=self.chkBoxActions, variable=self.use_file, onvalue=1, offvalue=0)
        self.file_checkbox.pack(side=tkinter_constants.LEFT, fill=tkinter_constants.BOTH)
        chk_frame7.pack(side=tkinter_constants.TOP, fill=tkinter_constants.BOTH)
        if self.gui_prefs['useFile']:
            self.file_checkbox.select()
        if not self.edu_quotes.get():
            self.file_checkbox.config(state="disabled")

        entry_frame1 = tkinter.Frame(body, bd=1)
        self.cust_file_path = tkinter.Entry(entry_frame1)
        self.cust_file_path.pack(side=tkinter_constants.LEFT, fill=tkinter_constants.BOTH, expand=1)
        self.choose_button = tkinter.Button(entry_frame1, text="...", command=self.fileChooser)
        self.choose_button.pack(side=tkinter_constants.RIGHT, fill=tkinter_constants.BOTH)
        if len(self.gui_prefs['useFilePath']):
            self.cust_file_path.insert(0, unicode_str(self.gui_prefs['useFilePath'], 'utf-8'))
        self.cust_file_path.config(state="readonly")
        if not self.use_file.get():
            self.choose_button.config(state="disabled")
        entry_frame1.pack(side=tkinter_constants.TOP, fill=tkinter_constants.BOTH)

        combo2 = tkinter.Frame(body, bd=2, relief=tkinter_constants.SUNKEN)
        dash_label = tkinter.Label(combo2, text='(EM|EN)-Dash Settings')
        dash_label.pack(fill=tkinter_constants.BOTH)
        self.dashBox_value = tkinter.StringVar()
        self.dashBox = tkinter_ttk.Combobox(combo2, textvariable=self.dashBox_value)
        self.dashBox['values'] = ('No dash support', "'--' = emdash (no endash support)", "'--' = emdash '---' = endash", "'---' = emdash '--' = endash")
        self.dashBox.current(self.gui_prefs['dashes'])
        self.dashBox.pack(side=tkinter_constants.LEFT, fill=tkinter_constants.BOTH, expand=True)
        combo2.pack(side=tkinter_constants.TOP, fill=tkinter_constants.BOTH)

        chk_frame5 = tkinter.Frame(body)
        self.edu_ellipses = tkinter.StringVar()
        ellipses_checkbox = tkinter.Checkbutton(chk_frame5, text="'Educate' ellipses", variable=self.edu_ellipses, onvalue='e', offvalue='')
        ellipses_checkbox.pack(side=tkinter_constants.LEFT, fill=tkinter_constants.BOTH)
        chk_frame5.pack(side=tkinter_constants.TOP, fill=tkinter_constants.BOTH)
        if self.gui_prefs['educateEllipses']:
            ellipses_checkbox.select()

        chk_frame10 = tkinter.Frame(body)
        self.unicodevar = tkinter.IntVar()
        unicode_checkbox = tkinter.Checkbutton(chk_frame10, text='Use Unicode Characters', variable=self.unicodevar, onvalue=1, offvalue=0)
        unicode_checkbox.pack(side=tkinter_constants.LEFT, fill=tkinter_constants.BOTH)
        chk_frame10.pack(side=tkinter_constants.TOP, fill=tkinter_constants.BOTH)
        if self.gui_prefs['useUnicodeChars']:
            unicode_checkbox.select()

        filelist_frame = tkinter.Frame(body, bd=2, relief=tkinter_constants.SUNKEN)
        filelist_label = tkinter.Label(filelist_frame, text='Select files to process:')
        filelist_label.pack(fill=tkinter_constants.BOTH)
        scrollbar = tkinter.Scrollbar(filelist_frame, orient=tkinter_constants.VERTICAL)
        self.filelist = tkinter.Listbox(filelist_frame, yscrollcommand=scrollbar.set, selectmode=tkinter_constants.EXTENDED)
        scrollbar.config(command=self.filelist.yview)
        scrollbar.pack(side=tkinter_constants.RIGHT, fill=tkinter_constants.Y)
        for (id, href) in self.bk.text_iter():
            self.filelist.insert(tkinter_constants.END, href)
        self.filelist.pack(side=tkinter_constants.LEFT, fill=tkinter_constants.BOTH, expand=1)
        filelist_frame.pack(side=tkinter_constants.TOP, fill=tkinter_constants.BOTH)

        buttons = tkinter.Frame(body)
        buttons.pack(side=tkinter_constants.BOTTOM, fill=tkinter_constants.BOTH)
        self.gbutton = tkinter.Button(
            buttons, text='Process', command=self.cmdDo)
        self.gbutton.pack(side=tkinter_constants.LEFT, fill=tkinter_constants.X, expand=1)
        self.qbutton = tkinter.Button(
            buttons, text='Quit', command=self.quitApp)
        self.qbutton.pack(side=tkinter_constants.RIGHT, fill=tkinter_constants.X, expand=1)

        self.parent.geometry(self.misc_prefs['windowGeometry'])

    def chkBoxActions(self):
        if self.use_file.get():
            self.choose_button.config(state="normal")
        else:
            self.choose_button.config(state="disabled")

    def edu_quotesActions(self):
        if self.edu_quotes.get() == 'q':
            self.file_checkbox.config(state="normal")
        else:
            self.file_checkbox.config(state="disabled")

    def cmdDo(self):
        global CRITERIA

        if self.dashBox.current() == 0:
            dash_settings = ''
        elif self.dashBox.current() == 1:
            dash_settings = 'd'
        elif self.dashBox.current() == 2:
            dash_settings = 'i'
        else:
            dash_settings = 'D'

        if self.use_file.get():
            self.cust_file_path.config(state="normal")
            if len(self.cust_file_path.get()):
                apos_exception_file = self.cust_file_path.get()
                if not unipath.exists(utf8_str(apos_exception_file)):
                    print ('Apostrophe exception file %s does not exist!' % apos_exception_file)
                    apos_exception_file = None
            else:
                apos_exception_file = None
            self.cust_file_path.config(state="readonly")
        else:
            apos_exception_file = None
        CRITERIA['apos_exception_file'] = apos_exception_file

        smarty_attr = self.edu_quotes.get() + dash_settings + self.edu_ellipses.get()
        if smarty_attr == '':
            smarty_attr = '0'
        CRITERIA['smarty_attr'] = smarty_attr

        CRITERIA['use_unicode'] = self.unicodevar.get()

        indices = self.filelist.curselection()
        CRITERIA['files'] = [self.filelist.get(index) for index in indices]

        self.quitApp()

    def fileChooser(self):
        file_opt = {}
        file_opt['parent'] = None
        file_opt['title']= 'Select exception file'
        file_opt['defaultextension'] = '.txt'
        file_opt['initialdir'] = unicode_str(self.misc_prefs['lastDir'], 'utf-8')
        file_opt['multiple'] = False
        file_opt['filetypes'] = [('Text Files', '.txt'), ('All files', '.*')]
        inpath = tkinter_filedialog.askopenfilename(**file_opt)
        if len(inpath):
            self.cust_file_path.config(state="normal")
            self.cust_file_path.delete(0, tkinter_constants.END)
            self.cust_file_path.insert(0, os.path.normpath(inpath))
            self.misc_prefs['lastDir'] = pathof(os.path.dirname(inpath))
            self.cust_file_path.config(state="readonly")

    def quitApp(self):
        global prefs
        if self.edu_quotes.get() == 'q':
            self.gui_prefs['educateQuotes'] = 1
        else:
            self.gui_prefs['educateQuotes'] = 0
        self.gui_prefs['dashes'] = self.dashBox.current()
        if self.edu_ellipses.get() == 'e':
            self.gui_prefs['educateEllipses'] = 1
        else:
            self.gui_prefs['educateEllipses'] = 0
        self.gui_prefs['useFile'] = self.use_file.get()
        if len(self.cust_file_path.get()):
            self.gui_prefs['useFilePath'] = pathof(self.cust_file_path.get())
        else:
            self.gui_prefs['useFilePath'] = ''
        self.gui_prefs['useUnicodeChars'] = self.unicodevar.get()
        self.misc_prefs['windowGeometry'] = self.parent.geometry()

        # copy preferences settings groups pack to global dict
        prefs['gui_selections'] = self.gui_prefs
        prefs['miscellaneous_settings'] = self.misc_prefs

        self.parent.destroy()
        self.quit()

def parseExceptionsFile(filename):
    safename = utf8_str(filename)
    words_list = []
    snippet = min(32, os.path.getsize(pathof(safename)))
    raw = open(pathof(safename), 'rb').read(snippet)
    if raw.startswith(codecs.BOM_UTF8):
        enc = 'utf-8-sig'
    else:
        encodings = ['utf-8', 'utf-16' 'windows-1252', 'windows-1250']
        for e in encodings:
            try:
                fh = file_open(pathof(safename), 'r', encoding=e)
                fh.readlines()
                fh.seek(0)
            except UnicodeDecodeError:
                print('Got unicode error with %s , trying different encoding' % e)
            else:
                break
        enc = e
    try:
        with file_open(pathof(safename), 'r', encoding=enc) as fd:
            words_list = [line.rstrip() for line in fd]
        #words_list = filter(None, words_list)
        words_list = [_f for _f in words_list if _f]
        print('Parsing apostrophe exception file %s' % filename)
    except:
        print('Error parsing apostrophe exception file %s: ignoring' % filename)
        words_list = []
    return words_list

def run(bk):
    global prefs
    # Get preferences from json prefs
    prefs = bk.getPrefs()

    # Or use defaults if json doesn't yet exist
    prefs.defaults['gui_selections'] = gui_selections
    prefs.defaults['miscellaneous_settings'] = miscellaneous_settings
    
    root = tkinter.Tk()
    root.title('')
    root.resizable(True, True)
    root.minsize(400, 425)
    guiMain(root, bk).pack(fill=tkinter_constants.BOTH, expand=True)
    root.mainloop()

    # Save prefs to back to json
    bk.savePrefs(prefs)

    NO_CHANGE = True
    if len(CRITERIA):
        apos_words_list = []
        if CRITERIA['apos_exception_file'] is not None and len(CRITERIA['files']):
            apos_words_list = parseExceptionsFile(CRITERIA['apos_exception_file'])
            
        for html_file in CRITERIA['files']:
            id = bk.href_to_id(html_file)
            html = bk.readfile(id)

            if not isinstance(html, text_type):
               html = text_type(html, 'utf-8')
    
            html_orig = html
    
            html = html.replace('<!--', START)
            html = html.replace('-->', STOP)
            # Slightly mangle all preexisting entities so HTMLParser
            # ignores them. We'll put them all back at the end.
            html = html.replace('&', AMPERSAND)
    
            html = smartyPants(html, CRITERIA['smarty_attr'], AMPERSAND, apos_words_list)
            html = html.replace(START, '<!--')
            html = html.replace(STOP, '-->')
    
            if CRITERIA['use_unicode']:
               # Convert the entities we created to unicode characters
               html = unescape(html)
            # Unmangle the pre-existing entities
            html = html.replace(AMPERSAND, '&')
            if not html == html_orig:
                NO_CHANGE = False
                bk.writefile(id, html)
                print('Changes made to %s' % html_file)
            else:
                print ('No changes made to %s.' % html_file)
        if NO_CHANGE:
            print('No files were altered')
    
    return 0

def main():
    print ('I reached main when I should not have\n')
    return -1

if __name__ == "__main__":
    sys.exit(main())
