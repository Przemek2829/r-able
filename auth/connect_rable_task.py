import requests

from qgis.PyQt.QtCore import QThread


class ConnectRableTask(QThread):
    def __init__(self, parent):
        self.parent = parent
        super(ConnectRableTask, self).__init__()

    def run(self):
        config = self.parent.currentConfig()
        self.error = None
        self.parent.app.token = None
        if config:
            config_map = config.configMap()
            auth_url = '%s/auth/token' % config.uri()
            user = config_map.get('username')
            password = config_map.get('password')
            payload = {"username": user, "password": password}
            try:
                response = requests.request("POST", auth_url, data=payload)
                if response.status_code == 200:
                    self.parent.app.token = response.json().get("access_token")
                else:
                    self.error = response.text
            except Exception as e:
                self.error = e
