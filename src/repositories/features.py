from geoalchemy2.functions import GeometryType
from sqlalchemy import delete, func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from src.exeptions.error import ObjectNotFoundError
from src.mappers.features import FeatureMapper
from src.models.features import FeaturesORM
from src.schemas.feature import (
    FeatureCollection,
    FeatureRequest,
)


class FeatureRepository:
    mapper = FeatureMapper
    model = FeaturesORM

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, feature_data: FeatureRequest) -> int:
        feature = self.mapper.to_entity(feature_data)
        self.session.add(feature)
        await self.session.flush()
        return feature.id

    async def delete(self, **filter_by) -> None:
        query = select(self.model).filter_by(**filter_by)
        result = await self.session.execute(query)
        try:
            feature_result = result.scalar_one()
        except NoResultFound:
            raise ObjectNotFoundError
        if feature_result:
            delete_model_stmt = delete(self.model).filter_by(**filter_by)
            await self.session.execute(delete_model_stmt)

    async def get_feature_collection(self) -> FeatureCollection:
        query = select(self.model).select_from(self.model)
        features_result = await self.session.execute(query)
        features_list = features_result.scalars().all()
        features_collection = FeatureCollection(
            features=[
                self.mapper.to_feature(feature) for feature in features_list
            ]
        )
        return features_collection

    async def get_feature_count_by_type(self) -> dict[str, int]:
        query = (
            select(
                GeometryType(self.model.geometry).label("type"),
                func.count("*").label("count"),
            )
            .select_from(self.model)
            .group_by(GeometryType(self.model.geometry))
        )
        result_execute = await self.session.execute(query)
        features_stats = result_execute.all()
        stats = dict()
        # Переделал json под пример
        for feature in features_stats:
            if feature.type == "POINT":
                _type = "points"
            elif feature.type == "LINESTRING":
                _type = "lines"
            else:
                _type = "polygons"
            stats[_type] = feature.count
        return stats
