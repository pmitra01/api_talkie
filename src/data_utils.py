from enum import Enum, auto
from strenum import LowercaseStrEnum
from pydantic import BaseModel
import datetime
import pandas as pd
import uuid


class COLUMN_NAMES(LowercaseStrEnum):
    UUID = auto()
    MEAL_ID = auto()
    DATE = auto()
    TIME = auto()
    MEAL_COMPONENT = auto()
    QUANTITY_PER_SERVING = auto()
    CARBOHYDRATES = auto()
    PROTEIN = auto()
    FAT = auto()
    CALORIES = auto()
    DAILY_MEAL_ID = auto()
    USER_ID = auto()


class MealRecord(BaseModel):
    meal_id: int
    date: datetime.date
    time: str
    meal_component: str
    quantity_per_serving: float
    carbohydrates: float
    protein: float
    fat: float
    calories: float
    daily_meal_id: int


def validate_dataframe(df: pd.DataFrame):
    records = df.to_dict(orient='records')
    validated_records = [MealRecord(**record) for record in records]
    return validated_records
# validated_data = validate_dataframe(df)


def process_df_for_writing_to_sql_db(df:pd.DataFrame):
    df[COLUMN_NAMES.DATE] = pd.to_datetime(df[COLUMN_NAMES.DATE], format="%Y-%m-%d")
    df[COLUMN_NAMES.DATE] = df[COLUMN_NAMES.DATE].dt.date
    NUTRIENT_COLS = [COLUMN_NAMES.PROTEIN, COLUMN_NAMES.FAT, COLUMN_NAMES.CARBOHYDRATES, COLUMN_NAMES.CALORIES]
    df[NUTRIENT_COLS] = df[NUTRIENT_COLS].astype(int)
    df[COLUMN_NAMES.DAILY_MEAL_ID] = df.groupby(COLUMN_NAMES.DATE).cumcount() + 1
    df[COLUMN_NAMES.MEAL_ID] = df.apply(lambda x: mint_meal_id(x), axis=1)
    df[COLUMN_NAMES.UUID] = df.apply(lambda x: generate_uuid(), axis=1)
    df[COLUMN_NAMES.DATE] = df[COLUMN_NAMES.DATE].apply(lambda x: datetime.datetime.strftime(x, "%Y-%m-%d"))

    return df


def process_df_for_analysis(df:pd.DataFrame):
    df[COLUMN_NAMES.DATE] = pd.to_datetime(df[COLUMN_NAMES.DATE], format="%Y-%m-%d")
    df[COLUMN_NAMES.DATE] = df[COLUMN_NAMES.DATE].dt.date
    # df[COLUMN_NAMES.DATE] = df[COLUMN_NAMES.DATE].apply(lambda x: datetime.datetime.strptime(x, "%Y-%m-%d").date)
    NUTRIENT_COLS = [COLUMN_NAMES.PROTEIN, COLUMN_NAMES.FAT, COLUMN_NAMES.CARBOHYDRATES, COLUMN_NAMES.CALORIES]
    df[NUTRIENT_COLS] = df[NUTRIENT_COLS].astype(int)
    return df

def mint_meal_id(row):
    return "_".join([row[COLUMN_NAMES.DATE].strftime("%Y%m%d"), str(row[COLUMN_NAMES.DAILY_MEAL_ID])])


# Function to generate UUID
def generate_uuid():
    return str(uuid.uuid4())

# Create an empty DataFrame
df = pd.DataFrame(columns=['id', 'data'])

