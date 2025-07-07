from PyQt5.QtWidgets import QAction, QMessageBox
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry,
    QgsPointXY, QgsField, QgsMessageLog, Qgis
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

    # Подписка на события
    def connect_layer_signals(self):
        for layer, name in [
            (self.point_layer, "Point"),
            (self.line_layer, "Line"),
            (self.polygon_layer, "Polygon")
        ]:
            if layer:
                layer.editingStarted.connect(
                    lambda l=layer, t=name: self._log(
                        f"Начато редактирование слоя {t}"
                    )
                )

                layer.committedFeaturesAdded.connect(
                    lambda
                            layer_id,
                            added,
                            l=layer,
                            t=name: self.on_features_added(l, added, t)
                )

                layer.committedFeaturesRemoved.connect(
                    lambda
                            layer_id,
                            removed,
                            l=layer,
                            t=name: self.on_features_removed(l, removed, t)
                )

                layer.committedAttributeValuesChanges.connect(
                    lambda
                            layer_id,
                            attr_changes,
                            l=layer,
                            t=name: self.on_features_modified(
                        l,
                        attr_changes,
                        t
                    )
                )

                layer.committedGeometriesChanges.connect(
                    lambda
                            layer_id,
                            geom_changes,
                            l=layer,
                            t=name: self.on_geometry_modified(
                        l,
                        geom_changes,
                        t
                    )
                )

    def on_editing_stopped(self, layer: QgsVectorLayer, feature_type: str):
        changes = layer.editBuffer().changeSet()

        added = list(layer.editBuffer().addedFeatures().keys())
        deleted = list(layer.editBuffer().deletedFeatureIds())

        if added:
            for fid in added:
                self._show_feature_action_message(
                    "добавлен",
                    feature_type,
                    fid
                )
        if deleted:
            for fid in deleted:
                self._show_feature_action_message("удалён", feature_type, fid)

    # Выполнение действий над объект
    def on_features_added(self, layer, added_ids, feature_type):
        for fid in added_ids:
            self._show_feature_action_message("добавлен", feature_type, fid)

    def on_features_removed(self, layer, removed_ids, feature_type):
        for fid in removed_ids:
            self._show_feature_action_message("удалён", feature_type, fid)

    def on_features_modified(self, layer, changes, feature_type):
        for fid in changes:
            self._show_feature_action_message(
                "изменён (атрибуты)",
                feature_type,
                fid
            )

    def on_geometry_modified(self, layer, changes, feature_type):
        for fid in changes:
            self._show_feature_action_message(
                "изменён (геометрия)",
                feature_type,
                fid
            )

    # Отображение сообщения о событии
    def _show_feature_action_message(
            self,
            action: str,
            feature_type: str,
            feature_id: int
    ):
        QMessageBox.information(
            self.iface.mainWindow(),
            "Событие в слое",
            f"Объект типа «{feature_type}» был {action}. ID: {feature_id}"
        )

    def _log(self, message: str):
        QgsMessageLog.logMessage(message, "MinimalSyncPlugin", level=Qgis.Info)

    def sync_layers(self):
        # Загрузка объектов из API
        try:
            data = requests.get("http://localhost:8000/features").json()
        except Exception as e:
            print("Ошибка запроса:", e)
            return
        # Получить или создать слои и сохранить в self
        self.point_layer = self.get_or_create_layer("Points_synced", "Point")
        self.line_layer = self.get_or_create_layer(
            "Lines_synced",
            "LineString"
        )
        self.polygon_layer = self.get_or_create_layer(
            "Polygons_synced",
            "Polygon"
        )

        layers = {
            "Point": self.point_layer,
            "LineString": self.line_layer,
            "Polygon": self.polygon_layer,
        }

        # Очистить данные в слоях
        for layer in layers.values():
            layer.dataProvider().truncate()

        # Подписка на события
        self.connect_layer_signals()

        # Добавление объектов
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

        field1 = QgsField(name="name", type=QVariant.String)
        field2 = QgsField(name="type", type=QVariant.String)
        pr.addAttributes([field1, field2])
        vl.updateFields()
        QgsProject.instance().addMapLayer(vl)
        return vl
