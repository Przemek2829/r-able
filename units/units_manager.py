import os
import re
import json

from qgis.core import QgsMessageLog, Qgis
from qgis.PyQt.QtCore import Qt, QSize
from qgis.PyQt.QtWidgets import QMessageBox, QCompleter, QLabel, QWidget, QHBoxLayout, QPushButton
from qgis.PyQt.QtGui import QFontMetrics

from .get_units_task import GetUnitsTask
from .supply_units_task import SupplyUnitsTask
from r_able.gui.gui_handler import GuiHandler as gh
from r_able.messenger import Messenger as msg


class UnitsManager:
    def __init__(self, app):
        self.app = app
        self.country_codes = self.countryCodes()
        self.window = app.window
        self.get_units_task = GetUnitsTask(self)
        self.supply_data_units_task = SupplyUnitsTask(self,
                                                      self.window.data_selected_units,
                                                      self.window.data_unit_input,
                                                      self.window.data_progress_label,
                                                      [self.window.data_adm_load_datasets_btn,
                                                       self.window.data_clear_search_btn])
        self.supply_reports_units_task = SupplyUnitsTask(self,
                                                         self.window.reports_selected_units,
                                                         self.window.reports_unit_input,
                                                         self.window.reports_progress_label,
                                                         [self.window.reports_clear_units_btn,
                                                          self.window.reports_order_report_btn])
        self.units = []
        self.units_completer = QCompleter(self.units)
        self.get_units_task.finished.connect(self.getUnitsTaskFinished)
        self.window.data_unit_input.editingFinished.connect(lambda: self.addUnits(self.supply_data_units_task))
        self.supply_data_units_task.progress_changed.connect(lambda units: self.fillUnits(self.supply_data_units_task, units))
        self.supply_data_units_task.finished.connect(lambda: self.fillUnits(self.supply_data_units_task))

        self.supply_reports_units_task.progress_changed.connect(lambda units: self.fillUnits(self.supply_reports_units_task, units))
        self.supply_reports_units_task.finished.connect(lambda: self.fillUnits(self.supply_reports_units_task))
        self.window.reports_unit_input.editingFinished.connect(lambda: self.addUnits(self.supply_reports_units_task))

    def countryCodes(self):
        with open(os.path.join(os.path.dirname(__file__), 'country_codes.json'), encoding='utf-8') as f:
            return json.load(f)

    def configureCompleter(self):
        self.units_completer = QCompleter(self.units)
        self.units_completer.setFilterMode(Qt.MatchContains)
        self.units_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.window.data_unit_input.setCompleter(self.units_completer)
        self.window.reports_unit_input.setCompleter(self.units_completer)

    def getUnits(self):
        if self.window.app.token:
            self.window.progress_screen.ui.labelLoadingInfo.setText('units loading...')
            self.get_units_task.auth_manager = self.app.auth_manager
            self.get_units_task.token = self.app.token
            self.get_units_task.start()

    def getUnitsTaskFinished(self):
        self.window.progress_screen.hideProgress()
        self.configureCompleter()
        if self.get_units_task.error:
            msg.createMessage('R-ABLE - download units', QMessageBox.Warning,
                              '<p>An error occurred while downloading units</p>'
                              '<p><i>%s</i></p>' % self.get_units_task.error,
                              False)
        else:
            QgsMessageLog.logMessage('Units successfully loaded', 'R-ABLE', Qgis.Success)

    def addUnits(self, supply_task):
        self.lockGui(supply_task)
        supply_task.start()

    def lockGui(self, supply_task):
        supply_task.input_widget.setEnabled(False)
        supply_task.progress_label.show()
        for btn in supply_task.buttons:
            btn.setEnabled(False)

    def fillUnits(self, supply_task, supply_units=None):
        if supply_units:
            units = supply_units
        else:
            units = supply_task.supply_units
        units_container = supply_task.units_container
        units_layout = units_container.widget().layout()
        container_width = supply_task.input_widget.size().width()
        for unit, unit_text, unit_code in units:
            units_container.show()
            unit_widget = QWidget()
            unit_widget.setMaximumHeight(25)
            unit_widget.setObjectName('unit_container')
            unit_widget.setStyleSheet('QWidget#unit_container{'
                                      'background-color: rgba(169, 92, 63, 100);'
                                      'border: 1px solid rgb(169, 92, 63);'
                                      'border-radius: 5px}'
                                      'QWidget#unit_container:hover{'
                                      'background-color: rgba(169, 92, 63, 0);}')
            unit_layout = QHBoxLayout()
            unit_layout.setContentsMargins(5, 2, 5, 2)
            unit_layout.setSpacing(5)
            remove_button = QPushButton('x')
            remove_button.setMinimumSize(QSize(20, 20))
            remove_button.setMaximumSize(QSize(20, 20))
            remove_button.setStyleSheet('QPushButton{'
                                        'color: rgb(169, 92, 63);'
                                        'background-color: rgba(0, 0, 0, 0);'
                                        'border: 2px solid rgba(0, 0, 0, 0);}'
                                        'QPushButton:hover{font-weight: bold;}'
                                        'QPushButton:pressed{color: rgb(0, 0, 0)}')
            remove_button.clicked.connect(lambda: self.removeUnit(units_container))
            unit_label = gh.createLabel('unit', 'unit_label', True)
            unit_label.setToolTip(unit)
            unit_layout.addWidget(unit_label)
            unit_layout.addWidget(remove_button)
            unit_widget.setLayout(unit_layout)
            units_layout.addWidget(unit_widget)
            font_metrics = QFontMetrics(unit_label.font())
            elided_unit = font_metrics.elidedText(unit_text, Qt.ElideRight, container_width - 60)
            unit_label.setText(elided_unit)
        if not supply_units:
            self.unlockGui(supply_task)
            supply_task.progress_label.hide()
        units_container.parent().setTitle('Unit(s) search (%s)' % units_layout.count())

    def unlockGui(self, supply_task):
        supply_task.input_widget.setEnabled(True)
        for btn in supply_task.buttons:
            btn.setEnabled(True)

    def removeUnit(self, units_container):
        unit_widget = self.window.focusWidget().parent()
        units_layout = units_container.widget().layout()
        units_layout.removeWidget(unit_widget)
        unit_widget.deleteLater()
        units_count = units_layout.count()
        if units_count == 0:
            units_container.parent().setTitle('Unit(s) search')
        else:
            units_container.parent().setTitle('Unit(s) search (%s)' % units_count)

    def clearSelectedUnits(self, units_container, units_input):
        units_layout = units_container.widget().layout()
        units_input.clear()
        for i in range(0, units_layout.count()):
            selected_unit_item = units_layout.takeAt(0)
            if selected_unit_item is not None:
                selected_unit_item.widget().deleteLater()
        units_container.parent().setTitle('Unit(s) search')
