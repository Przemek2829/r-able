import os
import sys
import re

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDialog

from .gui_translator import GuiTranslator as gt
from r_able.messenger import Messenger as msg


class ReportMetaDialog(QDialog):
    def __init__(self, report=None):
        super(ReportMetaDialog, self).__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), "report_meta_dialog.ui"), self)
        self.fillMetadata(report)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

    def fillMetadata(self, report):
        if report:
            self.title.setPlainText(report.get('title'))
            self.subtitle.setPlainText(report.get('subtitle'))
            self.description.setPlainText(report.get('meta', {}).get('description'))
            self.time_from.setText(str(report.get('year_from')))
            self.time_to.setText(str(report.get('year_to')))
            unit_dict = report.get('administrative_unit', {})
            self.unit.setText('%s %s %s (%s)' % (unit_dict.get('country'),
                                                 unit_dict.get('type'),
                                                 unit_dict.get('name'),
                                                 unit_dict.get('code')))
            self.created.setText(report.get('created'))
            self.created_by.setText(report.get('meta', {}).get('author'))
