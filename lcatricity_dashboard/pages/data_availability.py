import logging
import os
from datetime import datetime

import httpx
import july
import pandas as pd
import sqlalchemy
import streamlit as st
from dotenv import load_dotenv
from july.utils import date_range
from matplotlib import pyplot as plt

from lcatricity_dashboard.get_common_data import load_common_data_from_db


def main():
    logging.basicConfig(level=logging.DEBUG)

    if 'sql_engine' not in locals():
        load_dotenv()
        HOST = os.getenv('ELEC_LCA_DB_HOST')
        DB_NAME = os.getenv('ELEC_LCA_DB_NAME')
        USER = os.getenv('ELEC_LCA_DB_LOGIN')
        PASSWORD = os.getenv('ELEC_LCA_DB_PWD')
        PORT = os.getenv('ELEC_LCA_DB_PORT')
        ELEC_LCA_API_URL = os.getenv('ELEC_LCA_API_URL')

        # Connect to postgres database
        sql_engine = sqlalchemy.create_engine(sqlalchemy.engine.url.URL.create(
            drivername='postgresql',
            host=HOST,
            database=DB_NAME,
            username=USER,
            password=PASSWORD,
            port=PORT
        ))


    if 'cache' not in locals():
        cache = load_common_data_from_db(sql_engine=sql_engine)

    st.subheader('Data availability')
    availability_response = httpx.get(f'{ELEC_LCA_API_URL}/available_data_region')
    if availability_response.status_code >= 300 or availability_response.status_code < 200:
        logging.warning(f'Data availability not known successful. Status code: {availability_response.status_code}')
        st.text('Data availability not known')
        return
    data_availability_df = pd.DataFrame.from_dict(availability_response.json())
    data_availability_df['EarliestTimeStamp'] = pd.to_datetime(data_availability_df['EarliestTimeStamp'])
    data_availability_df['LatestTimeStamp'] = pd.to_datetime(data_availability_df['LatestTimeStamp'])
    # st.dataframe(data_availability_df)
    # Show barchart with count of datapoints per region
    st.bar_chart(data_availability_df, x='RegionCode', y='CountDataPoints',x_label="Region")

    earliest_date = data_availability_df['EarliestTimeStamp'].min()
    latest_date = data_availability_df['LatestTimeStamp'].max()
    # st.text(f'Earliest date: {earliest_date}, Latest date: {latest_date}')


if __name__ == '__main__':
    main()
