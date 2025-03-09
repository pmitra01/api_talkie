from enum import Enum, auto
from strenum import LowercaseStrEnum
from pydantic import BaseModel, Field, validator
import datetime
import pandas as pd
import uuid
import logging
from pydantic import ValidationError
from typing import Tuple, Optional
from datetime import date


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
    uuid: str
    meal_id: str
    date: date
    time: str
    meal_component: str
    quantity_per_serving: float
    carbohydrates: float
    protein: float 
    fat: float
    calories: float
    daily_meal_id: int
    user_id: Optional[str] = None

"""
    @validator('uuid')
    def validate_uuid_format(cls, v):
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')

    class Config:
        extra = "forbid"  # Prevents additional fields


def validate_dataframe(df: pd.DataFrame):
    records = df.to_dict(orient='records')
    validated_records = [MealRecord(**record) for record in records]
    return validated_records
"""

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

"""
def clean_and_validate_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, list[dict]]:
    \"""
    Attempts to clean and correct common validation errors in the DataFrame.
    
    Args:
        df: DataFrame containing meal records
    
    Returns:
        Tuple containing:
        - Cleaned DataFrame
        - List of validation errors that couldn't be automatically fixed
    \"""
    df = df.copy()  # Create a copy to avoid modifying original
    unfixable_errors = []

    # Clean numeric columns
    numeric_cols = [
        COLUMN_NAMES.QUANTITY_PER_SERVING,
        COLUMN_NAMES.CARBOHYDRATES,
        COLUMN_NAMES.PROTEIN,
        COLUMN_NAMES.FAT,
        COLUMN_NAMES.CALORIES
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            # Replace negative values with 0
            df[col] = df[col].apply(lambda x: max(0, float(x)) if pd.notnull(x) else 0)
            # Replace non-numeric values with 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Clean time format
    if COLUMN_NAMES.TIME in df.columns:
        def fix_time_format(time_str):
            try:
                # Try to parse various time formats
                if pd.isna(time_str):
                    return "00:00"
                if isinstance(time_str, (int, float)):
                    time_str = str(int(time_str)).zfill(4)
                    return f"{time_str[:2]}:{time_str[2:]}"
                if ':' not in str(time_str):
                    time_str = str(time_str).zfill(4)
                    return f"{time_str[:2]}:{time_str[2:]}"
                # Parse HH:MM format
                datetime.strptime(time_str, "%H:%M")
                return time_str
            except (ValueError, TypeError):
                return "00:00"  # Default time if parsing fails
        
        df[COLUMN_NAMES.TIME] = df[COLUMN_NAMES.TIME].apply(fix_time_format)

    # Clean date format
    if COLUMN_NAMES.DATE in df.columns:
        df[COLUMN_NAMES.DATE] = pd.to_datetime(df[COLUMN_NAMES.DATE], errors='coerce').dt.date
        # Fill missing dates with today
        df[COLUMN_NAMES.DATE] = df[COLUMN_NAMES.DATE].fillna(datetime.today().date())

    # Ensure meal_component is string and not empty
    if COLUMN_NAMES.MEAL_COMPONENT in df.columns:
        df[COLUMN_NAMES.MEAL_COMPONENT] = df[COLUMN_NAMES.MEAL_COMPONENT].fillna("Unknown")
        df[COLUMN_NAMES.MEAL_COMPONENT] = df[COLUMN_NAMES.MEAL_COMPONENT].astype(str)

    # Generate missing UUIDs
    if COLUMN_NAMES.UUID in df.columns:
        df[COLUMN_NAMES.UUID] = df[COLUMN_NAMES.UUID].apply(
            lambda x: x if isinstance(x, str) and len(x) > 0 else generate_uuid()
        )

    # Validate each record and collect unfixable errors
    for index, row in df.iterrows():
        try:
            MealRecord(**row.to_dict())
        except ValidationError as e:
            error_info = {
                'row_index': index,
                'data': row.to_dict(),
                'errors': e.errors()
            }
            unfixable_errors.append(error_info)
            logging.warning(f"Validation error at row {index}: {e}")

    return df, unfixable_errors
"""
"""

def handle_validation_errors(df: pd.DataFrame) -> pd.DataFrame:
    \"""
    Wrapper function to clean data and handle validation errors.
    
    Args:
        df: Input DataFrame
    
    Returns:
        Cleaned DataFrame with valid records only
    
    Example:
        >>> df = handle_validation_errors(my_dataframe)
        >>> if df is not None:
        >>>     # Process valid data
    \"""
    cleaned_df, errors = clean_and_validate_dataframe(df)
    
    if errors:
        logging.warning(f"Found {len(errors)} records with validation errors")
        # Remove rows with validation errors
        error_indices = [e['row_index'] for e in errors]
        cleaned_df = cleaned_df.drop(error_indices)
        
        # Log detailed error information
        for error in errors:
            logging.error(f"Row {error['row_index']} failed validation:")
            for err in error['errors']:
                logging.error(f"  - {err['loc']}: {err['msg']}")
    
    return cleaned_df

 Example usage
try:
    # Load your DataFrame
    df = pd.read_csv('meal_data.csv')
    
    # Clean and validate the data
    cleaned_df = handle_validation_errors(df)
    
    if not cleaned_df.empty:
        # Process the valid records
        validated_records = validate_dataframe(cleaned_df)
        print(f"Successfully processed {len(validated_records)} valid records")
    else:
        print("No valid records found after cleaning")
        
except Exception as e:
    logging.error(f"Error processing data: {str(e)}")
"""