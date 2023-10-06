import os
from pathlib import Path
import sys
import re
import requests

from qgis.core import QgsMessageLog, Qgis
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QSize, QCoreApplication
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import QMovie

from .gui_translator import GuiTranslator as gt
from .gui_handler import GuiHandler as gh
from ..progress.progress_screen import ProgressScreen
from r_able.messenger import Messenger as msg


class TimeIntervalButton(QPushButton):
    def __init__(self, parent):
        super(TimeIntervalButton, self).__init__()
        self.base_size = QSize(85, 30)
        self.setMinimumSize(self.base_size)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(5, 2, 5, 2)
        self.buttons_layout = QVBoxLayout()
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(2)
        self.plus_button = QPushButton()
        self.configureButton(self.plus_button,
                             'QPushButton{image: url(:/plugins/r_able/plus.png);}\n'
                             'QPushButton:pressed{image: url(:/plugins/r_able/plus_pressed.png);}',
                             lambda: self.changeTimeInterval(1))
        self.minus_button = QPushButton('')
        self.configureButton(self.minus_button,
                             'QPushButton{image: url(:/plugins/r_able/minus.png);}\n'
                             'QPushButton:pressed{image: url(:/plugins/r_able/minus_pressed.png);}',
                             lambda: self.changeTimeInterval(-1))
        self.buttons_layout.addWidget(self.plus_button)
        self.buttons_layout.addWidget(self.minus_button)
        self.label = QLabel(gt.tr('TimeIntervalButton', 'Last year'))
        self.label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.layout.addWidget(self.label)
        self.layout.addLayout(self.buttons_layout)
        self.setLayout(self.layout)
        self.wheelEvent = self.wheelEvent
        self.fitButtonSize()
        parent.layout().addWidget(self)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.plus_button.animateClick()
        else:
            self.minus_button.animateClick()

    def configureButton(self, button, stylesheet, function):
        button.setMinimumSize(QSize(13, 13))
        button.setMaximumSize(QSize(13, 13))
        button.setStyleSheet(stylesheet)
        button.setFlat(True)
        button.clicked.connect(function)

    def changeTimeInterval(self, increment):
        current_interval = re.sub('^[a-zA-Z]+ (\\d+) [a-zA-Z()?]+$', r'\1', self.label.text())
        current_interval = int(current_interval) if current_interval != gt.tr('TimeIntervalButton', 'Last year') else 1
        if current_interval == 1:
            if increment == 1:
                self.label.setText(gt.tr('TimeIntervalButton', 'Last 2 years'))
        else:
            current_interval += increment
            if current_interval == 1:
                self.label.setText(gt.tr('TimeIntervalButton', 'Last year'))
            else:
                self.label.setText('%s %s %s' % (gt.tr('TimeIntervalButton', 'Last'), current_interval, gt.tr('TimeIntervalButton', 'years')))
        self.fitButtonSize()

    def fitButtonSize(self):
        point_size = self.label.font().pointSize()
        size_increment = len(self.label.text())
        self.setMinimumSize(QSize(size_increment * point_size + 5, 30))

    def tr(self, message):
        return QCoreApplication.translate('TimeIntervalButton', message)


class RAbleDialog(QDialog):
    def __init__(self, app):
        """Constructor."""
        super(RAbleDialog, self).__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), "r_able_dialog_base.ui"), self)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.app = app
        self.reports_tree.setColumnHidden(1, True)
        self.reports_tree.setColumnHidden(2, True)
        self.reports_tree.setColumnHidden(3, True)
        self.reports_tree.setColumnHidden(4, True)
        self.progress_screen = ProgressScreen(self)
        self.reports_time_interval_btn = TimeIntervalButton(self.reports_timeframe_box)
        loading_gif = QMovie(os.path.join(Path(__file__).parents[1], 'resources', "loading.gif"))
        loading_gif.setScaledSize(QSize(20, 20))
        self.reports_progress_label.setMovie(loading_gif)
        self.data_progress_label.setMovie(loading_gif)
        loading_gif.start()
        self.reports_progress_label.hide()
        self.data_progress_label.hide()
