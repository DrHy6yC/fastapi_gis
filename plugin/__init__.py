from PyQt5.QtWidgets import QAction, QMessageBox
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry,
    QgsPointXY, QgsField, QgsMessageLog, Qgis, QgsWkbTypes
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

    # Выполнение действий над объектом
    def on_features_added(self, layer, added_features, feature_type):
        for feature in added_features:
            self.send_feature_to_api(feature)

    def on_features_removed(self, layer, removed_ids, feature_type):
        for fid in removed_ids:
            self._show_feature_action_message(
                "удален",
                feature_type,
                fid
            )

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
            f.setAttribute("id", props.get("id", ""))
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
        field3 = QgsField(name="id", type=QVariant.Int)
        pr.addAttributes([field1, field2, field3])
        vl.updateFields()
        QgsProject.instance().addMapLayer(vl)
        return vl

    # Получить данные о добавляемом объекте
    def feature_to_geojson_dict(self, feature: QgsFeature):
        geom = feature.geometry()
        if geom is None or geom.isEmpty():
            return None

        geom_type = QgsWkbTypes.displayString(geom.wkbType())

        if geom_type.startswith("Point"):
            geojson_type = "Point"
            coords = list(geom.asPoint())
        elif geom_type.startswith("LineString"):
            geojson_type = "LineString"
            coords = [list(pt) for pt in geom.asPolyline()]
        elif geom_type.startswith("Polygon"):
            geojson_type = "Polygon"
            polygon = geom.asPolygon()
            coords = [[list(pt) for pt in polygon[0]]] if polygon else []
        else:
            return None

        # Извлечение атрибутов с приведением к Python-типам
        name = feature["name"]
        name = name if isinstance(
            name,
            (str, int, float, type(None))
        ) else str(name)

        type_ = feature["type"]
        type_ = type_ if isinstance(
            type_,
            (str, int, float, type(None))
        ) else str(type_)

        return {
            "geometry": {
                "type": geojson_type,
                "coordinates": coords
            },
            "properties": {
                "name": name,
                "type": type_
            }
        }

    # Добавление объекта в API
    def send_feature_to_api(self, feature: QgsFeature):
        data = self.feature_to_geojson_dict(feature)
        if not data:
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Ошибка",
                "Не удалось сформировать объект для отправки."
            )
            return

        try:
            response = requests.post(
                "http://localhost:8000/features",  # URL вашего API
                json=data,
                timeout=5
            )
            if response.status_code == 201:
                QMessageBox.information(
                    self.iface.mainWindow(),
                    "Успешно",
                    "Объект отправлен в API успешно."
                )
            else:
                QMessageBox.warning(
                    self.iface.mainWindow(),
                    "Ошибка API",
                    f"Код ответа: {response.status_code}\nТело: {response.text}"
                )
        except requests.RequestException as e:
            QMessageBox.critical(
                self.iface.mainWindow(),
                "Сетевой сбой",
                f"Ошибка при запросе:\n{str(e)}"
            )