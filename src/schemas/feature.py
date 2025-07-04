from pydantic import BaseModel, Field
from typing import Literal, List, Union


class Geometry(BaseModel):
    type: Literal["Point", "LineString", "Polygon"]
    coordinates: Union[List[float], List[List[float]], List[List[List[float]]]]


class FeatureProperties(BaseModel):
    name: str
    type: str


class FeatureRequest(BaseModel):
    geometry: Geometry
    properties: FeatureProperties
