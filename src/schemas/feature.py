from typing import Any, Literal, Union

from pydantic import BaseModel


class Geometry(BaseModel):
    type: Literal["Point", "LineString", "Polygon"]
    coordinates: Union[list[float], list[list[float]], list[list[list[float]]]]


class FeatureProperties(BaseModel):
    name: str
    type: str


class FeaturePropertiesID(FeatureProperties):
    id: int


class FeatureRequest(BaseModel):
    geometry: Geometry
    properties: FeatureProperties


class FeaturesResponse(BaseModel):
    type: str = "Feature"
    geometry: dict[str, Any]
    properties: FeaturePropertiesID


class FeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[FeaturesResponse]
