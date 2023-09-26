import os
import sys
import re
import validators

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDialog, QMessageBox

from .gui_translator import GuiTranslator as gt
from r_able.messenger import Messenger as msg


class AuthDialog(QDialog):
    def __init__(self, config=None):
        super(AuthDialog, self).__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), "auth_dialog.ui"), self)
        self.fillConfig(config)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.button_box.accepted.connect(self.finish)
        self.button_box.rejected.connect(self.reject)
        self.name_input.setFocus(True)

    def finish(self):
        self.uri_input.setText(self.uri_input.text().replace('\\', '/'))
        if self.uri_input.text() != '':
            while self.uri_input.text()[-1] == '/':
                self.uri_input.setText(self.uri_input.text()[:-1])
        if self.validate():
            self.accept()
        else:
            msg.createMessage('R-ABLE', QMessageBox.Warning, 'Form is invalid, all fields should be filled and URI should be valid.', False)

    def validate(self):
        return self.name_input.text() != '' and \
               validators.url(self.uri_input.text()) and \
               self.user_input.text() != '' and \
               self.password_input.text() != ''

    def fillConfig(self, config):
        if config:
            config_map = config.configMap()
            self.name_input.setText(config.name())
            self.uri_input.setText(config.uri())
            self.user_input.setText(config_map.get('username'))
            self.password_input.setText(config_map.get('password'))
