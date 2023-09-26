import os

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsMessageLog, Qgis


class Messenger:

    @staticmethod
    def createMessage(title, icon, text, add_buttons=True):
        msg_box = QMessageBox()
        msg_box.setModal(True)
        msg_box.setWindowFlags(Qt.WindowStaysOnTopHint)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'resources/icon.png')))
        msg_box.setText(text)
        if add_buttons:
            msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.No)
        else:
            if icon == QMessageBox.Critical:
                message_level = Qgis.Critical
            elif icon == QMessageBox.Warning:
                message_level = Qgis.Warning
            else:
                message_level = Qgis.Info
            QgsMessageLog.logMessage(text, 'R-ABLE', level=message_level)
        returnValue = msg_box.exec()
        return returnValue
