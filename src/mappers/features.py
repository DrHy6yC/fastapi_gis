from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import shape
from src.models.features import FeaturesORM
from src.schemas.feature import (
    FeaturePropertiesID,
    FeatureRequest,
    FeaturesResponse,
)


class FeatureMapper:
    @staticmethod
    def to_entity(schema: FeatureRequest) -> FeaturesORM:
        shapely_geom = shape(
            schema.geometry.model_dump()
        )  # dict -> Shapely Geometry
        geoalchemy_geom = from_shape(shapely_geom, srid=4326)  # -> WKBElement
        return FeaturesORM(
            geometry=geoalchemy_geom, properties=schema.properties.model_dump()
        )

    @staticmethod
    def to_feature(feature) -> FeaturesResponse:
        shapely_geom = to_shape(feature.geometry)
        geojson_geom = shapely_geom.__geo_interface__
        properties_id_dict = {"id": feature.id}
        properties = {**feature.properties, **properties_id_dict}
        return FeaturesResponse(
            geometry=geojson_geom,
            properties=FeaturePropertiesID(**properties),
        )
