from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.connectors.database_init import BaseORM


class FeaturesORM(BaseORM):
    __tablename__ = "features"

    id: Mapped[int] = mapped_column(primary_key=True)
    feature: Mapped[Geometry] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326)
    )  # SRID 4326 - формат долгота, широта
    properties: Mapped[dict] = mapped_column(JSONB)
