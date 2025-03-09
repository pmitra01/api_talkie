import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import datetime
import pandas as pd
from typing import List, Dict, Optional
from Home import supabase_conn, STREAMLIT_APP_POSTGRESS_HOST, STREAMLIT_APP_POSTGRES_CONFIG
from Home import POSTGRES_TABLENAME, POSTGRES_HOST_LOCAL, POSTGRES_HOST_SUPABASE, ALLOWED_POSTGRES_HOSTS
from src.llm_utils import prompt_llm_for_response
from src.data_utils import process_df_for_writing_to_sql_db
from src.config import DEFAULT_POSTGRES_CONFIG_LOCAL_v1, PostgresConfig

# Initialize connection
#supabase_conn = init_connection()


# TODO: remove repeat parameter entry of table_name. consolidate config into single point of entry
# TODO: fix code to allow cache of supabase query response



# Initialize session state for both buttons if not already set
if "button_clicked_analyze_nutrition" not in st.session_state:
    st.session_state.button_clicked_analyze_nutrition = False
if "button_clicked_add_to_database_button" not in st.session_state:
    st.session_state.button_clicked_add_to_database = False
if 'text_area' not in st.session_state:
    st.session_state.text_area = ""
if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame()



def fetch_data_from_supabase(conn = supabase_conn, table_name = POSTGRES_TABLENAME):
    return conn.table(table_name).select("*").execute()


def insert_data_in_supabase(json_records: List[Dict],
                            table_name = POSTGRES_TABLENAME,
                            conn = supabase_conn):
    try:
        response = (
            conn.table(table_name)
            .insert(json_records)
            .execute()
        )
        return response
    except Exception as exception:
        return exception


def write_to_postgres(df: pd.DataFrame,
                      postgres_host: str,
                      postgres_config: PostgresConfig = STREAMLIT_APP_POSTGRES_CONFIG,
                      conn: Optional[st.connection] = None):

    if postgres_host not in ALLOWED_POSTGRES_HOSTS:
        raise exception(ValueError(f"Postgres host is not recognised. Allowed choices: {ALLOWED_POSTGRES_HOSTS}"))

    if postgres_host == POSTGRES_HOST_LOCAL:
        # Create SQLAlchemy engine
        engine = create_engine(
            f'postgresql+psycopg2://{postgres_config.username}:{postgres_config.password}@{postgres_config.host}:{postgres_config.port}/{postgres_config.database}')

        # Store DataFrame into PostgreSQL
        try:
            df.to_sql(postgres_config.table_name, engine, index=False, if_exists='append')

        except:
            df.to_sql(postgres_config.table_name, engine, index=False, if_exists='replace')

    elif postgres_host == POSTGRES_HOST_SUPABASE:
        json_records = df.to_dict(orient = "records")
        # insert_data_in_supabase(json_records=json_records,
        #                        table_name=postgres_config.table_name,
        #                        conn=conn)
        st.dataframe(df)
        conn.table(postgres_config.table_name).insert(json_records).execute()

    st.write(f"Records written to: Table: {postgres_config.table_name}\n"
             f"Database info: {postgres_config},"
             f"Host: {postgres_host}")


def get_nutrition(user_input_meal_description_string: str,
                  user_input_date: datetime.datetime):
    response = prompt_llm_for_response(user_input_meal_description_string = user_input_meal_description_string,
                                       user_input_date = user_input_date
                                       )
    return response

# Function to clear the text input
def clear_text_area():
    st.session_state.text_area = ""


#### app logic ####

st.title("Log your meal")

# Date input
selected_date = st.sidebar.date_input('Select a date:', value=datetime.datetime.now())
meal_input = st.text_area("Enter your meal description:")
log_df = pd.DataFrame()

# Logic for the first button
if st.button("Analyze Nutrition", key="analyze_nutrition_button"):
    st.session_state.button_clicked_analyze_nutrition = True
    if meal_input:
        nutrition_data_response = get_nutrition(
            user_input_meal_description_string=meal_input,
            user_input_date=selected_date)
        log_df = pd.DataFrame.from_records(nutrition_data_response)
        log_df = process_df_for_writing_to_sql_db(log_df)
        st.write("### Nutrition Information:")
        st.session_state.log_df = st.data_editor(log_df, num_rows = "fixed")

    else:
        st.warning("Please enter a meal description.")

if st.session_state.button_clicked_analyze_nutrition:
    if st.button("Yes, correct. Add to database.", key="add_to_database_button"):
        if not st.session_state.log_df.empty:
            write_to_postgres(st.session_state.log_df,
                            conn=supabase_conn,
                            postgres_host=STREAMLIT_APP_POSTGRESS_HOST,
                            postgres_config=STREAMLIT_APP_POSTGRES_CONFIG)
            st.write("Data added to database.")
        else:
            st.warning("Please analyze a meal first.")


    if st.button("No, incorrect. Reset", key="reset_button"):
        clear_text_area()
        st.write("Reset complete. Enter your meal description again.")