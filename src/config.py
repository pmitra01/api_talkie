from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
import os


load_dotenv()
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
OPEN_AI_KEY = os.environ["OPEN_AI_KEY"]


@dataclass
class PostgresConfig:
    username: str
    password: str
    host: str
    port: str
    database: str
    table_name: Optional[str] = None
    # todo: find different place to register access tables, instead of bloating the login PostgresConfig


DEFAULT_POSTGRES_CONFIG_SUPABASE = PostgresConfig(
     username = 'postgres',
     password = 'postgres',
     host = 'localhost',
     port = '5432',
     database = 'postgres',
     table_name = 'nutrition_data'
 )


DEFAULT_POSTGRES_CONFIG_LOCAL_v1 = PostgresConfig(
     username = 'postgres',
     password = 'postgres',
     host = 'localhost',
     port = '5432',
     database = 'postgres',
     table_name = 'nutrition_data'
 )


# create a user-metadata lookup. User logs in,
