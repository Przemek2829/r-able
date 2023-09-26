import requests

from qgis.PyQt.QtCore import QThread, pyqtSignal


class DownloadReportTask(QThread):
    progress_changed = pyqtSignal(object)

    def __init__(self):
        super(DownloadReportTask, self).__init__()

    def run(self):
        self.error = None
        self.responses = []
        self.terminated = False
        if self.config:
            items_len = len(self.report_items)
            for i, report_item in enumerate(self.report_items, 1):
                progress = int((i / items_len) * 100)
                self.progress_changed.emit(progress)
                url = '%s/report/%s/pdf' % (self.config.uri(), report_item.data(0, 100).get('id'))
                headers = {
                    'Authorization': 'Bearer %s' % self.token
                }
                try:
                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        self.responses.append((response, report_item.data(0, 100).get('task_id')))
                    else:
                        self.error += '%s\n' % response.text
                except Exception as e:
                    self.error += '%s\n' % e
