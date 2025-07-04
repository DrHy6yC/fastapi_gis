from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
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
