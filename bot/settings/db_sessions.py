from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from .config import conf

import logging

# после создания движка или в начале приложения
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

ENGINE = create_async_engine(url=conf.db_url, echo=False, pool_pre_ping=True)
sessions = sessionmaker(bind=ENGINE, class_=AsyncSession, expire_on_commit=False)
