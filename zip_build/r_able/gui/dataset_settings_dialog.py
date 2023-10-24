import os
import sys

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QSettings
from qgis.PyQt.QtWidgets import QDialog, QMessageBox
from qgis.core import QgsCoordinateReferenceSystem

CRS_KEY = 'dataset_crs'


class DatasetSettingsDialog(QDialog):
    def __init__(self):
        super(DatasetSettingsDialog, self).__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), "dataset_settings_dialog.ui"), self)
        self.loadSettings()
        self.setModal(True)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.button_box.accepted.connect(self.finish)
        self.button_box.rejected.connect(self.reject)

    def finish(self):
        QSettings().setValue(CRS_KEY, self.crs_widget.crs())
        self.accept()

    def loadSettings(self):
        crs = QSettings().value(CRS_KEY)
        if crs and isinstance(crs, QgsCoordinateReferenceSystem) and crs.isValid():
            self.crs_widget.setCrs(crs)
        else:
            self.crs_widget.setCrs(QgsCoordinateReferenceSystem.fromEpsgId(2180))
