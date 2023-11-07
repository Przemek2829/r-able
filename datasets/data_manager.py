import os.path
import re
import shutil
import time
import sip
import json
import tempfile
import glob

from qgis.core import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
import processing

from .get_data_task import GetDataTask
from ..map.map_tool import MapTool
from ..messenger import Messenger as msg
from ..gui.dataset_settings_dialog import DatasetSettingsDialog
from ..gui.gui_handler import GuiHandler as gh
from ..gui.gui_translator import GuiTranslator as gt


class DataManager:
    def __init__(self, app, iface):
        self.app = app
        self.window = app.window
        self.iface = iface
        self.map_tool = MapTool(iface, self.window)
        self.project = QgsProject.instance()
        self.get_data_task = GetDataTask()
        self.reloadLayersCombo()
        self.connectSignals()
        self.clearTempDatasets()

    def tr(self, message):
        return QCoreApplication.instance().translate('DataManager', message)

    def clearTempDatasets(self):
        gpkg_files = glob.glob('%s/**/*.gpkg' % os.path.dirname(__file__), recursive=True)
        for f in gpkg_files:
            try:
                os.remove(f)
            except:
                pass

    def connectSignals(self):
        self.window.data_settings_btn.clicked.connect(self.showSettings)
        self.project.layersAdded.connect(self.reloadLayersCombo)
        self.project.layersRemoved.connect(self.reloadLayersCombo)
        self.window.data_unit_selection_box.toggled.connect(
            lambda checked: self.changeSearchMode(checked, self.window.data_unit_selection_box))
        self.window.data_search_extent_box.toggled.connect(
            lambda checked: self.changeSearchMode(checked, self.window.data_search_extent_box))
        self.window.data_active_layer_btn.clicked.connect(lambda: self.getLayerExtent(None))
        self.window.data_layers_combo.currentIndexChanged.connect(lambda idx: self.getLayerExtent(idx))
        self.window.data_select_map_range_btn.clicked.connect(self.drawRange)
        self.window.data_load_datasets_btn.clicked.connect(self.getRableData)
        self.window.data_clear_search_btn.clicked.connect(self.clearSearch)
        self.get_data_task.finished.connect(self.getDataTaskFinished)

    def showSettings(self):
        dialog = DatasetSettingsDialog()
        dialog.exec()

    def reloadLayersCombo(self):
        self.window.data_layers_combo.clear()
        self.window.data_layers_combo.addItem(self.tr('Layer'))
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
                self.map_tool.fillSpatialWidget(extent_geom, map_layer.crs())

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

    def getRableData(self):
        year = self.window.data_years_from_box.value()
        if self.app.token:
            extent = self.validateExtent()
            if not(isinstance(extent, str)):
                self.get_data_task.payload = {"year": self.window.data_years_from_box.value(),
                                              "extent": extent}
                self.get_data_task.token = self.app.token
                self.get_data_task.config = self.app.auth_manager.currentConfig()
                self.window.progress_screen.showProgress(self.tr('data downloading...'), self.get_data_task, can_terminate=True)
                self.get_data_task.start()
            else:
                msg.createMessage(self.tr('R-ABLE - data'), QMessageBox.Warning, extent, False)
        else:
            msg.createMessage(self.tr('R-ABLE - connection error'), QMessageBox.Warning,
                              '%s' % (self.tr('<p>An attempt to connect to the R-ABLE service failed</p>')),
                              False)

    def validateExtent(self):
        units_layout = self.window.data_selected_units.widget().layout()
        if self.window.data_unit_selection_box.isChecked():
            extent = list(map(lambda i: {"code": re.sub('^(.*) \\((\\d+)\\)$', r'\2', units_layout.itemAt(i).widget().findChildren(QLabel)[0].toolTip()),
                                         "country": "pl"}, range(0, units_layout.count())))
            if len(extent) == 0:
                return self.tr('<i>No administrative units selected</i>')
            else:
                return extent
        else:
            try:
                xmin = float(self.window.data_west_input.text())
                ymin = float(self.window.data_south_input.text())
                xmax = float(self.window.data_east_input.text())
                ymax = float(self.window.data_north_input.text())
                return {'geometry': json.loads(QgsGeometry.fromRect(QgsRectangle(xmin, ymin, xmax, ymax)).asJson())}
            except:
                return self.tr('<i>Given extent is invalid</i>')

    def getDataTaskFinished(self):
        self.window.progress_screen.hideProgress()
        if self.get_data_task.terminated:
            msg.createMessage(self.tr('R-ABLE - data'), QMessageBox.Warning,
                              self.tr('Terminated by user'),
                              False)
        elif self.get_data_task.error:
            msg.createMessage(self.tr('R-ABLE - data error'), QMessageBox.Warning,
                              '%s<p><i>%s</i></p>' % (self.tr('<p>An error occurred while downloading data</p>'), self.get_data_task.error),
                              False)
        else:
            data_file = tempfile.NamedTemporaryFile(suffix='.gpkg', delete=False)
            data_file.write(self.get_data_task.response.content)
            temp_path = os.path.join(os.path.dirname(__file__), os.path.basename(data_file.name))
            shutil.copy(data_file.name, temp_path)
            data_file.close()
            os.remove(data_file.name)
            layer = QgsVectorLayer(temp_path, f'Arable land {self.window.data_years_from_box.value()}', "ogr")
            mem_layer = layer.materialize(QgsFeatureRequest().setFilterFids(layer.allFeatureIds()))
            mem_layer.loadNamedStyle(os.path.join(os.path.dirname(__file__), 'style.qml'))
            self.project.addMapLayer(mem_layer)
            QgsMessageLog.logMessage(self.tr('R-ABLE - data: Data downloaded successfully, result added to map'), 'R-ABLE', Qgis.Success)
