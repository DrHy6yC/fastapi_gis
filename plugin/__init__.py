from PyQt5.QtWidgets import QAction, QMessageBox
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry,
    QgsPointXY, QgsField
)
from qgis.PyQt.QtCore import QVariant
import requests


def classFactory(iface):
    return MinimalSyncPlugin(iface)


class MinimalSyncPlugin:

    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        self.action = QAction("Синхронизировать слои", self.iface.mainWindow())
        self.action.triggered.connect(self.sync_layers)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        # del self.action

    def sync_layers(self):
        # Загрузка объектов из API
        try:
            data = requests.get("http://localhost:8000/features").json()
        except Exception as e:
            print("Ошибка запроса:", e)
            return
        # Создать словарь слоев
        layers = {
            "Point": self.get_or_create_layer("Points_synced", "Point"),
            "LineString": self.get_or_create_layer(
                "Lines_synced",
                "LineString"
            ),
            "Polygon": self.get_or_create_layer("Polygons_synced", "Polygon"),
        }

        # Создание слоев в QGIS
        for layer in layers.values():
            layer.dataProvider().truncate()

        # Парсинг объектов из запроса и добавление их в слои
        for feat in data.get("features", []):
            geom_type = feat["geometry"]["type"]
            coords = feat["geometry"]["coordinates"]
            props = feat.get("properties", {})
            layer = layers.get(geom_type)
            if not layer:
                continue

            f = QgsFeature()
            f.setFields(layer.fields())
            if geom_type == "Point":
                f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(*coords)))
            elif geom_type == "LineString":
                f.setGeometry(
                    QgsGeometry.fromPolylineXY(
                        [QgsPointXY(*pt) for pt in coords]
                    )
                )
            elif geom_type == "Polygon":
                f.setGeometry(
                    QgsGeometry.fromPolygonXY(
                        [[QgsPointXY(*pt) for pt in coords[0]]]
                    )
                )
            f.setAttribute("name", props.get("name", ""))
            f.setAttribute("type", props.get("type", ""))
            layer.dataProvider().addFeature(f)

        # Вывод сообщения об успешной загрузке
        QMessageBox.information(
            None,
            "Синхронизация",
            "Слои успешно синхронизированы."
        )

    def get_or_create_layer(self, name, geom):
        for l in QgsProject.instance().mapLayers().values():
            if l.name() == name:
                return l
        vl = QgsVectorLayer(f"{geom}?crs=EPSG:4326", name, "memory")
        pr = vl.dataProvider()
        pr.addAttributes(
            [
                QgsField("name", QVariant.String),
                QgsField("type", QVariant.String)
            ]
        )
        vl.updateFields()
        QgsProject.instance().addMapLayer(vl)
        return vl
