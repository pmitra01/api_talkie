import datetime
from sys import exception

import matplotlib.pyplot as plt

import streamlit as st
import pandas as pd
from typing import Union, List, Dict, Optional
from sqlalchemy import create_engine

from src.llm_utils import prompt_llm_for_response
from src.data_utils import process_df_for_writing_to_sql_db, process_df_for_analysis
from src.config import PostgresConfig, DEFAULT_POSTGRES_CONFIG_LOCAL_v1
from src.data_utils import COLUMN_NAMES
from st_supabase_connection import SupabaseConnection

import streamlit as st
from supabase import create_client, Client

POSTGRES_TABLENAME = "nutrition_data"
POSTGRES_HOST_LOCAL = "local"
POSTGRES_HOST_SUPABASE = "supabase"
ALLOWED_POSTGRES_HOSTS = [POSTGRES_HOST_SUPABASE, POSTGRES_HOST_LOCAL]


## app level config
STREAMLIT_APP_POSTGRESS_HOST = POSTGRES_HOST_SUPABASE
STREAMLIT_APP_POSTGRES_CONFIG = DEFAULT_POSTGRES_CONFIG_LOCAL_v1

# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase_conn = init_connection()
# supabase_conn = st.connection("supabase", type=SupabaseConnection)


if not st.experimental_user.is_logged_in:
    if st.button("Log in with Google"):
        st.login()
    st.stop()

if st.button("Log out"):
    st.logout()
st.markdown(f"Welcome! {st.experimental_user.name}")

# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
#@st.cache_data(ttl=600)
# TODO: remove repeat parameter entry of table_name. consolidate config into single point of entry
# TODO: fix code to allow cache of supabase query response
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


def get_nutrition(user_input_meal_description_string: str,
                  user_input_date: datetime.datetime):
    response = prompt_llm_for_response(user_input_meal_description_string = user_input_meal_description_string,
                                       user_input_date = user_input_date
                                       )
    return response


def plot_nutrition(df_, nutrient):
    filtered_df_ = df_.groupby('date')[nutrient].mean().reset_index()
    # st.dataframe(filtered_df_)
    fig, ax = plt.subplots()
    ax.plot(filtered_df_['date'], filtered_df_[nutrient], marker='o')
    ax.set_xlabel('Date')
    ax.set_ylabel(nutrient.capitalize())
    ax.set_title(f'{nutrient.capitalize()} Intake Over Time')
    ax.grid(True)
    return fig


def read_table_from_postgres(
        host: str, #  "local" or "supabase"
        postgres_config: PostgresConfig = STREAMLIT_APP_POSTGRES_CONFIG) -> pd.DataFrame:

    if host == POSTGRES_HOST_LOCAL:
        # Create SQLAlchemy engine
        engine = create_engine(
            f'postgresql+psycopg2://{postgres_config.username}:{postgres_config.password}@{postgres_config.host}:{postgres_config.port}/{postgres_config.database}')

        # SQL query to read data from the PostgreSQL table
        query = f'SELECT * FROM {postgres_config.table_name}'

        # Read data into a DataFrame
        df_ = pd.read_sql(query, engine)

    elif host == POSTGRES_HOST_SUPABASE:
        response = fetch_data_from_supabase()
        df_ = pd.DataFrame(response.data)

    # todo: add user-filtering, and authentication
    return df_


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
        conn.table(postgres_config.table_name).insert(json_records).execute()

    st.write(f"Records written to: Table: {postgres_config.table_name}\n"
             f"Database info: {postgres_config},"
             f"Host: {postgres_host}")

# Function to clear the text input
def clear_text_area():
    st.session_state.text_area = ""


# Function to handle radio button selection
def handle_radio_selection():
    st.session_state.user_approval_response = st.radio(
        "Does this look correct?",
        options=("Yes", "No"),
        captions = ["Yes, add to database", "No, reset"],
        index=None,
        horizontal=True,
    )

##############################################################################
########################## Streamlit App ##########################
##############################################################################

# Initialize session state for text input
if 'text_area' not in st.session_state:
    st.session_state.text_area = ""


st.title("Meal Nutrition Logger")
tab1, tab2 = st.tabs(["Log your meal", "Check your trends", ])

# Date input
selected_date = st.sidebar.date_input('Select a date:', value=datetime.datetime.now())

with tab1:

    meal_input = st.text_area("Enter your meal description:")

    if st.button("Analyze Nutrition"):
        if meal_input:
            nutrition_data_response = get_nutrition(
                user_input_meal_description_string= meal_input,
                user_input_date = selected_date)
            # if nutrition_data_response:
            log_df = pd.DataFrame.from_records(nutrition_data_response)
            log_df = process_df_for_writing_to_sql_db(log_df)
            st.write("### Nutrition Information:")
            st.dataframe(log_df)
        else:
            st.warning("Please enter a meal description.")

        if st.button("Yes, correct. Add to database."):
            write_to_postgres(log_df,
                                conn=supabase_conn,
                                postgres_host=STREAMLIT_APP_POSTGRESS_HOST,
                                postgres_config=STREAMLIT_APP_POSTGRES_CONFIG)
            st.write("Data added to database.")

        if st.button("No, incorrect. Reset"):
            clear_text_area()
            st.write("Reset complete. Enter your meal description again.")


with tab2:
    # Plotting function
    st.subheader("View Nutrition Trends")

    def display_nutrition_trends(config):
        """Display nutrition trends visualization dashboard"""
        df = read_table_from_postgres(
            host=config.postgres_host,
            postgres_config=config.postgres_config
        )
        df = process_df_for_analysis(df)
        return df

    def create_date_filter(df):
        """Create and return date filter controls"""
        st.subheader('Meal Nutrition Logs')
        start_date, end_date = st.slider(
            'Select date range',
            min_value=df[COLUMN_NAMES.DATE].min(),
            max_value=df[COLUMN_NAMES.DATE].max() + datetime.timedelta(days=1),
            value=(df[COLUMN_NAMES.DATE].min(), df[COLUMN_NAMES.DATE].max())
        )
        return df[(df[COLUMN_NAMES.DATE] >= start_date) & (df[COLUMN_NAMES.DATE] <= end_date)]

    def display_nutrition_plots(filtered_df):
        """Display nutrition plots in a grid layout"""
        nutrients = ['protein', 'fat', 'carbohydrates', 'calories']
        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        cols = [col1, col2, col3, col4]

        for col, nutrient in zip(cols, nutrients):
            with col:
                st.pyplot(plot_nutrition(filtered_df, nutrient))

    if st.button("View trends"):
        config = {
            'postgres_host': STREAMLIT_APP_POSTGRESS_HOST,
            'postgres_config': STREAMLIT_APP_POSTGRES_CONFIG
        }
        config = type('Config', (), config)  # Convert dict to object

        df = display_nutrition_trends(config)
        filtered_df = create_date_filter(df)
        display_nutrition_plots(filtered_df)
        
        # Display the filtered DataFrame
        st.write('Filtered DataFrame:', filtered_df)
