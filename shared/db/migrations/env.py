import asyncio
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

from alembic import context

from db.base import METADATA
from settings import conf


config = context.config
config.set_main_option("sqlalchemy.url", conf.db_url)


if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = METADATA

# если буду подключать админку джанго. Исключить её модели
EXCLUDE_PREFIXES = (
    "auth_",
    "django_",
    "idx_tiger_",
    "tiger_",
)
EXCLUDE_EXACT = {
    "django_migrations",
    "django_content_type",
    "django_admin_log",
    "django_session",
    "addr",
    "addrfeat",
    "bg",
    "county",
    "county_lookup",
    "countysub_lookup",
    "cousub",
    "direction_lookup",
    "edges",
    "faces",
    "featnames",
    "geocode_settings",
    "geocode_settings_default",
    "geography_columns",
    "geometry_columns",
    "layer",
    "loader_lookuptables",
    "loader_platform",
    "loader_variables",
    "pagc_gaz",
    "pagc_lex",
    "pagc_rules",
    "place",
    "place_lookup",
    "raster_columns",
    "raster_overviews",
    "secondary_unit_lookup",
    "spatial_ref_sys",
    "state",
    "state_lookup",
    "street_type_lookup",
    "tabblock",
    "tabblock20",
    "topology",
    "tract",
    "zcta5",
    "zip_lookup",
    "zip_lookup_all",
    "zip_lookup_base",
    "zip_state",
    "zip_state_loc",
}


def include_object(obj, name, type_, reflected, compare_to):
    # не трогаем служебную таблицу Alembic
    if type_ == "table" and name == "alembic_version":
        return True

    # игнор префиксов и точных совпадений для таблиц Django
    if type_ == "table":
        if name.startswith(EXCLUDE_PREFIXES) or name in EXCLUDE_EXACT:
            return False

    # для индексов/колонок/внешних ключей смотрим родительскую таблицу
    if type_ in {"index", "column", "foreign_key_constraint"}:
        tbl = getattr(obj, "table", None)
        if tbl is not None:
            tname = tbl.name
            if tname == "alembic_version":
                return True
            if tname.startswith(EXCLUDE_PREFIXES) or tname in EXCLUDE_EXACT:
                return False

    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
