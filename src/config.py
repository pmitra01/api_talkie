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

FEMALE_27_40_YEARS = "Female (27-40 years)"
MALE_27_40_YEARS = "Male (27-40 years)"
FEMALE_55_65_YEARS = "Female (55-65 years)"
MALE_55_65_YEARS = "Male (55-65 years)"


DEFAULT_NUTRIENT_BASELINE = {
  "nutrients": [
    {
      "group": FEMALE_27_40_YEARS,
      "daily": {
        "calories_kcal": 1800,
        "protein_g": 46,
        "carbohydrates_g": 225,
        "fat_g": 60
      },
      "per_meal": {
        "calories_kcal": 600,
        "protein_g": 15,
        "carbohydrates_g": 75,
        "fat_g": 20
      }
    },
    {
      "group": MALE_27_40_YEARS,
      "daily": {
        "calories_kcal": 2500,
        "protein_g": 56,
        "carbohydrates_g": 325,
        "fat_g": 80
      },
      "per_meal": {
        "calories_kcal": 833,
        "protein_g": 19,
        "carbohydrates_g": 108,
        "fat_g": 27
      }
    },
    {
      "group": FEMALE_55_65_YEARS,
      "daily": {
        "calories_kcal": 1600,
        "protein_g": 46,
        "carbohydrates_g": 200,
        "fat_g": 50
      },
      "per_meal": {
        "calories_kcal": 533,
        "protein_g": 15,
        "carbohydrates_g": 67,
        "fat_g": 17
      }
    },
    {
      "group": MALE_55_65_YEARS,
      "daily": {
        "calories_kcal": 2200,
        "protein_g": 56,
        "carbohydrates_g": 250,
        "fat_g": 60
      },
      "per_meal": {
        "calories_kcal": 733,
        "protein_g": 19,
        "carbohydrates_g": 83,
        "fat_g": 20
      }
    }
  ]
}

# create a user-metadata lookup. User logs in,
