from pydantic import BaseModel, Field
from typing import Literal, List


class Geometry(BaseModel):
    type: Literal["Point"] = Field(description="GeoJSON geometry type")
    coordinates: List[float] = Field(description="Longitude and latitude")


class FeatureProperties(BaseModel):
    name: str
    type: str


class FeatureRequest(BaseModel):
    geometry: Geometry
    properties: FeatureProperties
