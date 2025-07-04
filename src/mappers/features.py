from geoalchemy2.shape import from_shape
from shapely.geometry import shape
from src.models.features import FeaturesORM
from src.schemas.feature import FeatureRequest


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
