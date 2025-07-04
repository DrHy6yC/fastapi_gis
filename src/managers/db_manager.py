from src.repositories.features import FeatureRepository


class DBManager:
    def __init__(self, session_factories):
        self.session_factories = session_factories

    async def __aenter__(self):
        self.session = self.session_factories()

        self.feature = FeatureRepository(self.session)

        return self

    async def __aexit__(self, *args):
        await self.session.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()

    async def flush(self):
        await self.session.flush()
