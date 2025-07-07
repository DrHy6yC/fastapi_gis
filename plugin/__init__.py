from PyQt5.QtWidgets import QAction
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry,
    QgsPointXY, QgsField, QgsMessageLog, Qgis, QgsWkbTypes
)
from qgis.PyQt.QtCore import QVariant
import requests


def classFactory(iface):
    """
    Фабричная функция для создания экземпляра плагина QGIS.

    :param iface: интерфейс QGIS
    :return: экземпляр SyncPlugin
    """
    return SyncPlugin(iface)


class SyncPlugin:
    def __init__(self, iface):
        """
        Инициализация плагина.

        :param iface: интерфейс QGIS
        """
        self.iface = iface
        self.point_layer = None
        self.line_layer = None
        self.polygon_layer = None
        self.sync_action = None

    def initGui(self):
        """
        Добавляет кнопку на панель инструментов QGIS и связывает ее с функцией синхронизации слоев.
        """
        self.sync_action = QAction("Синхронизировать слои", self.iface.mainWindow())
        self.sync_action.triggered.connect(self.sync_layers)
        self.iface.addToolBarIcon(self.sync_action)

    def unload(self):
        """
        Удаляет кнопку с панели инструментов при выгрузке плагина.
        """
        if self.sync_action:
            self.iface.removeToolBarIcon(self.sync_action)
            self.sync_action = None

    def _connect_layer_signals(self):
        """
        Подписывает обработчики событий на редактируемые слои для отслеживания изменений.
        """
        for layer, geometry_type in [
            (self.point_layer, "Point"),
            (self.line_layer, "LineString"),
            (self.polygon_layer, "Polygon"),
        ]:
            if layer:
                layer.editingStarted.connect(
                    lambda l=layer, t=geometry_type: self._log(f"Начато редактирование слоя {t}")
                )

                layer.committedFeaturesAdded.connect(
                    lambda layer_id, added, l=layer, t=geometry_type: self._on_features_added(l, added, t)
                )

                layer.committedFeaturesRemoved.connect(
                    lambda layer_id, removed, l=layer, t=geometry_type: self._on_features_removed(l, removed, t)
                )

                layer.committedAttributeValuesChanges.connect(
                    lambda layer_id, attr_changes, l=layer, t=geometry_type: self._on_features_modified(l, attr_changes, t)
                )

                layer.committedGeometriesChanges.connect(
                    lambda layer_id, geom_changes, l=layer, t=geometry_type: self._on_geometry_modified(l, geom_changes, t)
                )

                layer.editingStopped.connect(
                    lambda l=layer, t=geometry_type: self._log(
                        f"Закончено редактирование слоя {t}"
                    )
                )

    def _on_features_added(self, layer, added_features, geometry_type):
        """
        Обработка добавления новых объектов в слой.

        :param layer: слой, в который добавлены объекты
        :param added_features: список добавленных объектов
        :param geometry_type: тип геометрии ("Point", "LineString", "Polygon")
        """
        for feature in added_features:
            _id = self._send_feature_to_api(feature)
            if _id is None:
                self._log(
                    f"Не удалось получить ID от API для объекта типа «{geometry_type}»"
                )
                continue
            id_idx = layer.fields().indexFromName("id")
            if id_idx == -1:
                self._log("Поле 'id' не найдено в слое.")
                continue

            success = layer.dataProvider().changeAttributeValues({feature.id(): {id_idx: _id}})
            if success:
                self._log(f"Добавлен объект типа «{geometry_type}» с ID {_id}")
            else:
                self._log(
                    f"Не удалось обновить ID объекта типа «{geometry_type}»"
                )

    def _on_features_removed(self, layer, removed_ids, geometry_type):
        """
        Обработка удаления объектов из слоя.

        :param layer: слой, из которого удалены объекты
        :param removed_ids: список ID удалённых объектов
        :param geometry_type: тип геометрии
        """
        for feature_id in removed_ids:
            self._log(f"Удалён объект типа «{geometry_type}» с ID {feature_id}")

    def _on_features_modified(self, layer, attribute_changes, geometry_type):
        """
        Обработка изменения атрибутов объектов в слое.

        :param layer: слой, в котором изменены объекты
        :param attribute_changes: словарь изменений атрибутов {feature_id: {field_index: (old_value, new_value)}}
        :param geometry_type: тип геометрии
        """
        for feature_id in attribute_changes:
            self._log(f"Изменён объект (атрибуты) типа «{geometry_type}» с ID {feature_id}")

    def _on_geometry_modified(self, layer, geometry_changes, geometry_type):
        """
        Обработка изменения геометрии объектов в слое.

        :param layer: слой, в котором изменена геометрия объектов
        :param geometry_changes: словарь изменений геометрии {feature_id: QgsGeometry}
        :param geometry_type: тип геометрии
        """
        for feature_id in geometry_changes:
            self._log(f"Изменён объект (геометрия) типа «{geometry_type}» с ID {feature_id}")

    def _log(self, message: str):
        """
        Записывает информационное сообщение в лог QGIS.

        :param message: текст сообщения
        """
        QgsMessageLog.logMessage(message, "SyncPlugin", level=Qgis.Info)

    def sync_layers(self):
        """
        Основная функция синхронизации.
        Загружает объекты из API, создаёт или получает слои, очищает их,
        добавляет загруженные объекты, и подписывается на события изменений.
        """
        try:
            response = requests.get("http://localhost:8000/features")
            response.raise_for_status()
            data = response.json()
            self._log("Данные успешно загружены из API.")
        except requests.RequestException as error:
            self._log(f"Ошибка запроса к API: {error}")
            return

        self.point_layer = self._get_or_create_layer("Points_synced", "Point")
        self.line_layer = self._get_or_create_layer("Lines_synced", "LineString")
        self.polygon_layer = self._get_or_create_layer("Polygons_synced", "Polygon")

        geometry_type_to_layer = {
            "Point": self.point_layer,
            "LineString": self.line_layer,
            "Polygon": self.polygon_layer,
        }

        # Очистка данных слоев
        for layer in geometry_type_to_layer.values():
            layer.dataProvider().truncate()
            layer.triggerRepaint()

        self._connect_layer_signals()

        # Добавление объектов из API в слои
        for feature_data in data.get("features", []):
            geom_type = feature_data["geometry"]["type"]
            coordinates = feature_data["geometry"]["coordinates"]
            properties = feature_data.get("properties", {})
            layer = geometry_type_to_layer.get(geom_type)
            if not layer:
                self._log(f"Пропущен объект с типом геометрии {geom_type} — слой не найден.")
                continue

            qgs_feature = QgsFeature()
            qgs_feature.setFields(layer.fields())

            if geom_type == "Point":
                qgs_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(*coordinates)))
            elif geom_type == "LineString":
                qgs_feature.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(*pt) for pt in coordinates]))
            elif geom_type == "Polygon":
                qgs_feature.setGeometry(QgsGeometry.fromPolygonXY([[QgsPointXY(*pt) for pt in coordinates[0]]]))
            else:
                self._log(f"Неизвестный тип геометрии: {geom_type}")
                continue

            qgs_feature.setAttribute("name", properties.get("name", ""))
            qgs_feature.setAttribute("type", properties.get("type", ""))
            qgs_feature.setAttribute("id", properties.get("id", 0))
            layer.dataProvider().addFeature(qgs_feature)

        self._log("Слои успешно синхронизированы.")

    def _get_or_create_layer(self, name: str, geometry_type: str) -> QgsVectorLayer:
        """
        Получает существующий слой по имени или создаёт новый временный слой.

        :param name: имя слоя
        :param geometry_type: тип геометрии слоя ("Point", "LineString", "Polygon")
        :return: объект QgsVectorLayer
        """
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() == name:
                return layer

        vector_layer = QgsVectorLayer(f"{geometry_type}?crs=EPSG:4326", name, "memory")
        provider = vector_layer.dataProvider()

        provider.addAttributes([
            QgsField("name", QVariant.String),
            QgsField("type", QVariant.String),
            QgsField("id", QVariant.Int),
        ])
        vector_layer.updateFields()
        QgsProject.instance().addMapLayer(vector_layer)
        self._log(f"Создан новый слой '{name}' с типом геометрии {geometry_type}.")
        return vector_layer

    def _feature_to_geojson_dict(self, feature: QgsFeature) -> dict | None:
        """
        Преобразует QgsFeature в словарь в формате GeoJSON для отправки в API.

        :param feature: объект QgsFeature
        :return: словарь с данными GeoJSON или None при ошибке
        """
        geometry = feature.geometry()
        if geometry is None or geometry.isEmpty():
            self._log("Пустая или отсутствующая геометрия в объекте.")
            return None

        geom_type_display = QgsWkbTypes.displayString(geometry.wkbType())

        if geom_type_display.startswith("Point"):
            geojson_type = "Point"
            coordinates = list(geometry.asPoint())
        elif geom_type_display.startswith("LineString"):
            geojson_type = "LineString"
            coordinates = [list(pt) for pt in geometry.asPolyline()]
        elif geom_type_display.startswith("Polygon"):
            geojson_type = "Polygon"
            polygon = geometry.asPolygon()
            coordinates = [[list(pt) for pt in polygon[0]]] if polygon else []
        else:
            self._log(f"Неподдерживаемый тип геометрии: {geom_type_display}")
            return None

        name_attr = feature["name"]
        if not isinstance(name_attr, (str, int, float, type(None))):
            name_attr = str(name_attr)

        type_attr = feature["type"]
        if not isinstance(type_attr, (str, int, float, type(None))):
            type_attr = str(type_attr)

        return {
            "geometry": {
                "type": geojson_type,
                "coordinates": coordinates,
            },
            "properties": {
                "name": name_attr,
                "type": type_attr,
            },
        }

    def _send_feature_to_api(self, feature: QgsFeature):
        """
        Отправляет объект в REST API.

        :param feature: объект QgsFeature для отправки
        """
        data = self._feature_to_geojson_dict(feature)
        if not data:
            self._log("Не удалось сформировать объект для отправки в API.")
            return

        try:
            response = requests.post(
                "http://localhost:8000/features",
                json=data,
                timeout=5,
            )
            if response.status_code == 201:
                self._log("Объект успешно отправлен в API.")
                return response.json()["id"]
            else:
                self._log(f"Ошибка API: код {response.status_code}, ответ: {response.text}")
        except requests.RequestException as error:
            self._log(f"Ошибка сети при отправке запроса: {error}")

    def _delete_feature_to_api(self, feature: QgsFeature):
        """
        Отправляет объект в REST API.

        :param feature: объект QgsFeature для отправки
        """
        data = self._feature_to_geojson_dict(feature)
        if not data:
            self._log("Не удалось сформировать объект для отправки в API.")
            return

        try:
            response = requests.post(
                "http://localhost:8000/features",
                json=data,
                timeout=5,
            )
            if response.status_code == 201:
                self._log("Объект успешно отправлен в API.")
                return response.json()["id"]
            else:
                self._log(f"Ошибка API: код {response.status_code}, ответ: {response.text}")
        except requests.RequestException as error:
            self._log(f"Ошибка сети при отправке запроса: {error}")

