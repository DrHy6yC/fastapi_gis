from typing import Any

import geoalchemy2.shape as ga_shape
from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer
from src.connection.database_init import BaseORM


class GeoJSONFeature(BaseORM):
    type: str
    geometry: dict[str, Any]
    properties: dict[str, Any] = {}


class FeaturesORM(GeoJSONFeature):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True)
    feature = Column(
        Geometry(geometry_type="GEOMETRY", srid=4326)
    )  # SRID 4326 - формат долгота, широта

    def set_geojson(self, geojson: GeoJSONFeature):
        """Конвертирует GeoJSON в объект Geometry"""
        self.feature = ga_shape.from_shape(geojson.geometry, srid=4326)

    def get_geojson(self) -> GeoJSONFeature:
        """Конвертирует Geometry обратно в GeoJSON"""
        shape = ga_shape.to_shape(self.feature)
        return GeoJSONFeature(
            type="Feature", geometry=shape.__geo_interface__, properties={}
        )
