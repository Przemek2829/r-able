import time

from PyQt5.QtCore import Qt, QTimer, QEvent, QPoint, QCoreApplication
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import *

from .ui_progress_screen import UiProgressScreen
from ..gui.gui_translator import GuiTranslator as gt

counter = 0
jumper = 10


class ProgressScreen(QDialog):
    def __init__(self, window):
        super(ProgressScreen, self).__init__()
        self.ui = UiProgressScreen()
        self.ui.setupUi(self)
        self.window = window

        self.progressBarValue(0)
        self.progress_task = None
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 120))
        self.ui.circularBg.setGraphicsEffect(self.shadow)

        self.timer = QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.progress)

        self.ui.minimize_btn.clicked.connect(lambda: self.showMinimized())
        self.ui.kill_task_btn.clicked.connect(self.killProgressTask)

    def tr(self, message):
        return QCoreApplication.instance().translate('ProgressScreen', message)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.move_event = True
            self.cur_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.move_event:
            cur_pos = event.globalPos()
            delta = QPoint(cur_pos - self.cur_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.cur_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.move_event = False

    def progress(self):
        global counter
        global jumper
        value = counter
        if value >= 100:
            value = 1.000
        self.progressBarValue(value)

        counter += 0.5
        if counter == 100:
            counter = 0

    def progressBarValue(self, value):
        styleSheet = """
        QFrame{
            border-radius: 150px;
            background-color: qconicalgradient(cx:0.5, cy:0.5, angle:90, stop:{STOP_1} rgba(255, 0, 127, 0), stop:{STOP_2} rgba(169, 92, 63, 255));
        }
        """

        progress = (100 - value) / 100.0

        self.ui.labelPercentage.setText(f'{value}%')

        stop_1 = str(progress - 0.001)
        stop_2 = str(progress)

        newStylesheet = styleSheet.replace("{STOP_1}", stop_1).replace("{STOP_2}", stop_2)

        self.ui.circularProgress.setStyleSheet(newStylesheet)

    def showProgress(self, info_text, task=None, show_percentage=False, can_terminate=False):
        self.window.setVisible(False)
        self.progress_task = task
        self.ui.labelLoadingInfo.setText(info_text)
        self.ui.labelPercentage.setVisible(show_percentage)
        self.ui.kill_task_btn.setVisible(can_terminate)
        self.ui.minimize_btn.setVisible(show_percentage)
        if not show_percentage:
            self.timer.start()
            self.ui.labelTitle.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        else:
            self.ui.labelTitle.setAlignment(Qt.AlignCenter)
        self.show()

    def hideProgress(self, visible=True):
        self.window.setVisible(visible)
        self.timer.stop()
        global counter
        counter = 0
        self.close()

    def killProgressTask(self):
        if self.progress_task is not None:
            self.progress_task.terminated = True
            self.progress_task.error = self.tr('Terminated by user')
            self.progress_task.terminate()
