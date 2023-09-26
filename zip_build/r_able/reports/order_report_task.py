import requests

from qgis.PyQt.QtCore import QThread


class OrderReportTask(QThread):
    def __init__(self):
        super(OrderReportTask, self).__init__()

    def run(self):
        self.error = None
        if self.config:
            url = '%s/report/' % self.config.uri()
            headers = {
                'Authorization': 'Bearer %s' % self.token,
                'Content-Type': 'application/json'
            }
            try:
                response = requests.post(url, json=self.payload, headers=headers)
                if response.status_code != 201:
                    self.error = response.text
            except Exception as e:
                self.error = e
