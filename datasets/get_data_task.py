import requests

from qgis.PyQt.QtCore import QThread, QSettings
from qgis.core import QgsCoordinateReferenceSystem


class GetDataTask(QThread):
    def __init__(self):
        super(GetDataTask, self).__init__()

    def run(self):
        self.error = None
        self.terminated = False

        if self.config:
            srid = 2180
            crs = QSettings().value('dataset_crs')
            if crs and isinstance(crs, QgsCoordinateReferenceSystem) and crs.isValid():
                srid = crs.authid().replace('EPSG:', '')
            url = '%s/data/?srid=%s' % (self.config.uri(), srid)
            headers = {
                'Authorization': 'Bearer %s' % self.token,
                'Content-Type': 'application/json'
            }
            try:
                self.response = requests.post(url, json=self.payload, headers=headers)
                if self.response.status_code != 200:
                    self.error = self.response.text
            except Exception as e:
                self.error = e
