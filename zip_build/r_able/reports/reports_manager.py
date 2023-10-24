import os
from pathlib import Path
import re
import requests
import platform
import subprocess

from qgis.core import QgsMessageLog, Qgis
from qgis.PyQt.QtCore import QDateTime, QSize, Qt
from qgis.PyQt.QtWidgets import QLabel, QMessageBox, QPushButton, QFileDialog, QMenu
from qgis.PyQt.QtGui import QIcon

from .reports_monitor import ReportsMonitor
from .order_report_task import OrderReportTask
from .delete_report_task import DeleteReportTask
from .download_report_task import DownloadReportTask
from ..messenger import Messenger as msg
from ..gui.report_meta_dialog import ReportMetaDialog
from ..gui.gui_handler import GuiHandler as gh
from ..gui.gui_translator import GuiTranslator as gt


class ReportsManager:
    def __init__(self, app):
        self.app = app
        self.window = app.window
        self.reports_monitor = ReportsMonitor(self)
        self.order_task = OrderReportTask()
        self.delete_task = DeleteReportTask()
        self.download_task = DownloadReportTask()
        self.deleted_ids = []
        self.sort_buttons = [self.window.reports_sort_by_title_btn,
                             self.window.reports_sort_by_date_btn,
                             self.window.reports_sort_by_status_btn]
        self.sort_mode = 'no_sort'
        self.window.reports_tree.contextMenuEvent = self.contextMenuEvent
        self.connectSignals()

    def contextMenuEvent(self, event):
        menu = QMenu()
        delete_action = gt.tr('Delete selected items')
        download_action = gt.tr('Download selected items')
        menu.addAction(QIcon(os.path.join(Path(__file__).parents[1], 'resources/reject.png')), delete_action)
        menu.addAction(QIcon(os.path.join(Path(__file__).parents[1], 'resources/pdf.png')), download_action)
        action = menu.exec(event.globalPos())
        if action:
            if action.text() == delete_action:
                self.deleteReport(self.window.reports_tree.selectedItems())
            if action.text() == download_action:
                self.downloadReportPdf(self.window.reports_tree.selectedItems())

    def connectSignals(self):
        self.window.reports_time_interval_btn.clicked.connect(
            lambda: gh.setupDateRange(self.window.reports_time_interval_btn,
                                      self.window.reports_start_year,
                                      self.window.reports_end_year))
        self.window.reports_clear_units_btn.clicked.connect(
            lambda: self.app.units_manager.clearSelectedUnits(self.window.reports_selected_units, self.window.reports_unit_input))
        self.window.reports_order_report_btn.clicked.connect(self.orderReport)
        self.window.reports_tree.currentItemChanged.connect(self.reloadTreeButtons)
        self.window.reports_sort_by_title_btn.clicked.connect(
            lambda checked: self.changeSortAttribute(checked, self.window.reports_sort_by_title_btn))
        self.window.reports_sort_by_date_btn.clicked.connect(
            lambda checked: self.changeSortAttribute(checked, self.window.reports_sort_by_date_btn))
        self.window.reports_sort_by_status_btn.clicked.connect(
            lambda checked: self.changeSortAttribute(checked, self.window.reports_sort_by_status_btn))
        self.window.reports_sort_btn.clicked.connect(lambda: self.sortReports(True))
        self.window.reports_filter_input.textChanged.connect(self.filterReportsTree)
        self.window.reports_prev_page_btn.clicked.connect(lambda: self.changePage(-1))
        self.window.reports_next_page_btn.clicked.connect(lambda: self.changePage(1))

        self.order_task.finished.connect(self.orderTaskFinished)
        self.delete_task.finished.connect(self.deleteTaskFinished)
        self.delete_task.progress_changed.connect(self.updateProgress)
        self.download_task.finished.connect(self.downloadTaskFinished)
        self.download_task.progress_changed.connect(self.updateProgress)

    def updateProgress(self, progress):
        self.window.progress_screen.progressBarValue(progress)
        self.window.progress_screen.setWindowTitle(f'R-ABLE ({progress}%)')

    def changePage(self, interval):
        current_page = int(re.sub('^(Page )(\\d+)$', r'\2', self.window.reports_page_label.text()))
        if (interval == -1 and current_page > 1) or interval == 1:
            self.window.reports_tree.clear()
            current_page = current_page + interval
            self.window.reports_page_label.setText(gt.tr('Page %s') % current_page)
            self.reports_monitor.monitorReports(False)

    def changeSortAttribute(self, checked, btn):
        if checked:
            for sort_btn in self.sort_buttons:
                if sort_btn != btn:
                    sort_btn.setChecked(False)
            if self.sort_mode != 'no_sort':
                self.sortReports(False)

    def sortReports(self, change_mode):
        if change_mode:
            if self.sort_mode == 'sort_asc':
                self.sort_mode = 'sort_desc'
            elif self.sort_mode == 'sort_desc':
                self.sort_mode = 'no_sort'
            else:
                self.sort_mode = 'sort_asc'
            self.window.reports_sort_btn.setIcon(QIcon(os.path.join(Path(__file__).parents[1], 'resources', self.sort_mode)))
        sort_column = 1
        qt_sort_mode = Qt.DescendingOrder if self.sort_mode == 'sort_desc' else Qt.AscendingOrder
        for i, btn in enumerate(self.sort_buttons, 2):
            if btn.isChecked() and self.sort_mode != 'no_sort':
                sort_column = i
                break
        qt_sort_mode = Qt.AscendingOrder if sort_column == 1 else qt_sort_mode
        self.window.reports_tree.sortItems(sort_column, qt_sort_mode)

    def filterReportsTree(self, text):
        all_items = self.window.reports_tree.findItems('', Qt.MatchContains, 2)
        found_items = self.window.reports_tree.findItems(text.lower(), Qt.MatchContains, 2)
        hidden_items = [item for item in all_items if item not in found_items]
        for item in hidden_items:
            item.setHidden(True)
        for item in found_items:
            item.setHidden(False)
        self.sortReports(False)

    def reloadTreeButtons(self, curr_item, prev_item):
        if prev_item:
            item_widget = self.window.reports_tree.itemWidget(prev_item, 0)
            if item_widget:
                item_layout = item_widget.layout()
                item_layout.removeWidget(item_widget.findChild(QPushButton, 'info'))
                item_layout.removeWidget(item_widget.findChild(QPushButton, 'pdf'))
                item_layout.removeWidget(item_widget.findChild(QPushButton, 'reject'))
        item_widget = self.window.reports_tree.itemWidget(curr_item, 0)
        if item_widget:
            item_layout = item_widget.layout()
            status = item_widget.findChild(QLabel, 'status_label').text()
            info_btn = gh.createBtn('info', gt.tr('Show report metadata'), lambda: self.displayReportMeta(curr_item))
            pdf_btn = gh.createBtn('pdf', gt.tr('Download and view report'), lambda: self.downloadReportPdf([curr_item]))
            pdf_btn.setEnabled(status == 'SUCCESS')
            del_btn = gh.createBtn('reject', gt.tr('Delete report'), lambda: self.deleteReport([curr_item]))
            item_layout.addWidget(info_btn)
            item_layout.addWidget(pdf_btn)
            item_layout.addWidget(del_btn)

    def orderReport(self):
        units_layout = self.window.reports_selected_units.widget().layout()
        administrative_units = list(map(lambda i: {"code": re.sub('^(.*) \\((\\d+)\\)$', r'\2', units_layout.itemAt(i).widget().findChildren(QLabel)[0].toolTip()),
                                                   "country": "pl"}, range(0, units_layout.count())))
        if self.app.token:
            validation_message = self.reportFormValid(administrative_units)
            if validation_message == '':
                self.order_task.payload = {"year_from": self.window.reports_start_year.value(),
                                           "year_to": self.window.reports_end_year.value(),
                                           "administrative_units": administrative_units,
                                           "title": self.window.reports_title_browser.toPlainText(),
                                           "subtitle": self.window.reports_subtitle_browser.toPlainText(),
                                           "description": self.window.reports_description_browser.toPlainText(),
                                           "author": self.window.reports_author_browser.toPlainText(),
                                           "lang": "pl"}
                self.order_task.token = self.app.token
                self.order_task.config = self.app.auth_manager.currentConfig()
                self.window.progress_screen.showProgress(gt.tr('report generating...'))
                self.order_task.start()
            else:
                msg.createMessage(gt.tr('R-ABLE - report'), QMessageBox.Information, gt.tr('<p>Report form is not valid</p>%s') % validation_message, False)

    def reportFormValid(self, administrative_units):
        validation_message = []
        if len(administrative_units) == 0:
            validation_message.append(gt.tr('<p><i>No administrative units selected</i></p>'))
        if self.window.reports_title_browser.toPlainText().strip() == '':
            validation_message.append(gt.tr('<p><i>Title input is empty</i></p>'))
        if self.window.reports_subtitle_browser.toPlainText().strip() == '':
            validation_message.append(gt.tr('<p><i>Subtitle input is empty</i></p>'))
        if self.window.reports_author_browser.toPlainText().strip() == '':
            validation_message.append(gt.tr('<p><i>Author input is empty</i></p>'))
        if self.window.reports_start_year.value() > self.window.reports_end_year.value():
            validation_message.append(gt.tr('<p><i>Report timeframe is incorrect</i></p>'))
        return ''.join(validation_message)

    def orderTaskFinished(self):
        self.window.setVisible(True)
        self.reports_monitor.monitorReports()
        if self.order_task.error:
            msg.createMessage(gt.tr('R-ABLE - report error'), QMessageBox.Warning,
                              '%s<p><i>%s</i></p>' % (gt.tr('<p>An error occurred while ordering the report</p>'), self.order_task.error),
                              False)
        else:
            msg.createMessage(gt.tr('R-ABLE - report'), QMessageBox.Information,
                              gt.tr('Report(s) ordered successfully'),
                              False)

    def displayReportMeta(self, report_item):
        dialog = ReportMetaDialog(report_item.data(0, 100))
        dialog.exec()

    def downloadReportPdf(self, report_items):
        if self.app.token:
            if len(report_items) > 0:
                self.download_task.report_items = report_items
                self.download_task.token = self.app.token
                self.download_task.config = self.app.auth_manager.currentConfig()
                self.window.progress_screen.showProgress(gt.tr('downloading...'), self.download_task, True)
                self.download_task.start()
        else:
            msg.createMessage(gt.tr('R-ABLE - download report'), QMessageBox.Information,
                              gt.tr('Unable to download report - R-ABLE services not connected'), False)

    def downloadTaskFinished(self):
        self.window.progress_screen.hideProgress()
        if not self.download_task.error:
            reports_len = len(self.download_task.responses)
            if reports_len > 1:
                save_dir = QFileDialog.getExistingDirectory(self.window, gt.tr('Select save folder'), '')
                save = save_dir != ''
            else:
                pdf_file = QFileDialog.getSaveFileName(self.window, gt.tr('Save pdf report'), '', 'Portable Document Format (*.pdf)')[0]
                save = pdf_file != ''
            if save:
                for response in self.download_task.responses:
                    if reports_len > 1:
                        pdf_file = os.path.join(save_dir, '%s.pdf' % response[1])
                    open(pdf_file, 'wb').write(response[0].content)
                    if reports_len == 1:
                        self.openFile(pdf_file)
                        msg.createMessage(gt.tr('R-ABLE - download report'), QMessageBox.Information,
                                          '%s<p>%s</p>' % (gt.tr('<p>Report saved successfully in location:</p>'), pdf_file),
                                          False)
                if reports_len > 1:
                    msg.createMessage(gt.tr('R-ABLE - download reports'), QMessageBox.Information,
                                      '%s<p>%s</p>' % (gt.tr('<p>Reports saved successfully in location:</p>'), save_dir),
                                      False)
        else:
            if not self.download_task.terminated:
                msg.createMessage(gt.tr('R-ABLE - download report'), QMessageBox.Warning,
                                  '%s<p><i>%s</i></p>' % (gt.tr('<p>An error occurred while downloading the report</p>'), self.download_task.error),
                                  False)
            else:
                QgsMessageLog.logMessage('%s: %s' % (gt.tr('Download report'), self.download_task.error), 'R-ABLE', Qgis.Info)

    def openFile(self, pdf_file):
        if platform.system() == "Windows":
            os.startfile(pdf_file)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", pdf_file])
        else:
            subprocess.Popen(["xdg-open", pdf_file])

    def deleteReport(self, report_items):
        if len(report_items) > 0:
            resp = msg.createMessage(gt.tr('R-ABLE - delete report'), QMessageBox.Question,
                                     gt.tr('Do you really want to delete selected report(s)?'))
            if resp == QMessageBox.Ok:
                if self.app.token:
                    self.delete_task.report_items = report_items
                    self.delete_task.token = self.app.token
                    self.delete_task.config = self.app.auth_manager.currentConfig()
                    self.window.progress_screen.showProgress(gt.tr('deleting...'), self.delete_task, True)
                    self.delete_task.start()
                else:
                    msg.createMessage(gt.tr('R-ABLE - delete report'), QMessageBox.Information,
                                      gt.tr('Unable to delete report - R-ABLE services not connected'), False)

    def deleteTaskFinished(self):
        for report_item in self.delete_task.report_items:
            self.deleted_ids.append(report_item.data(0, 100))
            self.window.reports_tree.takeTopLevelItem(self.window.reports_tree.indexOfTopLevelItem(report_item))
        self.window.setVisible(True)
        self.reports_monitor.monitorReports()
        if self.delete_task.error:
            if self.delete_task.terminated:
                QgsMessageLog.logMessage('%s: %s' % (gt.tr('Delete report'), self.download_task.error), 'R-ABLE', Qgis.Info)
            else:
                msg.createMessage(gt.tr('R-ABLE - delete report'), QMessageBox.Warning,
                                  '%s<p><i>%s</i></p>' % (gt.tr('<p>An error occurred while deleting the report</p>'), self.delete_task.error),
                                  False)
        else:
            QgsMessageLog.logMessage(gt.tr('Delete report: selected reports removed from user repository'), 'R-ABLE', Qgis.Success)
