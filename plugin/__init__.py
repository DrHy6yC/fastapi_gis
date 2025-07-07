"""
SyncPlugin — плагин QGIS для синхронизации векторных слоев с REST API.

Поддерживает загрузку объектов из API, отображение на карте, а также отправку
изменений (добавление и удаление объектов) обратно на сервер.

Версия QGIS: >= 3.40
"""
import os
import requests
from typing import Optional, Any, Dict, List

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry,
    QgsPointXY, QgsField, QgsMessageLog, Qgis, QgsWkbTypes
)

def classFactory(iface: Any) -> 'SyncPlugin':
    """
    Фабричная функция для создания экземпляра плагина QGIS.

    :param iface: интерфейс QGIS
    :return: экземпляр SyncPlugin
    """
    return SyncPlugin(iface)


class SyncPlugin:
    """
    Класс плагина для синхронизации слоев QGIS с удалённым REST API.
    Обеспечивает загрузку, создание и обновление векторных слоев, а также
    взаимодействие с API при добавлении и удалении объектов.
    """
    def __init__(self, iface: Any) -> None:
        """
        Инициализация плагина.

        :param iface: интерфейс QGIS
        """
        self.iface = iface
        self.point_layer: Optional[QgsVectorLayer] = None
        self.line_layer: Optional[QgsVectorLayer] = None
        self.polygon_layer: Optional[QgsVectorLayer] = None
        self.sync_action: Optional[QAction] = None
        self._ids: Dict[str, Dict[int, int]] = {}

    def initGui(self) -> None:
        """
        Добавляет кнопку на панель инструментов для запуска синхронизации.
        """
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        icon = QIcon(icon_path)
        self.sync_action = QAction(icon,"Синхронизировать слои", self.iface.mainWindow())
        self.sync_action.triggered.connect(self.sync_layers)
        self.iface.addToolBarIcon(self.sync_action)

    def unload(self) -> None:
        """
        Удаляет кнопку с панели инструментов при выгрузке плагина.
        """
        if self.sync_action:
            self.iface.removeToolBarIcon(self.sync_action)
            self.sync_action = None

    def _connect_layer_signals(self) -> None:
        """
        Подключает обработчики событий (добавление, удаление, редактирование)
        к каждому из синхронизируемых слоев.
        """
        for layer, geometry_type in [
            (self.point_layer, "Point"),
            (self.line_layer, "LineString"),
            (self.polygon_layer, "Polygon"),
        ]:
            if not layer:
                continue

            try:
                layer.editingStarted.disconnect()
                layer.committedFeaturesAdded.disconnect()
                layer.committedFeaturesRemoved.disconnect()
                layer.committedAttributeValuesChanges.disconnect()
                layer.committedGeometriesChanges.disconnect()
                layer.editingStopped.disconnect()
            except Exception:
                pass

            layer.editingStarted.connect(self._make_editing_started_callback(layer, geometry_type))
            layer.committedFeaturesAdded.connect(self._make_features_added_callback(layer, geometry_type))
            layer.committedFeaturesRemoved.connect(self._make_features_removed_callback(layer, geometry_type))
            layer.committedAttributeValuesChanges.connect(self._make_features_modified_callback(layer, geometry_type))
            layer.committedGeometriesChanges.connect(self._make_geometry_modified_callback(layer, geometry_type))
            layer.editingStopped.connect(self._make_editing_stopped_callback(layer, geometry_type))

    def _make_editing_started_callback(self, layer: QgsVectorLayer, geometry_type: str):
        """
        Создает callback-функцию для события изменения геометрии объектов.

        :param layer: слой QGIS
        :param geometry_type: тип геометрии слоя
        :return: callback-функция
        """
        def callback() -> None:
            self._log(f"Начато редактирование слоя {geometry_type}")
        return callback

    def _make_editing_stopped_callback(self, layer: QgsVectorLayer, geometry_type: str):
        """
        Создает callback-функцию для события изменения геометрии объектов.

        :param layer: слой QGIS
        :param geometry_type: тип геометрии слоя
        :return: callback-функция
        """
        def callback() -> None:
            self._log(f"Закончено редактирование слоя {geometry_type}")
        return callback

    def _make_features_added_callback(self, layer: QgsVectorLayer, geometry_type: str):
        """
        Создает callback-функцию для события изменения геометрии объектов.

        :param layer: слой QGIS
        :param geometry_type: тип геометрии слоя
        :return: callback-функция
        """
        def callback(layer_id: str, added: List[QgsFeature]) -> None:
            self._on_features_added(layer, added, geometry_type)
        return callback

    def _make_features_removed_callback(self, layer: QgsVectorLayer, geometry_type: str):
        """
        Создает callback-функцию для события изменения геометрии объектов.

        :param layer: слой QGIS
        :param geometry_type: тип геометрии слоя
        :return: callback-функция
        """
        def callback(layer_id: str, removed: List[int]) -> None:
            self._on_features_removed(layer, removed, geometry_type)
        return callback

    def _make_features_modified_callback(self, layer: QgsVectorLayer, geometry_type: str):
        """
        Создает callback-функцию для события изменения геометрии объектов.

        :param layer: слой QGIS
        :param geometry_type: тип геометрии слоя
        :return: callback-функция
        """
        def callback(layer_id: str, attr_changes: Dict[int, Dict[int, Any]]) -> None:
            self._on_features_modified(layer, attr_changes, geometry_type)
        return callback

    def _make_geometry_modified_callback(self, layer: QgsVectorLayer, geometry_type: str):
        """
        Создает callback-функцию для события изменения геометрии объектов.

        :param layer: слой QGIS
        :param geometry_type: тип геометрии слоя
        :return: callback-функция
        """
        def callback(layer_id: str, geom_changes: Dict[int, QgsGeometry]) -> None:
            self._on_geometry_modified(layer, geom_changes, geometry_type)
        return callback

    def _on_features_added(self, layer: QgsVectorLayer, added_features: List[QgsFeature], geometry_type: str) -> None:
        """
        Обработчик события добавления объектов в слой.

        :param layer: слой QGIS
        :param added_features: список добавленных объектов
        :param geometry_type: тип геометрии слоя
        """
        for feature in added_features:
            _id = self._send_feature_to_api(feature)
            if _id is None:
                self._log(f"Не удалось получить ID от API для объекта типа "
                          f"«{geometry_type}»", Qgis.Critical)
                continue
            id_idx = layer.fields().indexFromName("id")
            if id_idx == -1:
                self._log("Поле 'id' не найдено в слое.", Qgis.Critical)
                continue

            success = layer.dataProvider().changeAttributeValues({feature.id(): {id_idx: _id}})
            layer_name = layer.name()
            if layer_name not in self._ids:
                self._ids[layer_name] = {}
            self._ids[layer_name][feature.id()] = _id
            if success:
                self._log(f"Добавлен объект типа «{geometry_type}» с ID {_id}")
            else:
                self._log(f"Не удалось обновить ID объекта типа «"
                          f"{geometry_type}»", Qgis.Critical)

    def _on_features_removed(self, layer: QgsVectorLayer, removed_ids: List[int], geometry_type: str) -> None:
        """
       Обработчик события удаления объектов из слоя.

       :param layer: слой QGIS
       :param removed_ids: список ID удаленных объектов
       """
        for feature_id in removed_ids:
            self._delete_feature_from_api(feature_id, layer)

    def _on_features_modified(self, layer: QgsVectorLayer, attribute_changes: Dict[int, Dict[int, Any]], geometry_type: str) -> None:
        """
        Обработчик события изменения атрибутов объектов.

        :param layer: слой QGIS
        :param attribute_changes: словарь изменений атрибутов
        :param geometry_type: тип геометрии слоя
        """
        for feature_id in attribute_changes:
            self._log(f"Мог быть изменён объект (атрибуты) типа «{geometry_type}» с ID {feature_id}, но пока нет метода для отправки данных на API")

    def _on_geometry_modified(self, layer: QgsVectorLayer, geometry_changes: Dict[int, QgsGeometry], geometry_type: str) -> None:
        """
        Обработчик события изменения геометрии объектов.

        :param layer: слой QGIS
        :param geometry_changes: словарь изменений геометрии
        :param geometry_type: тип геометрии слоя
        """
        for feature_id in geometry_changes:
            self._log(f"Мог быть изменён объект (геометрия) типа «{geometry_type}» с ID {feature_id}, но пока нет метода для отправки данных на API")

    def _log(self, message: str) -> None:
        """
        Записывает сообщение в лог QGIS.

        :param message: сообщение для записи
        """
        QgsMessageLog.logMessage(message, "SyncPlugin", level=Qgis.Info)

    def sync_layers(self) -> None:
        """
        Основная функция синхронизации слоёв с API.
        Загружает данные из API и обновляет слои в QGIS.
        """
        try:
            response = requests.get("http://localhost:8000/features")
            response.raise_for_status()
            data = response.json()
            self._log("Данные успешно загружены из API.")
        except requests.RequestException as error:
            self._log(f"Ошибка запроса к API: {error}", Qgis.Critical)
            return

        self.point_layer = self._get_or_create_layer("Points_synced", "Point")
        self.line_layer = self._get_or_create_layer("Lines_synced", "LineString")
        self.polygon_layer = self._get_or_create_layer("Polygons_synced", "Polygon")

        geometry_type_to_layer = {
            "Point": self.point_layer,
            "LineString": self.line_layer,
            "Polygon": self.polygon_layer,
        }

        for layer in geometry_type_to_layer.values():
            if layer:
                layer.dataProvider().truncate()
                layer.triggerRepaint()

        self._connect_layer_signals()

        for feature_data in data.get("features", []):
            geom_type = feature_data["geometry"]["type"]
            coordinates = feature_data["geometry"]["coordinates"]
            properties = feature_data.get("properties", {})
            external_id = properties.get("id", 0)
            layer = geometry_type_to_layer.get(geom_type)
            if not layer:
                self._log(f"Пропущен объект с типом геометрии {geom_type} — слой не найден.", Qgis.Critical)
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
                self._log(f"Неизвестный тип геометрии: {geom_type}",
                    Qgis.Warning)
                continue

            qgs_feature.setAttribute("name", properties.get("name", ""))
            qgs_feature.setAttribute("type", properties.get("type", ""))
            qgs_feature.setAttribute("id", external_id)
            success = layer.dataProvider().addFeature(qgs_feature)
            if success:
                internal_id = qgs_feature.id()
                layer_name = layer.name()
                if layer_name not in self._ids:
                    self._ids[layer_name] = {}
                self._ids[layer_name][internal_id] = external_id
                self._log(f"Объект добавлен: QGIS-ID={layer_name}/{internal_id} → API-ID={external_id}")
            else:
                self._log("Не удалось добавить объект в слой.", Qgis.Critical)

        self._log("Слои успешно синхронизированы.")

    def _get_or_create_layer(self, name: str, geometry_type: str) -> QgsVectorLayer:
        """
        Получает существующий или создает новый векторный слой.

        :param name: имя слоя
        :param geometry_type: тип геометрии слоя
        :return: векторный слой QGIS
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

    def _feature_to_geojson_dict(self, feature: QgsFeature) -> Optional[Dict[str, Any]]:
        """
        Конвертирует объект QGIS в словарь в формате GeoJSON.

        :param feature: объект QGIS
        :return: словарь в формате GeoJSON или None в случае ошибки
        """
        geometry = feature.geometry()
        if geometry is None or geometry.isEmpty():
            self._log("Пустая или отсутствующая геометрия в объекте.", Qgis.Critical)
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
            self._log(f"Неподдерживаемый тип геометрии: {geom_type_display}", Qgis.Critical)
            return None

        return {
            "geometry": {
                "type": geojson_type,
                "coordinates": coordinates,
            },
            "properties": {
                "name": str(feature["name"]),
                "type": str(feature["type"]),
            },
        }

    def _send_feature_to_api(self, feature: QgsFeature) -> Optional[int]:
        """
        Отправляет объект в API и возвращает полученный ID.

        :param feature: объект QGIS для отправки
        :return: ID объекта из API или None в случае ошибки
        """
        data = self._feature_to_geojson_dict(feature)
        if not data:
            self._log("Не удалось сформировать объект для отправки в API.", Qgis.Critical)
            return None

        try:
            response = requests.post("http://localhost:8000/features", json=data, timeout=5)
            if response.status_code == 201:
                self._log("Объект успешно отправлен в API.")
                return response.json().get("id")
            else:
                self._log(f"Ошибка API: код {response.status_code}, ответ: {response.text}", Qgis.Critical)
        except requests.RequestException as error:
            self._log(f"Ошибка сети при отправке запроса: {error}", Qgis.Critical)
        return None

    def _delete_feature_from_api(self, internal_id_feature: int, layer: QgsVectorLayer) -> None:
        """
        Удаляет объект из API по его ID.

        :param internal_id_feature: внутренний ID объекта в QGIS
        :param layer: слой, содержащий объект
        """
        external_id = None
        layer_name = layer.name()
        if layer_name in self._ids and internal_id_feature in self._ids[layer_name]:
            external_id = self._ids[layer_name].pop(internal_id_feature)

        if external_id is None:
            self._log(f"Не найден внешний ID для внутреннего ID {internal_id_feature} в слое {layer.name()}", Qgis.Critical)
            return

        try:
            response = requests.delete(f"http://localhost:8000/features/{external_id}", timeout=5)
            if response.status_code == 204:
                self._log("Объект успешно удален в API.")
            else:
                self._log(f"Ошибка API: код {response.status_code}, ответ: {response.text}", Qgis.Critical)
        except requests.RequestException as error:
            self._log(f"Ошибка сети при отправке запроса: {error}", Qgis.Warning)
