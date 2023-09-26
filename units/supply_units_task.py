import re
import time

from qgis.PyQt.QtCore import QThread, pyqtSignal
from qgis.PyQt.QtWidgets import QLabel


class SupplyUnitsTask(QThread):
    progress_changed = pyqtSignal(object)

    def __init__(self, manager, units_container, input_widget, progress_label, buttons):
        super(SupplyUnitsTask, self).__init__()
        self.manager = manager
        self.units_container = units_container
        self.input_widget = input_widget
        self.progress_label = progress_label
        self.buttons = buttons

    def run(self):
        self.error = None
        self.supply_units = []
        unit = self.input_widget.text()
        units_layout = self.units_container.widget().layout()
        selected_units = list(map(lambda i: units_layout.itemAt(i).widget().findChildren(QLabel)[0].toolTip(),
                                  range(0, units_layout.count())))
        try:
            country = unit[0:unit.index(' ')].replace(',', '')
        except:
            country = ''
        country_units = list(filter(lambda u: country in u, self.manager.units))
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
        c = 1
        for unit in units:
            unit_text = re.sub('^(.*) \\((\\d+)\\)$', r'\1', unit)
            if unit in self.manager.units and unit not in selected_units:
                unit_code = re.sub('^(.*) \\((\\d+)\\)$', r'\2', unit)
                self.supply_units.append((unit, unit_text, unit_code))
                if c == 100:
                    self.progress_changed.emit(self.supply_units.copy())
                    self.supply_units.clear()
                    c = 0
                    time.sleep(1)
                c += 1
