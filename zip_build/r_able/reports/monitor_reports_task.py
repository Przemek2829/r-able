import requests

from qgis.PyQt.QtCore import QThread


class MonitorReportsTask(QThread):
    def __init__(self):
        super(MonitorReportsTask, self).__init__()

    def run(self):
        self.response = None
        self.error = None
        if self.app.token:
            config = self.app.auth_manager.currentConfig()
            if config:
                url = '%s/report/' % config.uri()
                params = {'page': self.page,
                          'page_size': 30,
                          'order_by': 'created',
                          'ascending': True}
                headers = {
                    'Authorization': 'Bearer %s' % self.app.token
                }
                try:
                    response = requests.get(url, params=params, headers=headers)
                    if response.status_code == 200:
                        self.response = response.json()
                    else:
                        self.error = response.text
                except Exception as e:
                    self.error = e
