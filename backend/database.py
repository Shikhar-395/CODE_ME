import os
from collections.abc import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import load_environment

load_environment()


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

    if not database_url.startswith("postgresql+asyncpg://"):
        return database_url

    parts = urlsplit(database_url)
    query_items = parse_qsl(parts.query, keep_blank_values=True)
    normalized_query: list[tuple[str, str]] = []
    ssl_value = None

    for key, value in query_items:
        if key == "sslmode":
            ssl_value = value
            continue
        if key == "channel_binding":
            continue
        normalized_query.append((key, value))

    if ssl_value and not any(key == "ssl" for key, _ in normalized_query):
        normalized_query.append(("ssl", ssl_value))

    return urlunsplit(parts._replace(query=urlencode(normalized_query)))


DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./leetcode.db"))

engine = create_async_engine(DATABASE_URL)

SessionLocal = async_sessionmaker(
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


# Shared dependency lives here so auth.py and main.py do not import each other.
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as db:
        yield db
