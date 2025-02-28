import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

from src.llm_utils import prompt_llm_for_response
from src.data_utils import postprocess_df
from src.config import PostgresConfig, DEFAULT_POSTGRES_CONFIG_LOCAL

POSTGRES_TABLENAME = 'nutrition_data'


def get_nutrition(meal_description_string: str):
    response = prompt_llm_for_response(user_input_string=meal_description_string)
    return response


def write_to_postgres(df: pd.DataFrame,
                      postgres_config: PostgresConfig = DEFAULT_POSTGRES_CONFIG_LOCAL):

    # Create SQLAlchemy engine
    engine = create_engine(
        f'postgresql+psycopg2://{postgres_config.username}:{postgres_config.password}@{postgres_config.host}:{postgres_config.port}/{postgres_config.database}')

    # Store DataFrame into PostgreSQL
    try:
        df.to_sql(postgres_config.table_name, engine, index=False, if_exists='append')
    except:
        df.to_sql(postgres_config.table_name, engine, index=False, if_exists='replace')


st.title("Meal Nutrition Logger")
meal_input = st.text_area("Enter your meal description:")

if st.button("Analyze Nutrition"):
    if meal_input:
        nutrition_data_response = get_nutrition(meal_input)
        if nutrition_data_response:
            df = pd.DataFrame.from_records(nutrition_data_response)
            df = postprocess_df(df)
            st.write("### Nutrition Information:")
            st.dataframe(df)
            df.to_csv("data/nutrition_data.csv", index=False)

            write_to_postgres(df, postgres_config=DEFAULT_POSTGRES_CONFIG_LOCAL)

        else:
            st.error("Error retrieving nutrition data using LLM. Try again.")
    else:
        st.warning("Please enter a meal description.")


# Compare this snippet from src/llm_utils
