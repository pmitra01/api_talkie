import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from Home import supabase_conn, STREAMLIT_APP_POSTGRESS_HOST, STREAMLIT_APP_POSTGRES_CONFIG
from src.data_utils import process_df_for_analysis, COLUMN_NAMES
from src.config import DEFAULT_POSTGRES_CONFIG_LOCAL_v1, PostgresConfig, DEFAULT_NUTRIENT_BASELINE
from Home import POSTGRES_TABLENAME, POSTGRES_HOST_LOCAL, POSTGRES_HOST_SUPABASE, ALLOWED_POSTGRES_HOSTS


# Initialize session state for both buttons if not already set
if "time_range" not in st.session_state:
    st.session_state.time_range = "1 Week"
if "end_date" not in st.session_state:
    st.session_state.end_date = datetime.datetime.now().date()
if "view_start_date" not in st.session_state:
    st.session_state.view_start_date = st.session_state.end_date - datetime.timedelta(days=7)
if "nutri_data" not in st.session_state:
    st.session_state.nutri_data = pd.DataFrame()


def display_nutrition_trends(postgres_host, postgres_config):
    """Display nutrition trends visualization dashboard"""
    df = read_table_from_postgres(
        host = postgres_host,
        postgres_config = postgres_config
    )
    df = process_df_for_analysis(df)
    return df


def create_date_slider(df):
    """Create and return date filter controls"""
    st.subheader('Meal Nutrition Logs')

    start_date, end_date = st.sidebar.slider(
            'Select custom date range',
            min_value=df[COLUMN_NAMES.DATE].min(),
            max_value=df[COLUMN_NAMES.DATE].max() + datetime.timedelta(days=1),
            value=(df[COLUMN_NAMES.DATE].min(), df[COLUMN_NAMES.DATE].max())
        )
    
    return start_date, end_date
    # end_date = datetime.datetime.now().date()
    # return slice_df_by_date_range(df, st.session_state.view_start_date, st.session_state.end_date)


def date_window_selector(end_date = st.session_state.end_date, time_range = "1 Week"):
    if time_range == "1 Week":
        start_date = end_date - datetime.timedelta(days=7)
    elif time_range == "1 Month":
        start_date = end_date - datetime.timedelta(days=30)
    elif time_range == "3 Months":
        start_date = end_date - datetime.timedelta(days=90)
    elif time_range == "1 Year":
        start_date = end_date - datetime.timedelta(days=365)
    else:  # Custom
        start_date = st.session_state.start_date
    return start_date, end_date

   
def slice_df_by_date_range(df, start_date, end_date):
    return df[(df[COLUMN_NAMES.DATE] >=start_date) & (df[COLUMN_NAMES.DATE] <= end_date)]


def plot_nutrition(df_, selected_nutrients, start_date, end_date):
    """Plot nutrition trends for selected nutrients with fixed date range"""
    # Get baseline values for Female 27-40 from config
    baseline_values = {
        'protein': DEFAULT_NUTRIENT_BASELINE['nutrients'][0]['per_meal']['protein_g'],
        'fat': DEFAULT_NUTRIENT_BASELINE['nutrients'][0]['per_meal']['fat_g'], 
        'carbohydrates': DEFAULT_NUTRIENT_BASELINE['nutrients'][0]['per_meal']['carbohydrates_g'],
        'calories': DEFAULT_NUTRIENT_BASELINE['nutrients'][0]['per_meal']['calories_kcal']
    }

    # df_, start_date, end_date = date_window_selector(df_, time_range)
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create complete date range
    date_range = pd.date_range(start=st.session_state.view_start_date, end=st.session_state.end_date, freq='D').strftime('%Y-%m-%d')
    
    for nutrient in selected_nutrients:
        # Group by date and calculate mean
        df_['date'] = pd.to_datetime(df_['date'])
        filtered_df_ = df_.groupby('date')[nutrient].mean().reset_index()
        # Reindex to include all dates in range, fill missing values with 0
        complete_df = pd.DataFrame({'date': date_range})
        complete_df['date'] = pd.to_datetime(complete_df['date'])
        filtered_df_ = pd.merge(complete_df, filtered_df_, how='left', left_on='date', right_on='date')
        filtered_df_[nutrient] = filtered_df_[nutrient].fillna(0)
        # Plot actual nutrient values
        ax.plot(filtered_df_['date'], filtered_df_[nutrient], marker='o', label=f'Actual {nutrient.capitalize()}')
        
        # Plot baseline as shaded line
        baseline = baseline_values[nutrient]
        ax.axhline(y=baseline, color='gray', alpha=0.3, linestyle='--', 
                  label=f'Target {nutrient.capitalize()} ({baseline})')
        ax.fill_between(filtered_df_['date'], baseline, alpha=0.1, color='gray')
    
    ax.set_xlabel('Date')
    ax.set_ylabel('Amount')
    ax.set_title('Nutrient Intake Over Time')
    ax.grid(True)
    ax.legend()
    
    # Set x-axis limits to selected date range
    ax.set_xlim(st.session_state.view_start_date, st.session_state.end_date)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    return fig


def display_nutrition_plots(filtered_df):
    """Display nutrition plots in a grid layout"""
    nutrients = ['protein', 'fat', 'carbohydrates', 'calories']
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    cols = [col1, col2, col3, col4]

    for col, nutrient in zip(cols, nutrients):
        with col:
            st.pyplot(plot_nutrition(filtered_df, nutrient))


def read_table_from_postgres(
        host: str, #  "local" or "supabase"
        postgres_config: PostgresConfig = STREAMLIT_APP_POSTGRES_CONFIG) -> pd.DataFrame:

    if host == POSTGRES_HOST_LOCAL:
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

def fetch_data_from_supabase(conn = supabase_conn, table_name = POSTGRES_TABLENAME):
    return conn.table(table_name).select("*").execute()

########################
#### app logic ####
########################

st.subheader("View Nutrition Trends")

# Add nutrient selector
available_nutrients = [COLUMN_NAMES.PROTEIN, COLUMN_NAMES.FAT, COLUMN_NAMES.CARBOHYDRATES, COLUMN_NAMES.CALORIES]
selected_nutrients = st.multiselect(
    'Select nutrients to display',
    options=available_nutrients,
    default=[COLUMN_NAMES.PROTEIN, COLUMN_NAMES.CALORIES]
)


st.session_state.nutri_data = display_nutrition_trends(postgres_host=STREAMLIT_APP_POSTGRESS_HOST,
                            postgres_config=STREAMLIT_APP_POSTGRES_CONFIG)


st.session_state.start_date, st.session_state.end_date = create_date_slider(df = st.session_state.nutri_data)
# df = slice_df_by_date_range(st.session_state.nutri_data, st.session_state.start_date, st.session_state.end_date)

time_range = st.sidebar.radio(
    "Select time range",
    ["1 Week", "1 Month", "3 Months", "1 Year", "Custom"],
    index = 0, # Default to 1 Week, 
    key = "time_range"
)

st.session_state.view_start_date, st.session_state.end_date = date_window_selector(end_date=st.session_state.end_date, time_range=time_range)                            
filtered_df = slice_df_by_date_range(st.session_state.nutri_data, start_date = st.session_state.view_start_date, end_date = st.session_state.end_date)

if selected_nutrients:
    st.pyplot(plot_nutrition(filtered_df, selected_nutrients, st.session_state.view_start_date, st.session_state.end_date))
else:
    st.warning("Please select at least one nutrient to display")

# Display the filtered DataFrame
st.write('Filtered DataFrame:', filtered_df)

