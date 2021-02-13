from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from alembic.script import write_hooks

from lation.core.orm import Base
from lation.core.env import get_env

APP = get_env('APP')

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
# fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = migration.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


# 魔改區開始
# https://stackoverflow.com/questions/35342367/how-can-i-ignore-certain-schemas-with-alembic-autogenerate
def include_object(object, name, type_, reflected, compare_to):
    if type_ == 'table' and object.schema != APP:
        return False
    return True
# 魔改區結束

def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata,
            # 魔改區開始
            # https://gist.github.com/h4/fc9b6d350544ff66491308b535762fee
            version_table_schema=target_metadata.schema,
            include_schemas=True,
            include_object=include_object
            # 魔改區結束
        )

        with context.begin_transaction():
            context.run_migrations()

@write_hooks.register('ignore_foreign_key_constraint')
def ignore_foreign_key_constraint(filename, options):
    lines = []
    with open(filename) as file_:
        for line in file_:
            if 'sa.ForeignKeyConstraint(' not in line:
                lines.append(line)
    with open(filename, 'w') as to_write:
        to_write.write(''.join(lines))

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
