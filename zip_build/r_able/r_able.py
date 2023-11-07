import os.path

from qgis.PyQt.QtCore import Qt, QTimer, QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon, QPixmap
from qgis.PyQt.QtWidgets import QAction, QSplashScreen, QApplication

from .resources.resources import *
from .auth.auth_manager import AuthManager
from .gui.r_able_dialog import RAbleDialog
from .datasets.data_manager import DataManager
from .reports.reports_manager import ReportsManager
from .services.service_manager import ServiceManager
from .units.units_manager import UnitsManager


class RAble:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        try:
            locale = QSettings().value('locale/userLocale')[0:2]
        except:
            locale = 'en'
        print(locale)
        # locale = 'en'
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'RAble_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&R-ABLE plugin')

        self.first_start = None

    def tr(self, message):
        return QCoreApplication.translate('RAble', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        icon_path = ':/plugins/r_able/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'R-ABLE plugin'),
            callback=self.run,
            parent=self.iface.mainWindow())
        self.first_start = True

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&R-ABLE plugin'),
                action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        if self.first_start:
            self.window = RAbleDialog(self)
            splash = self.createSplash()
            QTimer.singleShot(1000, lambda: self.load(splash))
        else:
            self.window.show()

    def createSplash(self):
        self.window.setWindowOpacity(0)
        self.window.show()
        self.window.hide()
        self.window.setWindowOpacity(1)
        splash_pix = QPixmap(os.path.join(os.path.dirname(__file__), 'resources', 'r_able_splash.png'))
        splash = QSplashScreen(self.window.screen(), splash_pix, Qt.WindowStaysOnTopHint)
        splash.show()
        return splash

    def load(self, splash):
        self.units_manager = UnitsManager(self)
        self.auth_manager = AuthManager(self)
        self.data_manager = DataManager(self, self.iface)
        self.reports_manager = ReportsManager(self)
        self.service_manager = ServiceManager(self)
        splash.close()
        self.first_start = False
