#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import os

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QMessageBox
from PySide6.QtWidgets import QLineEdit, QSizePolicy, QComboBox, QSpacerItem, QDialogButtonBox
from PySide6.QtWidgets import QFileDialog, QListWidget, QListWidgetItem, QAbstractItemView
from PySide6.QtCore import Qt, QSize, QByteArray

from utilities import UpdateChecker, setupPrefs, PLUGIN_NAME

from plugin_utils_light import PluginApplication
from plugin_utils_light import _t

DEBUG = 1

class SquareButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)

    def resizeEvent(self, event):
        size = min(self.width(), self.height())
        self.setFixedSize(QSize(size, size))
        super().resizeEvent(event)


class guiMain(QDialog):
    def __init__(self):
        super().__init__()

        app = PluginApplication.instance()
        self.setWindowTitle(_t('guiMain', 'PunctuationSmarten'))
        self.bk = app.bk
        self.CRITERIA = {}
        self.prefs = setupPrefs(app.bk.getPrefs())
        self.gui_prefs = self.prefs['gui_selections']
        self.misc_prefs = self.prefs['miscellaneous_settings']
        self.update_prefs = self.prefs['update_settings']
        self._ok_to_close = False
        self.update, self.newversion = self.check_for_update()
        self.setup_ui()

    def store_custom_app_data(self):
        # Access the custom app object through the `instance()` method
        app = PluginApplication.instance()
        app.app_results = self.CRITERIA

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.chkQuotes = QCheckBox(_t('guiMain', 'Educate Quotes'), self)
        self.chkQuotes.setToolTip('<p>{}'.format(_t('guiMain', 'Check to smarten quotation marks')))
        self.chkQuotes.setChecked(self.gui_prefs['educateQuotes'])
        layout.addWidget(self.chkQuotes)

        self.chkAposFile = QCheckBox(_t('guiMain', 'Use apostrophe exception file'), self)
        self.chkAposFile.setChecked(self.gui_prefs['useFile'])
        layout.addWidget(self.chkAposFile)
        self.chkAposFile.stateChanged.connect(self.update_gui)

        txtaposfile_layout = QHBoxLayout()
        layout.addLayout(txtaposfile_layout)
        self.aposfile_txt = QLineEdit('', self)
        self.aposfile_txt.setMinimumWidth(300)
        txtaposfile_layout.addWidget(self.aposfile_txt)
        if len(self.gui_prefs['useFilePath']):
            self.aposfile_txt.setText(self.gui_prefs['useFilePath'])
        self.aposfile_txt.setDisabled(not self.chkAposFile.isChecked())
        self.aposfile_txt.setReadOnly(True)

        self.select_file_button = SquareButton('...')
        self.select_file_button.setToolTip('<p>{}'.format(_t('guiMain', 'Select apostrophe exception file')))
        self.select_file_button.clicked.connect(self.fileChooser)
        txtaposfile_layout.addWidget(self.select_file_button)
        self.select_file_button.setDisabled(not self.chkAposFile.isChecked())
        hspacer =  QSpacerItem(40, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)
        txtaposfile_layout.addItem(hspacer)

        combo_layout = QHBoxLayout()
        layout.addLayout(combo_layout)
        self.cbodashes = QComboBox()
        self.cbodashes.addItems(['No dash support', "'--' = emdash (no endash support)", "'--' = emdash '---' = endash", "'---' = emdash '--' = endash"])
        self.cbodashes.setCurrentIndex(self.gui_prefs['dashes'])
        self.cbodashes.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        combo_layout.addWidget(self.cbodashes)
        hspacer =  QSpacerItem(40, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)
        combo_layout.addItem(hspacer)

        self.chkEllipse = QCheckBox(_t('guiMain', 'Educate Ellipses'), self)
        self.chkEllipse.setToolTip('<p>{}'.format(_t('guiMain', 'Check to smarten three periods to an elipse character')))
        self.chkEllipse.setChecked(self.gui_prefs['educateEllipses'])
        layout.addWidget(self.chkEllipse)

        self.chkUniChar = QCheckBox(_t('guiMain', 'Use Unicode Characters'), self)
        self.chkUniChar.setToolTip('<p>{}'.format(_t('guiMain', 'Check to smarten to characters rather than entities')))
        self.chkUniChar.setChecked(self.gui_prefs['useUnicodeChars'])
        layout.addWidget(self.chkUniChar)

        self.file_list = QListWidget(self)
        # self.file_list.setFixedWidth(200)
        self.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.file_list.setTextElideMode(Qt.ElideLeft)

        for (id, href) in self.bk.text_iter():
            item = QListWidgetItem(href)
            self.file_list.addItem(item)
            # bk.selected_iter() is not available on older versions of Sigil
            # The files selected in the Book Browser will not be pre-selected if so.
            selected_op = getattr(self.bk, "selected_iter", None)
            if callable(selected_op):
                if href in [self.bk.id_to_href(ident) for typ, ident in selected_op()]:
                    self.file_list.setCurrentItem(item)
        layout.addWidget(self.file_list)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        if 'windowGeometry' in self.misc_prefs and self.misc_prefs['windowGeometry'] is not None:
            try:
                self.restoreGeometry(QByteArray.fromHex(self.misc_prefs['windowGeometry'].encode('ascii')))
            except Exception:
                pass
        self.show()
        if self.update:
            self.update_msgbox()

    def fileChooser(self):
        options =  QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        title = "Select apostrophe exception file"
        startfolder = None
        if self.misc_prefs['lastDir'] is not None:
            startfolder = self.misc_prefs['lastDir']
        inpath, _ = QFileDialog.getOpenFileName(self, title, startfolder, options=options)
        if len(inpath):
            if DEBUG:
                print(inpath)
            self.aposfile_txt.setEnabled(True)
            self.aposfile_txt.setText(os.path.normpath(inpath))
            self.misc_prefs['lastDir'] = os.path.dirname(inpath)
        else:
            if self.aposfile_txt.text() =='':
                self.chkAposFile.setChecked(False)
                self.aposfile_txt.setEnabled(False)

    def update_msgbox(self):
        msgBox = QMessageBox()
        title = 'Plugin Update Available'
        msgBox.setWindowTitle(title)
        text = f'Version {self.newversion} of the {PLUGIN_NAME} plugin is now available.'
        msgBox.setText(text)
        msgBox.exec()

    def prep_criteria(self):
        if self.cbodashes.currentIndex() == 0:
            dash_settings = ''
        elif self.cbodashes.currentIndex() == 1:
            dash_settings = 'd'
        elif self.cbodashes.currentIndex() == 2:
            dash_settings = 'i'
        else:
            dash_settings = 'D'

        if self.chkAposFile.isChecked():
            if len(self.aposfile_txt.text()):
                apos_exception_file = self.aposfile_txt.text()
                if not os.path.exists(apos_exception_file):
                    print(f'Apostrophe exception file {apos_exception_file} does not exist!')
                    apos_exception_file = None
            else:
                apos_exception_file = None
        else:
            apos_exception_file = None
        self.CRITERIA['apos_exception_file'] = apos_exception_file

        quotes = 'q' if self.chkQuotes.isChecked() else ''
        ellipses = 'e' if self.chkEllipse.isChecked() else ''

        smarty_attr = quotes + dash_settings + ellipses
        if smarty_attr == '':
            smarty_attr = '0'
        self.CRITERIA['smarty_attr'] = smarty_attr

        self.CRITERIA['use_unicode'] = 1 if self.chkUniChar.isChecked() else 0

        self.CRITERIA['files'] = [item.text() for item in self.file_list.selectedItems()]

        # Store the criteria in the custom app object for retrieval from main plugin script
        self.store_custom_app_data()

    def check_for_update(self):
        last_time_checked = self.update_prefs['last_time_checked']
        last_online_version = self.update_prefs['last_online_version']
        chk = UpdateChecker(last_time_checked, last_online_version, self.bk._w)
        update_available, online_version, time = chk.update_info()
        # update preferences with latest date/time/version
        self.update_prefs['last_time_checked'] = time
        if online_version is not None:
            self.update_prefs['last_online_version'] = online_version
        if update_available:
            return (True, online_version)
        return (False, online_version)

    def accept(self):
        self._ok_to_close = True
        self.close()

    def reject(self):
        self.close()

    def update_gui(self):
        self.aposfile_txt.setDisabled(not self.chkAposFile.isChecked())
        self.select_file_button.setDisabled(not self.chkAposFile.isChecked())

    def closeEvent(self, event):
        if self._ok_to_close:
            # Save current window geometry to plugin prefernces
            self.misc_prefs['windowGeometry'] = self.saveGeometry().toHex().data().decode('ascii')
            self.gui_prefs['educateQuotes'] = self.chkQuotes.isChecked()
            self.gui_prefs['useFile'] = self.chkAposFile.isChecked()
            self.gui_prefs['useFilePath'] = self.aposfile_txt.text()
            self.gui_prefs['dashes']= self.cbodashes.currentIndex()
            self.gui_prefs['educateEllipses'] = self.chkEllipse.isChecked()
            self.gui_prefs['useUnicodeChars'] = self.chkUniChar.isChecked()
            self.prep_criteria()
            self.bk.savePrefs(self.prefs)
            event.accept()  # let the window close
            if DEBUG:
                print('Close event accepted')
        else:
            if DEBUG:
                print('Close event rejected')
            self.reject()
