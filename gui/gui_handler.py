import os
from pathlib import Path
import re

from qgis.PyQt.QtCore import Qt, QSize, QDateTime
from qgis.PyQt.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from qgis.PyQt.QtGui import QFontMetrics, QIcon, QMouseEvent
from .gui_translator import GuiTranslator as gt

RESOURCES_ROOT = os.path.join(Path(__file__).parents[1], 'resources')
LABEL_STYLESHEETS = {'SUCCESS': 'QLabel{color: rgb(5, 151, 49);'
                                'font-weight: bold;'
                                'background-color: rgb(255, 255, 255);'
                                'padding: 2px;'
                                'border-radius: 5px;}',
                     'PROCESSING': 'QLabel{color: rgb(22, 128, 255);'
                                   'font-weight: bold;'
                                   'background-color: rgb(255, 255, 255);'
                                   'padding: 2px;'
                                   'border-radius: 5px;}',
                     'WAITING': 'QLabel{color: rgb(255, 181, 0);'
                                'font-weight: bold;'
                                'background-color: rgb(255, 255, 255);'
                                'padding: 2px;'
                                'border-radius: 5px;}',
                     'unit': 'QLabel{font-weight: bold; '
                             'font-size: 7pt; '
                             'color: rgb(169, 92, 63)}'
                     }


class GuiHandler:

    @staticmethod
    def setupDateRange(interval_btn, start_time_edit, end_time_edit):
        interval = re.sub('^[a-zA-Z]+ (\\d+) [a-zA-Z()?]+$', r'\1', interval_btn.label.text())
        interval = -int(interval) if interval != gt.tr('TimeIntervalButton', 'Last year') else -1
        current_time = QDateTime().currentDateTime()
        past_time = current_time.addYears(interval)
        start_time_edit.setDateTime(past_time)
        end_time_edit.setDateTime(current_time)

    @staticmethod
    def addUnit(window, units_container, input_widget, unit):
        container_width = input_widget.size().width()
        units_layout = units_container.widget().layout()
        selected_units = list(map(lambda i: units_layout.itemAt(i).widget().findChildren(QLabel)[0].toolTip(),
                                  range(0, units_layout.count())))
        country = unit[0:unit.index(' ')].replace(',', '')
        country_units = list(filter(lambda u: country in u, window.units))
        unit_types = []
        for u in country_units:
            if ',' in u:
                break
            unit_types.append(re.sub('^.*\\s(.*)$', r'\1', u))
        unit_type = list(filter(lambda t: re.sub('^.*\\s(.*)$', r'\1', unit) == t, unit_types))
        if len(unit_type) == 1:
            unit_type = unit_type[0]
            parent_unit = unit.replace(' %s' % unit_type, '')
            commas_num = unit_types.index(unit_type) + 1
            units = list(filter(lambda u: parent_unit in u and u.count(',') == commas_num and not any(
                t == re.sub('^.*\\s(.*)$', r'\1', u) for t in unit_types), country_units))
        else:
            units = [unit]
        for unit in units:
            unit_text = re.sub('^(.*) \\((\\d+)\\)$', r'\1', unit)
            if unit_text not in selected_units:
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
                remove_button.clicked.connect(lambda: removeUnit(window, units_container))
                unit_code = re.sub('^(.*) \\((\\d+)\\)$', r'\2', unit)
                unit_label = GuiHandler.createLabel('unit', 'unit_label', True)
                unit_label.setToolTip(unit)
                unit_layout.addWidget(unit_label)
                unit_layout.addWidget(remove_button)
                unit_widget.setLayout(unit_layout)
                units_layout.addWidget(unit_widget)
                font_metrics = QFontMetrics(unit_label.font())
                elided_unit = font_metrics.elidedText(unit_text, Qt.ElideRight, container_width - 60)
                unit_label.setText(elided_unit)

    @staticmethod
    def createLabel(text, obj_name, custom_stylesheet=False):
        label = QLabel(text)
        label.setMinimumHeight(20)
        label.setObjectName(obj_name)
        if custom_stylesheet:
            GuiHandler.setLabelStyleSheet(label, text)
        return label

    @staticmethod
    def setLabelStyleSheet(label, text):
        stylesheet = LABEL_STYLESHEETS.get(text, 'QLabel{color: rgb(224, 43, 54);'
                                                 'font-weight: bold;'
                                                 'background-color: rgb(255, 255, 255);'
                                                 'padding: 2px;'
                                                 'border-radius: 5px;}')
        label.setStyleSheet(stylesheet)

    @staticmethod
    def createBtn(btn_name, tool_tip, signal_func):
        btn = QPushButton()
        btn.setObjectName(btn_name)
        btn.setToolTip(tool_tip)
        btn.setIcon(QIcon(os.path.join(RESOURCES_ROOT, '%s.png' % btn_name)))
        btn.clicked.connect(signal_func)
        return btn

