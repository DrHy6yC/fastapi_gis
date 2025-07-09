from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.connectors.database_init import BaseORM


class FeaturesORM(BaseORM):
    __tablename__ = "features"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    geometry: Mapped[Geometry] = mapped_column(
        Geometry(
            geometry_type="GEOMETRY",
            srid=4326,
            from_text="ST_GeomFromEWKT",
            name="geometry",
        ),
        nullable=False,
    )

    properties: Mapped[dict] = mapped_column(JSONB, nullable=False)
