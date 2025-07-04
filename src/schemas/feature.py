from typing import Literal, Union

from pydantic import BaseModel


class Geometry(BaseModel):
    type: Literal["Point", "LineString", "Polygon"]
    coordinates: Union[list[float], list[list[float]], list[list[list[float]]]]


class FeatureProperties(BaseModel):
    name: str
    type: str


class FeatureRequest(BaseModel):
    geometry: Geometry
    properties: FeatureProperties
