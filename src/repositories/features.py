from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.mappers.features import FeatureMapper
from src.models.features import FeaturesORM
from src.schemas.feature import FeatureRequest


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
