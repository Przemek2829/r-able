import re
from datetime import datetime

from qgis.core import QgsMessageLog, Qgis
from qgis.PyQt.QtCore import QDateTime, QSize, QTimer
from qgis.PyQt.QtWidgets import QTreeWidgetItem, QWidget, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy

from .monitor_reports_task import MonitorReportsTask
from ..gui.gui_handler import GuiHandler as gh


class ReportsMonitor:
    def __init__(self, manager):
        self.manager = manager
        self.app = manager.app
        self.window = manager.window
        self.monitor_task = MonitorReportsTask()
        self.configureBackgroundMonitoring()
        self.monitor_task.finished.connect(self.monitorTaskFinished)
        self.natural_order = 'a'

    def configureBackgroundMonitoring(self):
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(lambda: self.monitorReports(False))
        self.monitor_timer.setInterval(5000)

    def monitorReports(self, progress_screen=None):
        if progress_screen:
            progress_screen.ui.labelLoadingInfo.setText('updating reports...')
        self.monitor_task.page = int(re.sub('^(Page )(\\d+)$', r'\2', self.window.reports_page_label.text()))
        self.monitor_task.app = self.app
        self.monitor_task.start()

    def monitorTaskFinished(self):
        self.window.progress_screen.hideProgress()
        monitoring_completed = True
        if self.monitor_task.response:
            downloaded_reports = self.monitor_task.response.get('content', [])
            self.removeNotDownloadedReports(downloaded_reports)
            for report in downloaded_reports:
                monitoring_completed = report.get('status') == 'SUCCESS'
                self.updateReportItem(report)
            self.manager.filterReportsTree(self.window.reports_filter_input.text())
        elif self.monitor_task.error:
            QgsMessageLog.logMessage(str(self.monitor_task.error), 'R-ABLE', Qgis.Info)
        if monitoring_completed:
            self.monitor_timer.stop()
        else:
            if not self.monitor_timer.isActive():
                self.monitor_timer.start()

    def removeNotDownloadedReports(self, downloaded_reports):
        downloaded_reports_ids = list(map(lambda r: r.get('id'), downloaded_reports))
        tree_items = []
        root_item = self.window.reports_tree.invisibleRootItem()
        for i in range(0, root_item.childCount()):
            tree_items.append(root_item.child(i))
        for report_item in tree_items:
            if report_item.data(0, 100).get('id') not in downloaded_reports_ids:
                self.window.reports_tree.takeTopLevelItem(self.window.reports_tree.indexOfTopLevelItem(report_item))

    def updateReportItem(self, report):
        report_id = report.get('id')
        root_item = self.window.reports_tree.invisibleRootItem()
        title = report.get('title')
        created = QDateTime.fromString(re.sub('^(.*)\\.(.*)$', r'\1', report.get('created')), 'yyyy-MM-ddThh:mm:ss')
        uname = report.get('administrative_unit', {}).get('name')
        ucode = report.get('administrative_unit', {}).get('code')
        year_from = report.get('year_from')
        year_to = report.get('year_to')
        status = report.get('status')
        for i in range(0, root_item.childCount()):
            report_item = root_item.child(i)
            if report_item.data(0, 100).get('id') == report_id:
                report_widget = self.window.reports_tree.itemWidget(report_item, 0)
                report_widget.findChild(QLabel, 'name_label').setText('%s (%s %s)' % (title, uname, ucode))
                status_label = report_widget.findChild(QLabel, 'status_label')
                status_label.setText(status)
                gh.setLabelStyleSheet(status_label, status)
                return
        if report_id not in self.manager.deleted_ids:
            report_item = QTreeWidgetItem(self.window.reports_tree)
            report_widget = QWidget()
            report_widget.setObjectName('report_widget')
            widget_layout = QHBoxLayout()
            widget_layout.setContentsMargins(2, 2, 2, 2)
            name_label = gh.createLabel('%s (%s %s)' % (title, uname, ucode), 'name_label')
            timeframe_label = gh.createLabel('%s - %s' % (year_from, year_to), 'timeframe_label')
            status_label = gh.createLabel(status, 'status_label', True)
            widget_layout.addWidget(name_label)
            widget_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Ignored))
            widget_layout.addWidget(timeframe_label)
            widget_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Ignored))
            widget_layout.addWidget(status_label)
            widget_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Ignored))
            report_widget.setLayout(widget_layout)
            self.window.reports_tree.setItemWidget(report_item, 0, report_widget)
            report_item.setData(0, 100, report)
            report_item.setText(1, self.natural_order)
            report_item.setText(2, '%s (%s %s) %s - %s'.lower() % (title, uname, ucode, year_from, year_to))
            report_item.setData(3, 0, created)
            report_item.setText(4, status)
            self.natural_order += 'a'
