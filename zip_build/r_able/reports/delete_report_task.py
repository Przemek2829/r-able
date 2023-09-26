import requests

from qgis.PyQt.QtCore import QThread, pyqtSignal


class DeleteReportTask(QThread):
    progress_changed = pyqtSignal(object)

    def __init__(self):
        super(DeleteReportTask, self).__init__()

    def run(self):
        self.error = ''
        self.terminated = False
        if self.config:
            items_len = len(self.report_items)
            for i, report_item in enumerate(self.report_items, 1):
                progress = int((i / items_len) * 100)
                self.progress_changed.emit(progress)
                url = '%s/report/%s' % (self.config.uri(), report_item.data(0, 100).get('id'))
                headers = {
                    'Authorization': 'Bearer %s' % self.token
                }
                try:
                    response = requests.delete(url, headers=headers)
                    if response.status_code != 204:
                        self.error += '%s\n' % response.text
                except Exception as e:
                    self.error += '%s\n' % e
