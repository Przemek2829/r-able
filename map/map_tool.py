from qgis.core import *
from qgis.gui import QgsMapTool, QgsMapToolPan, QgsRubberBand, QgsSnapIndicator

from qgis.PyQt.QtGui import QColor, QKeySequence
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import Qt


COLOR = QColor(5, 151, 49)
BUFFER_COLOR = QColor(255, 255, 255)
FILL_COLOR = QColor(5, 151, 49, 25)
TEMP_FILL_COLOR = QColor(0, 0, 0, 0)
WGS_CRS = QgsCoordinateReferenceSystem('EPSG:4326')


class MapTool(QgsMapTool):
    def __init__(self, iface, window):
        self.iface = iface
        self.window = window
        self.map_canvas = iface.mapCanvas()
        self.project = QgsProject.instance()
        self.annotation_layer = self.project.mainAnnotationLayer()
        self.annotation_layer.setCrs(self.project.crs())
        self.start_new_rubber = True
        self.rubber, self.temp_rubber = None, None
        QgsMapTool.__init__(self, self.map_canvas)
        self.project.crsChanged.connect(self.changeAnnotationLayerCrs)
        self.deactivated.connect(self.toolDeactivated)

    def changeAnnotationLayerCrs(self):
        self.annotation_layer.setCrs(self.project.crs())

    def toolDeactivated(self):
        extent_geom = self.rubber.asGeometry()
        if not extent_geom.isEmpty():
            self.fillSpatialWidget(extent_geom)
        self.window.show()

    def fillSpatialWidget(self, geom):
        tr_wgs = QgsCoordinateTransform(self.project.crs(), WGS_CRS, self.project)
        geom.transform(tr_wgs)
        extent = geom.boundingBox()
        x_min = str(round(extent.xMinimum(), 8))
        y_min = str(round(extent.yMinimum(), 8))
        x_max = str(round(extent.xMaximum(), 8))
        y_max = str(round(extent.yMaximum(), 8))
        self.window.data_west_input.setText(str(x_min))
        self.window.data_south_input.setText(str(y_min))
        self.window.data_east_input.setText(str(x_max))
        self.window.data_north_input.setText(str(y_max))

    def drawShape(self):
        self.clearRubber()
        self.rubber = self.createRubber(COLOR, FILL_COLOR, Qt.DashLine)
        self.temp_rubber = self.createRubber(COLOR, TEMP_FILL_COLOR, Qt.DashLine)
        self.map_canvas.setMapTool(self)

    def createRubber(self, color, fill_color, line_style):
        rubber = QgsRubberBand(self.map_canvas, QgsWkbTypes.PolygonGeometry)
        rubber.setColor(color)
        rubber.setFillColor(fill_color)
        rubber.setLineStyle(line_style)
        rubber.setWidth(2)
        return rubber

    def canvasReleaseEvent(self, event):
        button = event.button()
        if button == Qt.LeftButton:
            point = event.mapPoint()
            if self.start_new_rubber:
                self.rubber.reset(QgsWkbTypes.PolygonGeometry)
                self.start_new_rubber = False
                self.rubber.addPoint(point)
                self.temp_rubber.addPoint(point)
            else:
                self.rubber.reset(QgsWkbTypes.PolygonGeometry)
                geometry = self.temp_rubber.asGeometry()
                self.rubber.addGeometry(geometry)
                self.temp_rubber.reset(QgsWkbTypes.PolygonGeometry)
                self.start_new_rubber = True
                self.setSelectionTool()
                self.addAreaLabel(self.rubber)
                if self.window.position is not None:
                    self.window.move(self.window.position)

    def canvasMoveEvent(self, event):
        geometry = self.rubber.asGeometry()
        if not geometry.isEmpty() and not self.start_new_rubber:
            point = event.mapPoint()
            start_point = self.rubber.getPoint(0)
            self.temp_rubber.reset(QgsWkbTypes.PolygonGeometry)
            p2 = QgsPointXY(point.x(), start_point.y())
            p3 = QgsPointXY(start_point.x(), point.y())
            self.temp_rubber.addPoint(start_point)
            self.temp_rubber.addPoint(p2)
            self.temp_rubber.addPoint(point)
            self.temp_rubber.addPoint(p3)
            self.temp_rubber.addPoint(start_point)
            self.addAreaLabel()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.clearRubber()
            self.setSelectionTool()

    def clearRubber(self):
        self.annotation_layer.clear()
        if self.rubber is not None:
            self.rubber.reset(QgsWkbTypes.PolygonGeometry)
        if self.temp_rubber is not None:
            self.temp_rubber.reset(QgsWkbTypes.PolygonGeometry)
        self.start_new_rubber = True

    def addAreaLabel(self, rubber=None):
        if rubber is None:
            rubber = self.temp_rubber
        self.annotation_layer.clear()
        zone_geom = rubber.asGeometry()
        if not zone_geom.isEmpty():
            c = 0
            for v in zone_geom.vertices():
                if c > 3:
                    break
                c += 1
            if c > 3:
                distance_area = QgsDistanceArea()
                distance_area.setSourceCrs(self.project.crs(), QgsCoordinateTransformContext())
                area = distance_area.convertAreaMeasurement(distance_area.measureArea(zone_geom), QgsUnitTypes.AreaSquareMeters)
                if area < 100:
                    unit = 'm2'
                elif 100 < area < 10000:
                    area = area / 100
                    unit = 'a'
                else:
                    area = area / 10000
                    unit = 'ha'
                point_geom = zone_geom.centroid()
                label = QgsAnnotationPointTextItem('%s %s' % (int(area), unit), point_geom.asPoint())
                text_format = QgsTextFormat()
                buffer = text_format.buffer()
                buffer.setEnabled(True)
                text_format.setColor(COLOR)
                font = text_format.font()
                font.setFamily('Calibri')
                font.setBold(True)
                text_format.setFont(font)
                label.setFormat(text_format)
                self.annotation_layer.addItem(label)

    def setSelectionTool(self):
        self.iface.actionSelect().trigger()
