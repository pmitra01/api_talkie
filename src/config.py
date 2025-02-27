from dataclasses import dataclass
from typing import Optional


@dataclass
class PostgresConfig:
    username: str
    password: str
    host: str
    port: str
    database: str
    table_name: Optional[str] = None
    # todo: find different place to register access tables, instead of bloating the login PostgresConfig


DEFAULT_POSTGRES_CONFIG_LOCAL = PostgresConfig(
     username = 'postgres',
     password = 'postgres',
     host = 'localhost',
     port = '5432',
     database = 'postgres',
     table_name = 'nutrition_data'
 )


# create a user-metadata lookup. User logs in,
