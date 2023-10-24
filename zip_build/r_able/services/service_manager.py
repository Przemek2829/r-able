import os
import re
import requests
from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService
from urllib.parse import quote

from qgis.core import Qgis, QgsProject, QgsRasterLayer, QgsMessageLog, QgsVectorLayer
from qgis.PyQt.QtWidgets import QApplication, QMessageBox, QListWidgetItem
from qgis.PyQt.QtCore import QTimer
from ..messenger import Messenger as msg
from ..gui.gui_translator import GuiTranslator as gt


class ServiceManager:
    def __init__(self, app):
        self.app = app
        self.window = app.window
        self.project = QgsProject.instance()
        self.window.services_wms_check.stateChanged.connect(self.changeServicesList)
        self.window.services_wfs_check.stateChanged.connect(self.changeServicesList)
        self.window.services_load_btn.clicked.connect(self.addServiceLayer)
        self.window.services_copy_url_btn.clicked.connect(self.copySelectedUrl)
        self.window.services_list.currentItemChanged.connect(self.adjustTimeRangeToService)
        self.available_services = []
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.restoreCopyBtn)

    def getServices(self):
        config = self.app.auth_manager.currentConfig()
        if self.app.token:
            url = '%s/system-info/components' % config.uri()
            headers = {
                'Authorization': 'Bearer %s' % self.app.token
            }
            try:
                response = requests.request("GET", url, headers=headers)
                if response.status_code == 200:
                    self.available_services = response.json()
                    self.available_services.append({'name': 'WFS', 'url': 'https://ws86-geoserver.tl.teralab-datascience.fr/geoserver/R-ABLE/wfs', 'description': ' Super serwer wfs'})
                else:
                    msg.createMessage(gt.tr('R-ABLE - services error'), QMessageBox.Warning,
                                      '%s<p><i>%s</i></p>' % (
                                      gt.tr('<p>An attempt to get R-ABLE services failed</p>'), response.text),
                                      False)
            except Exception as e:
                msg.createMessage(gt.tr('R-ABLE - connection error'), QMessageBox.Warning,
                                  '%s<p><i>%s</i></p>' % (
                                  gt.tr('<p>An attempt to connect to the R-ABLE service failed</p>'), e),
                                  False)

    def changeServicesList(self, checked):
        self.window.services_list.clear()
        for service in self.available_services:
            service_name = service.get('name', '').lower()
            service_item = QListWidgetItem(service.get('url'))
            if self.window.services_wms_check.isChecked() and 'wms' in service_name:
                service_item.setData(100, 'wms')
                self.window.services_list.addItem(service_item)
            if self.window.services_wfs_check.isChecked() and 'wfs' in service_name:
                service_item.setData(100, 'wfs')
                self.window.services_list.addItem(service_item)

    def adjustTimeRangeToService(self, cur_item, prev_item):
        if cur_item:
            url = cur_item.text()
            try:
                wms = WebMapService(url, version='1.3.0')
                years = []
                for name, metadata in wms.contents.items():
                    year = re.sub('(.*)(\\d{4})(.*)', r'\2', name)
                    try:
                        years.append(int(year))
                    except:
                        pass
                years.sort()
                if len(years) == 0:
                    self.window.services_year_box.setRange(2000, 10000)
                else:
                    self.window.services_year_box.setRange(min(years), max(years))
            except:
                self.window.services_year_box.setRange(2000, 10000)

    def addServiceLayer(self):
        service_items = self.window.services_list.selectedItems()
        if len(service_items) > 0:
            for service_item in service_items:
                year = str(self.window.services_year_box.value())
                service_url = service_item.text()
                service_type = service_item.data(100)
                if service_type == 'wms':
                    try:
                        wms = WebMapService(service_url, version='1.3.0')
                        layers = ''
                        styles = ''
                        loaded = False
                        for name, metadata in wms.contents.items():
                            if year in name:
                                layers += '&layers=%s' % quote(name)
                                styles += '&styles'
                                urlWithParams = 'url={}&crs={}&format=image/png{}{}'.format(service_url, self.project.crs().authid(), layers, styles)
                                wms_layer = QgsRasterLayer(urlWithParams, metadata.title, 'wms')
                                self.project.addMapLayer(wms_layer)
                                QgsMessageLog.logMessage('%s %s %s' % (gt.tr('Service'), service_url, gt.tr('loaded to map window')), 'R-ABLE', Qgis.Success)
                                loaded = True
                        if not loaded:
                            msg.createMessage('R-ABLE', QMessageBox.Information,
                                              gt.tr(f'<p>Service {service_url} for given year is unavailable</p>'),
                                              False)
                    except Exception as e:
                        msg.createMessage('R-ABLE', QMessageBox.Critical,
                                          '%s<i>%s</i>' % (gt.tr('<p>Failed to load selected service. Reason:</p>'), e),
                                          False)
                elif service_type == 'wfs':
                    try:
                        wfs = WebFeatureService(service_url)
                        layers = ''
                        styles = ''
                        loaded = False
                        for name, metadata in wfs.contents.items():
                            if year in name:
                                wfs_source = f"pagingEnabled='true' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='{self.project.crs().authid()}' typename='{name}' url='{service_url}' version='auto'"
                                wfs_layer = QgsVectorLayer(wfs_source, metadata.title, 'wfs')
                                wfs_layer.loadNamedStyle(os.path.join(os.path.dirname(__file__), 'style.qml'))
                                self.project.addMapLayer(wfs_layer)
                                QgsMessageLog.logMessage('%s %s %s' % (gt.tr('Service'), service_url, gt.tr('loaded to map window')), 'R-ABLE', Qgis.Success)
                                loaded = True
                        if not loaded:
                            msg.createMessage('R-ABLE', QMessageBox.Information,
                                              gt.tr(f'<p>Service {service_url} for given year is unavailable</p>'),
                                              False)
                    except Exception as e:
                        msg.createMessage('R-ABLE', QMessageBox.Critical,
                                          '%s<i>%s</i>' % (gt.tr('<p>Failed to load selected service. Reason:</p>'), e),
                                          False)
        else:
            msg.createMessage('R-ABLE', QMessageBox.Information,
                              gt.tr('No service selected to load'), False)

    def copySelectedUrl(self):
        service_item = self.window.services_list.currentItem()
        if service_item:
            cb = QApplication.clipboard()
            cb.clear(mode=cb.Clipboard)
            cb.setText(service_item.text(), mode=cb.Clipboard)
            self.window.services_copy_url_btn.setText(gt.tr('Copied!'))
            self.timer.start()
        else:
            msg.createMessage('R-ABLE', QMessageBox.Information, gt.tr('No service selected to copy'), False)

    def restoreCopyBtn(self):
        self.window.services_copy_url_btn.setText(gt.tr('Copy selected URL'))
