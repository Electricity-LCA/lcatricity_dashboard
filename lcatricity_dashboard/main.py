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

from get_common_data import load_common_data_from_db


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

    st.text(f'Connected to : {ELEC_LCA_API_URL}')

    st.title('Electricity LCA Dashboard')


    st.subheader('Data availability')
    availability_response = httpx.get(f'{ELEC_LCA_API_URL}/available_data_region')
    if availability_response.status_code >= 300 or availability_response.status_code < 200:
        logging.warning(f'Data availability not known successful. Status code: {availability_response.status_code}')
        st.text('Data availability not known')
        return
    data_availability_df = pd.DataFrame.from_dict(availability_response.json())
    data_availability_df['EarliestTimeStamp'] = pd.to_datetime(data_availability_df['EarliestTimeStamp'])
    data_availability_df['LatestTimeStamp'] = pd.to_datetime(data_availability_df['LatestTimeStamp'])
    st.dataframe(data_availability_df)
    # Show barchart with count of datapoints per region
    st.bar_chart(data_availability_df, x='RegionCode', y='CountDataPoints',x_label="Region")

    earliest_date = data_availability_df['EarliestTimeStamp'].min()
    latest_date = data_availability_df['LatestTimeStamp'].max()
    st.text(f'Earliest date: {earliest_date}, Latest date: {latest_date}')

    # Show calendar with data points per day
    region_code = st.selectbox(label='Region',options=cache.regions.Code)
    show_calendar_button = st.button('Show calendar')
    if show_calendar_button and region_code:
        calendar_response = httpx.get(f'{ELEC_LCA_API_URL}/datapoints_count_by_day?region_code={region_code}')

        calendar_df = pd.DataFrame.from_dict(calendar_response.json())
        if calendar_df.empty:
            st.text(f'No data for region {region_code}')
        else:
            st.dataframe(calendar_df)

            latest_date = data_availability_df['LatestTimeStamp'].max()
            dates = date_range(earliest_date, latest_date)
            datapoint_counts = list(calendar_df.groupby('Datestamp').agg(sum).iloc[:,0].values)

            ## Create a figure with a single axes
            fig, ax = plt.subplots()

            ## Tell july to make a plot in a specific axes
            july.heatmap(dates, datapoint_counts, ax=ax, colorbar=True)

            st.pyplot(fig)

    st.subheader('See electricity in your region')


    # TODO: Get earliest and latest data for region R, and show a date picker
    st.text(f'Available data for the region {region_code} are listed below')
    if region_code:
        calendar_response_1 = httpx.get(f'{ELEC_LCA_API_URL}/datapoints_count_by_day', params={'region_code': region_code})

        try:
            calendar_df = pd.DataFrame.from_dict(calendar_response_1.json())
            st.dataframe(calendar_df)
            earliest_datestamp = calendar_df["Datestamp"].min()
            earliest_datestamp = datetime.strptime(earliest_datestamp, '%Y-%m-%d')
            latest_datestamp = calendar_df["Datestamp"].max()
            latest_datestamp = datetime.strptime(latest_datestamp, '%Y-%m-%d')
            start_date = st.date_input(label='Start date',min_value=earliest_datestamp,max_value=latest_datestamp)

            if start_date:
                if st.button('Show electricity generation for period'):
                    params = {
                        'date_start': start_date,
                        'region_code': region_code,
                    }
                    st.text(region_code)
                    availability_response = httpx.get(f'{ELEC_LCA_API_URL}/generation', params=params)
                    if availability_response.status_code >= 300 or availability_response.status_code < 200:
                        logging.warning(f'Calculation not successful. Status code: {availability_response.status_code}')
                        st.text('Calculation Error')
                        return

                    generation_json = availability_response.json()

                    impact_df = pd.DataFrame.from_dict(generation_json)
                    if impact_df.empty:
                        st.text('No data available')

                    else:
                        impact_df_w_gen_names = impact_df.merge(cache.generation_types, left_on='GenerationTypeId',
                                                                right_on='Id')
                        del impact_df
                        impact_df_w_gen_names.drop(['Id'], axis=1, inplace=True)
                        impact_df_w_gen_names.rename({'Name': 'ElectricityType'}, axis=1, inplace=True)


                        st.line_chart(impact_df_w_gen_names, x='DateStamp', y='AggregatedGeneration', color='ElectricityType')
                        with st.expander('See data'):
                            st.dataframe(impact_df_w_gen_names)
        except ValueError:
            st.text(f'No data for {region_code}, try a different region code')


    # TODO: Select the impact category of interest by selecting a tab
    impact_category_tabs = st.tabs([x for x in cache.impact_categories['Name']])
    for i, tab in enumerate(impact_category_tabs):
        with tab:
            impact_category_name = cache.impact_categories.loc[i,'Name']
            st.text(impact_category_name)
            calc_params = {
                'date_start': start_date,
                'region_code': region_code,
                'impact_category_id': i+1
            }
            impact_calc_response = httpx.get(f'{ELEC_LCA_API_URL}/calculate', params=calc_params)
            if impact_calc_response.status_code >= 300 or impact_calc_response.status_code < 200:
                st.text(impact_calc_response.text)
                logging.warning(f'Calculation not successful. Status code: {impact_calc_response.status_code}')
                st.text('Calculation Error')
                return

            impact_results_json = impact_calc_response.json()

            impact_results_df = pd.DataFrame.from_dict(impact_results_json)
            st.dataframe(impact_results_df)

            st.text(f'Tab group {i}')

            # Get environmental impact X for all regions





def get_available_dates(region_code):
    raise NotImplementedError()



if __name__ == '__main__':
    main()
