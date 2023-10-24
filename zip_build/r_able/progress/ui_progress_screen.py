import os.path
from pathlib import Path

from PyQt5.QtCore import (QCoreApplication, QMetaObject, QObject, QPoint, QRect, QSize, QUrl, Qt)
from PyQt5.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QIcon, QLinearGradient,
                         QPalette, QPainter, QPixmap, QRadialGradient)
from PyQt5.QtWidgets import *

from ..gui.gui_translator import GuiTranslator as gt


class UiProgressScreen(object):
    def setupUi(self, ProgressScreen):
        if ProgressScreen.objectName():
            ProgressScreen.setObjectName(u"ProgressScreen")
        ProgressScreen.resize(340, 340)
        ProgressScreen.setWindowTitle("R-ABLE")
        ProgressScreen.setWindowIcon(QIcon(os.path.join(Path(__file__).parents[1], "resources/icon.png")))
        self.centralwidget = QWidget(ProgressScreen)
        self.centralwidget.setObjectName(u"centralwidget")

        self.circularProgressBarBase = QFrame(self.centralwidget)
        self.circularProgressBarBase.setObjectName(u"circularProgressBarBase")
        self.circularProgressBarBase.setGeometry(QRect(10, 10, 320, 320))
        self.circularProgressBarBase.setFrameShape(QFrame.NoFrame)
        self.circularProgressBarBase.setFrameShadow(QFrame.Raised)
        self.circularProgress = QFrame(self.circularProgressBarBase)
        self.circularProgress.setObjectName(u"circularProgress")
        self.circularProgress.setGeometry(QRect(10, 10, 300, 300))
        self.circularProgress.setStyleSheet(u"QFrame{\n"
                                            "	border-radius: 150px;\n"
                                            "	background-color: qconicalgradient(cx:0.5, cy:0.5, angle:90, stop:0.749 rgba(255, 0, 127, 0), stop:0.750 rgba(85, 170, 255, 255));\n"
                                            "}")
        self.circularProgress.setFrameShape(QFrame.NoFrame)
        self.circularProgress.setFrameShadow(QFrame.Raised)
        self.circularBg = QFrame(self.circularProgressBarBase)
        self.circularBg.setObjectName(u"circularBg")
        self.circularBg.setGeometry(QRect(10, 10, 300, 300))
        self.circularBg.setStyleSheet(u"QFrame{\n"
                                      "	border-radius: 150px;\n"
                                      "	background-color: rgba(169, 92, 63, 120);\n"
                                      "}")
        self.circularBg.setFrameShape(QFrame.NoFrame)
        self.circularBg.setFrameShadow(QFrame.Raised)
        self.container = QFrame(self.circularProgressBarBase)
        self.container.setObjectName(u"container")
        self.container.setGeometry(QRect(25, 25, 270, 270))
        self.container.setStyleSheet(u"QFrame{\n"
                                     "	border-radius: 135px;\n"
                                     "	background-color: rgb(255, 255, 255);\n"
                                     "}")
        self.container.setFrameShape(QFrame.NoFrame)
        self.container.setFrameShadow(QFrame.Raised)
        self.widget = QWidget(self.container)
        self.widget.setObjectName(u"widget")
        self.widget.setGeometry(QRect(40, 50, 193, 191))
        self.gridLayout = QGridLayout(self.widget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)

        self.labelPercentage = QLabel(self.widget)
        self.labelPercentage.setObjectName(u"labelPercentage")
        font1 = QFont()
        font1.setFamily(u"Roboto Thin")
        font1.setPointSize(32)
        self.labelPercentage.setFont(font1)
        self.labelPercentage.setStyleSheet(u"background-color: none;\n"
                                           "color: rgb(169, 92, 63)")
        self.labelPercentage.setAlignment(Qt.AlignCenter)
        self.gridLayout.addWidget(self.labelPercentage, 0, 0, 1, 1)

        self.labelTitle = QLabel(self.widget)
        self.labelTitle.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.labelTitle.setObjectName(u"labelTitle")
        pixmap = QPixmap(os.path.join(Path(__file__).parents[1], "resources/r_able_splash_no_frame.png"))
        self.labelTitle.setPixmap(pixmap.scaledToWidth(170, Qt.SmoothTransformation))
        self.gridLayout.addWidget(self.labelTitle, 1, 0, 1, 1)

        self.loading_info_container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(5)
        self.labelLoadingInfo = QLabel(self.widget)
        self.labelLoadingInfo.setObjectName(u"labelLoadingInfo")
        self.labelLoadingInfo.setMinimumSize(QSize(0, 20))
        self.labelLoadingInfo.setMaximumSize(QSize(16777215, 20))
        font2 = QFont()
        font2.setFamily(u"Segoe UI")
        font2.setPointSize(8)
        self.labelLoadingInfo.setFont(font2)
        self.labelLoadingInfo.setStyleSheet(u"QLabel{\n"
                                            "	border-radius: 10px;	\n"
                                            "	background-color: rgb(169, 92, 63);\n"
                                            "	color: #FFFFFF;\n"
                                            "}")
        self.labelLoadingInfo.setFrameShape(QFrame.NoFrame)
        self.labelLoadingInfo.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.labelLoadingInfo)

        self.kill_task_btn = QPushButton()
        self.kill_task_btn.setMinimumSize(QSize(20, 20))
        self.kill_task_btn.setMaximumSize(QSize(20, 20))
        self.kill_task_btn.setFlat(True)
        self.kill_task_btn.setStyleSheet('QPushButton{border-radius: 20px;image: url(:/plugins/r_able/x.png);}'
                                         'QPushButton:hover{image: url(:/plugins/r_able/x_hover.png);}'
                                         'QPushButton:pressed{image: url(:/plugins/r_able/x_pressed.png);}')
        layout.addWidget(self.kill_task_btn)
        self.loading_info_container.setLayout(layout)
        self.gridLayout.addWidget(self.loading_info_container, 2, 0, 1, 1)

        self.circularBg.raise_()
        self.circularProgress.raise_()
        self.container.raise_()
        self.retranslateUi(ProgressScreen)

        self.minimize_btn = QPushButton('', self.centralwidget)
        self.minimize_btn.setMinimumSize(18, 18)
        self.minimize_btn.setMaximumSize(18, 18)
        self.minimize_btn.move(310, 20)
        self.minimize_btn.setFlat(True)
        self.minimize_btn.setStyleSheet('QPushButton{border-radius: 20px;image: url(:/plugins/r_able/minimize.png);}'
                                        'QPushButton:hover{image: url(:/plugins/r_able/minimize_hover.png);}'
                                        'QPushButton:pressed{image: url(:/plugins/r_able/minimize_pressed.png);}')

        QMetaObject.connectSlotsByName(ProgressScreen)

    def retranslateUi(self, ProgressScreen):
        self.labelLoadingInfo.setText(gt.tr("connecting..."))
