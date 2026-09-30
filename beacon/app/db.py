"""Async PostgreSQL persistence for beacon pulses (SQLAlchemy 2.x)."""

from __future__ import annotations

import os

from sqlalchemy import String, Integer, Text, select
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

DATABASE_URL = os.environ.get(
    "BEACON_DATABASE_URL",
    "postgresql+asyncpg://aether:aether@localhost:5432/beacon",
)

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class PulseRow(Base):
    __tablename__ = "pulses"

    round_index: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[str] = mapped_column(String(64))
    entropy: Mapped[str] = mapped_column(Text)
    previous_hash: Mapped[str] = mapped_column(String(64))
    output_hash: Mapped[str] = mapped_column(String(64), index=True)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "round_index": self.round_index,
            "timestamp": self.timestamp,
            "entropy": self.entropy,
            "previous_hash": self.previous_hash,
            "output_hash": self.output_hash,
            "signature": self.signature,
        }


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_latest(session: AsyncSession) -> PulseRow | None:
    res = await session.execute(
        select(PulseRow).order_by(PulseRow.round_index.desc()).limit(1)
    )
    return res.scalar_one_or_none()


async def get_by_index(session: AsyncSession, idx: int) -> PulseRow | None:
    return await session.get(PulseRow, idx)


async def get_range(session: AsyncSession, start: int, end: int) -> list[PulseRow]:
    res = await session.execute(
        select(PulseRow)
        .where(PulseRow.round_index >= start, PulseRow.round_index <= end)
        .order_by(PulseRow.round_index.asc())
    )
    return list(res.scalars().all())


async def insert_pulse(session: AsyncSession, pulse: dict) -> None:
    session.add(PulseRow(**pulse))
    await session.commit()
