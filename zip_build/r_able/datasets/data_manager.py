import re
import sip

from qgis.core import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *

from ..map.map_tool import MapTool
from ..gui.gui_handler import GuiHandler as gh
from ..gui.gui_translator import GuiTranslator as gt


class DataManager:
    def __init__(self, app, iface):
        self.app = app
        self.window = app.window
        self.iface = iface
        self.map_tool = MapTool(iface, self.window)
        self.project = QgsProject.instance()
        self.reloadLayersCombo()
        self.connectSignals()

    def connectSignals(self):
        self.project.layersAdded.connect(self.reloadLayersCombo)
        self.project.layersRemoved.connect(self.reloadLayersCombo)
        self.window.data_unit_selection_box.toggled.connect(
            lambda checked: self.changeSearchMode(checked, self.window.data_unit_selection_box))
        self.window.data_search_extent_box.toggled.connect(
            lambda checked: self.changeSearchMode(checked, self.window.data_search_extent_box))
        self.window.data_time_interval_btn.clicked.connect(lambda: gh.setupDateRange(self.window.data_time_interval_btn,
                                                                                     self.window.data_start_time_edit,
                                                                                     self.window.data_end_time_edit))
        self.window.data_active_layer_btn.clicked.connect(lambda: self.getLayerExtent(None))
        self.window.data_layers_combo.currentIndexChanged.connect(lambda idx: self.getLayerExtent(idx))
        self.window.data_select_map_range_btn.clicked.connect(self.drawRange)
        self.window.data_clear_search_btn.clicked.connect(self.clearSearch)

    def reloadLayersCombo(self):
        self.window.data_layers_combo.clear()
        self.window.data_layers_combo.addItem(gt.tr('window', 'Layer'))
        for layer in self.project.mapLayers().values():
            self.window.data_layers_combo.addItem(layer.name(), layer.id())

    def changeSearchMode(self, checked, box):
        if checked:
            if box == self.window.data_unit_selection_box:
                self.window.data_search_extent_box.setChecked(False)
            else:
                self.window.data_unit_selection_box.setChecked(False)
        else:
            if box == self.window.data_unit_selection_box:
                self.window.data_search_extent_box.setChecked(True)
            else:
                self.window.data_unit_selection_box.setChecked(True)

    def getLayerExtent(self, idx):
        current_layer_id = None
        if idx is None:
            if self.iface.activeLayer():
                current_layer_id = self.iface.activeLayer().id()
        else:
            if idx != 0:
                current_layer_id = self.window.data_layers_combo.itemData(idx)
        if current_layer_id is not None:
            map_layer = self.project.mapLayer(current_layer_id)
            extent_geom = QgsGeometry.fromRect(map_layer.extent())
            if not extent_geom.isEmpty():
                self.map_tool.fillSpatialWidget(extent_geom)

    def drawRange(self):
        self.window.position = self.window.pos()
        self.window.hide()
        self.map_tool.drawShape()

    def clearSearch(self):
        self.app.units_manager.clearSelectedUnits(self.window.data_selected_units, self.window.data_unit_input)
        self.map_tool.clearRubber()
        self.clearSpatialExtentWidget()

    def clearSpatialExtentWidget(self):
        self.window.data_west_input.clear()
        self.window.data_south_input.clear()
        self.window.data_east_input.clear()
        self.window.data_north_input.clear()
