import requests
import os
from pathlib import Path

from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtGui import QPixmap
from qgis.core import QgsApplication, QgsAuthMethodConfig, QgsMessageLog, Qgis

from r_able.gui.gui_translator import GuiTranslator as gt
from r_able.gui.auth_dialog import AuthDialog
from r_able.messenger import Messenger as msg
from .connect_rable_task import ConnectRableTask


class AuthManager:
    def __init__(self, app):
        self.app = app
        self.window = app.window
        self.progress_screen = self.window.progress_screen
        self.auth_manager = QgsApplication.authManager()
        self.fillConfigs()
        self.connect_task = ConnectRableTask(self)
        self.connectRableService()
        self.connectSignals()

    def connectSignals(self):
        self.window.auths_combo.currentIndexChanged.connect(self.setCurrentConfig)
        self.window.reconnect_service_btn.clicked.connect(lambda: self.connectRableService())
        self.window.edit_auth_btn.clicked.connect(self.editConfig)
        self.window.add_auth_btn.clicked.connect(self.addConfig)
        self.window.remove_auth_btn.clicked.connect(self.removeConfig)
        self.connect_task.finished.connect(self.connectTaskFinished)

    def fillConfigs(self):
        self.window.auths_combo.clear()
        configs = []
        current_config = None
        for config_id, config_data in self.auth_manager.availableAuthMethodConfigs().items():
            config_name = config_data.name()
            if config_id == QSettings().value('auth_id'):
                current_config = config_name
            configs.append(config_name)
        self.window.auths_combo.addItems(configs)
        if current_config:
            self.window.auths_combo.setCurrentText(current_config)

    def addConfig(self):
        auth_dialog = AuthDialog()
        result = auth_dialog.exec()
        if result == 1:
            config = QgsAuthMethodConfig()
            config.setName(auth_dialog.name_input.text())
            config.setMethod('Basic')
            config.setUri(auth_dialog.uri_input.text())
            config.setConfigMap({'username': auth_dialog.user_input.text(),
                                 'password': auth_dialog.password_input.text()})
            self.auth_manager.storeAuthenticationConfig(config)
            self.window.auths_combo.addItem(auth_dialog.name_input.text())

    def editConfig(self):
        config = self.configByName()
        if config:
            auth_dialog = AuthDialog(config)
            result = auth_dialog.exec()
            if result == 1:
                config.setUri(auth_dialog.uri_input.text())
                config.setConfigMap({'username': auth_dialog.user_input.text(),
                                     'password': auth_dialog.password_input.text()})
                config.setName(auth_dialog.name_input.text())
                self.auth_manager.updateAuthenticationConfig(config)
                self.window.auths_combo.setItemText(self.window.auths_combo.currentIndex(), auth_dialog.name_input.text())
                self.connectRableService()

    def removeConfig(self):
        resp = msg.createMessage(gt.tr('R-ABLE - delete connection'), QMessageBox.Question,
                                 gt.tr('Do you really want to delete current connection?'))
        if resp == QMessageBox.Ok:
            config = self.configByName()
            if config:
                self.auth_manager.removeAuthenticationConfig(config.id())
                self.window.auths_combo.removeItem(self.window.auths_combo.currentIndex())
                if self.window.auths_combo.count() == 0:
                    QSettings().setValue('auth_id', None)
                    self.connectRableService()

    def configByName(self):
        combo = self.window.auths_combo
        config_name = combo.currentText()
        for config_id, config_data in self.auth_manager.availableAuthMethodConfigs().items():
            if config_data.name() == config_name:
                config = QgsAuthMethodConfig()
                self.auth_manager.loadAuthenticationConfig(config_id, config, True)
                return config

    def connectRableService(self):
        config = self.currentConfig()
        if config:
            self.connect_task.config = config
            self.progress_screen.showProgress(gt.tr('connecting...'))
            self.connect_task.start()

    def connectTaskFinished(self):
        self.changeServiceStatus()
        self.subscriptionInfo()
        self.app.units_manager.getUnits()
        self.app.service_manager.getServices()
        self.window.reports_tree.clear()
        self.app.reports_manager.reports_monitor.monitorReports()
        if self.connect_task.error:
            self.progress_screen.hideProgress()
            msg.createMessage(gt.tr('R-ABLE - connection error'), QMessageBox.Warning,
                              '%s<p><i>%s</i></p>' % (gt.tr('<p>An attempt to connect to the R-ABLE service failed</p>'), self.connect_task.error),
                              False)
        else:
            QgsMessageLog.logMessage(gt.tr('Successfully connected to R-ABLE services'), 'R-ABLE', Qgis.Success)

    def changeServiceStatus(self):
        if self.app.token:
            self.window.service_diode_label.setPixmap(
                QPixmap(os.path.join(Path(__file__).parents[1], 'resources/green.png')))
            self.window.service_info_label.setText(gt.tr('Connected to R-ABLE services'))
        else:
            self.window.service_diode_label.setPixmap(
                QPixmap(os.path.join(Path(__file__).parents[1], 'resources/red.png')))
            self.window.service_info_label.setText(gt.tr('Not connected to R-ABLE services'))

    def currentConfig(self):
        auth_id = QSettings().value('auth_id')
        if auth_id:
            config = QgsAuthMethodConfig()
            self.auth_manager.loadAuthenticationConfig(auth_id, config, True)
            if len(config.configMap()) > 0:
                return config

    def setCurrentConfig(self):
        config = self.configByName()
        if config:
            QSettings().setValue('auth_id', config.id())
            self.connectRableService()

    def subscriptionInfo(self):
        config = self.currentConfig()
        subscription_info = {}
        if self.app.token:
            url = '%s/user/me' % config.uri()
            headers = {
                'Authorization': 'Bearer %s' % self.app.token
            }
            try:
                response = requests.request("GET", url, headers=headers)
                if response.status_code == 200:
                    subscription_info = response.json()
                else:
                    msg.createMessage(gt.tr('R-ABLE - subscription error'), QMessageBox.Warning,
                                      '%s<p><i>%s</i></p>' % (gt.tr('<p>An attempt to get subscription info failed</p>'), response.text),
                                      False)
            except Exception as e:
                msg.createMessage(gt.tr('R-ABLE - connection error'), QMessageBox.Warning,
                                  '%s<p><i>%s</i></p>' % (gt.tr('<p>An attempt to connect to the R-ABLE service failed</p>'), e),
                                  False)
        self.updateSubscriptionInfo(subscription_info)

    def updateSubscriptionInfo(self, info):
        self.window.settings_subscription_value_label.setText('')
        first_name = info.get('first_name')
        last_name = info.get('last_name')
        username = info.get('username')
        self.window.settings_account_name_value_label.setText(f'{first_name} {last_name} ({username})')
        status = info.get('active')
        status = 'active' if status else ''
        self.window.reconnect_service_btn.setVisible(not status)
        self.window.settings_account_status_value_label.setText(status)
