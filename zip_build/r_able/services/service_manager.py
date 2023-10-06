from owslib.wms import WebMapService
from urllib.parse import quote

from qgis.core import Qgis, QgsProject, QgsRasterLayer
from qgis.PyQt.QtWidgets import QApplication, QMessageBox
from qgis.PyQt.QtCore import QTimer
from ..messenger import Messenger as msg


class ServiceManager:
    def __init__(self, app):
        self.window = app.window
        self.project = QgsProject.instance()
        self.window.services_load_btn.clicked.connect(self.addWMSLayer)
        self.window.services_copy_url_btn.clicked.connect(self.copySelectedUrl)
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.restoreCopyBtn)

    def addWMSLayer(self):
        wms_item = self.window.services_list.currentItem()
        if wms_item:
            wms_url = wms_item.text()
            try:
                wms = WebMapService(wms_url, version='1.3.0')
                if wms:
                    layers = ''
                    styles = ''
                    for name, metadata in wms.contents.items():
                        layers += '&layers=%s' % quote(name)
                        styles += '&styles'
                    urlWithParams = 'url={}&crs=EPSG:2180&format=image/png{}{}'.format(wms_url, layers, styles)
                    wms_layer = QgsRasterLayer(urlWithParams, wms.identification.title, 'wms')
                    self.project.addMapLayer(wms_layer)
                else:
                    msg.createMessage('R-ABLE', QMessageBox.Critical,
                                      '<p>Failed to load selected service. Reason:</p>'
                                      '<i>Service not found</i>', False)
            except Exception as e:
                print(e)
                msg.createMessage('R-ABLE', QMessageBox.Critical,
                                  '<p>Failed to load selected service. Reason:</p>'
                                  '<i>%s</i>' % e,
                                  False)
        else:
            msg.createMessage('R-ABLE', QMessageBox.Information,
                              'No service selected to load', False)

    def copySelectedUrl(self):
        wms_item = self.window.services_list.currentItem()
        if wms_item:
            cb = QApplication.clipboard()
            cb.clear(mode=cb.Clipboard)
            cb.setText(wms_item.text(), mode=cb.Clipboard)
            self.window.services_copy_url_btn.setText('Copied!')
            self.timer.start()
        else:
            msg.createMessage('R-ABLE', QMessageBox.Information, 'No service selected to copy', False)

    def restoreCopyBtn(self):
        self.window.services_copy_url_btn.setText('Copy selected URL')
