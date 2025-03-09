import streamlit as st
import pandas as pd
from typing import Union, List, Dict, Optional
from sqlalchemy import create_engine

from src.llm_utils import prompt_llm_for_response
from src.data_utils import process_df_for_writing_to_sql_db, process_df_for_analysis
from src.config import PostgresConfig, DEFAULT_POSTGRES_CONFIG_LOCAL_v1
from src.data_utils import COLUMN_NAMES
from st_supabase_connection import SupabaseConnection
from supabase import create_client


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

# Check if user is not logged in
if not st.experimental_user.is_logged_in:
    st.write("Please log in to continue")
    if st.button("Log in with Google"):
        st.login("google")
    st.stop()

# Show logout button and handle logout flow if user is logged in
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("Log out"):

        st.logout()
        st.switch_page("Home.py")
        st.markdown("""
            <script>
                window.addEventListener('load', function() {
                    window.location.href = '/';
                })
            </script>
        """, unsafe_allow_html=True)
        st.stop()

with col2:
    st.write(f"Logged in as: {st.experimental_user.email}")


st.markdown(f"Welcome! {st.experimental_user.name}")

st.title("Meal Nutrition Logger")
st.write("Use the sidebar to navigate between logging meals and checking trends.")
