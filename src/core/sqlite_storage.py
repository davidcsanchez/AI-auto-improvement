import asyncio

from sqlalchemy import event, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config.settings import get_settings
from src.interfaces.storage_interface import ITicketStorage
from src.models.golden_sample import GoldenSample
from src.models.prompt_version import PromptVersion
from src.models.ticket_sample import TicketSample


class SQLiteTicketStorage(ITicketStorage):
    def __init__(self) -> None:
        settings = get_settings()
        self._engine = create_async_engine(settings.DATABASE_URL, echo=False)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession)
        self._tables_ready = asyncio.Event()

        self._configure_sqlite()
        self._start_table_creation()

    def _configure_sqlite(self) -> None:
        @event.listens_for(self._engine.sync_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    def _start_table_creation(self) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self._create_tables())
            return

        loop.create_task(self._create_tables())

    async def _create_tables(self) -> None:
        async with self._engine.begin() as connection:
            await connection.run_sync(SQLModel.metadata.create_all)
        self._tables_ready.set()

    async def _get_session(self) -> AsyncSession:
        await self._tables_ready.wait()
        return self._session_factory()

    async def save_prompt(self, prompt: PromptVersion) -> PromptVersion:
        async with await self._get_session() as session:
            session.add(prompt)
            await session.commit()
            await session.refresh(prompt)

            if prompt.is_active:
                await session.exec(
                    update(PromptVersion)
                    .where(PromptVersion.id != prompt.id)
                    .values(is_active=False)
                )
                await session.commit()

            return prompt

    async def get_active_prompt(self) -> PromptVersion | None:
        async with await self._get_session() as session:
            statement = (
                select(PromptVersion)
                .where(PromptVersion.is_active.is_(True))
                .order_by(PromptVersion.version_number.desc())
            )
            result = await session.exec(statement)
            return result.first()

    async def save_sample(self, sample: TicketSample) -> TicketSample:
        async with await self._get_session() as session:
            session.add(sample)
            await session.commit()
            await session.refresh(sample)
            return sample

    async def get_failed_evaluations(self) -> list[TicketSample]:
        async with await self._get_session() as session:
            statement = select(TicketSample).where(
                TicketSample.for_evaluation.is_(True),
                TicketSample.is_correct.is_(False),
            )
            result = await session.exec(statement)
            return list(result.all())

    async def get_golden_samples(self) -> list[GoldenSample]:
        async with await self._get_session() as session:
            result = await session.exec(select(GoldenSample))
            return list(result.all())

    async def save_golden_sample(self, sample: GoldenSample) -> GoldenSample:
        async with await self._get_session() as session:
            session.add(sample)
            await session.commit()
            await session.refresh(sample)
            return sample
