import logging
import os
from datetime import datetime, timedelta

import httpx
import pandas as pd
import sqlalchemy
import streamlit as st
from PIL import Image
from dotenv import load_dotenv
# from streamlit_date_picker import date_range_picker, date_picker, PickerType

from get_common_data import load_common_data_from_db


def main():
    global end_date
    banner = Image.open("lcatricity_dashboard/images/lcatricity_logo.jpg")
    page_ico = Image.open("lcatricity_dashboard/images/lcatricity_logo_small.jpg")
    st.set_page_config(page_title="LCAtricty", page_icon=page_ico)

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

    with st.sidebar:
        st.image(banner, width=180)
        st.title('LCAtricity Dashboard')

        st.markdown(f'_Connected to : {ELEC_LCA_API_URL}_', )

    # Show calendar with data points per day
    st.subheader("Choose a region")
    regions_response = httpx.get(f'{ELEC_LCA_API_URL}/list_regions')
    regions_df = pd.DataFrame.from_dict(regions_response.json())
    regions_w_data_list = list(regions_df.loc[
        regions_df['entsoedataavailable'] == True, 'Code'])
    region_code = st.selectbox(label='Region', options=regions_w_data_list)

    if region_code:
        st.subheader('Choose time period')

        calendar_response_1 = httpx.get(f'{ELEC_LCA_API_URL}/datapoints_count_by_day',
                                        params={'region_code': region_code})
        calendar_df = pd.DataFrame.from_dict(calendar_response_1.json())
        if calendar_df.empty:
            st.text(f'No data available for region {region_code}')
        else:
            try:
                # st.text(f'Available data for the region {region_code} are listed below')
                # st.dataframe(calendar_df)
                earliest_datestamp = calendar_df["Datestamp"].min()
                earliest_datestamp = datetime.strptime(earliest_datestamp, '%Y-%m-%d')
                latest_datestamp = calendar_df["Datestamp"].max()
                latest_datestamp = datetime.strptime(latest_datestamp, '%Y-%m-%d')
                start_date = st.date_input(label='Start date', min_value=earliest_datestamp, max_value=latest_datestamp,
                                           format='YYYY-MM-DD')
                if start_date:
                    end_date = st.date_input(label='End date', min_value=start_date,
                                             max_value=latest_datestamp + timedelta(days=1), format='YYYY-MM-DD')
                # date_range_str = date_range_picker(picker_type=PickerType.date,start=earliest_datestamp,end=latest_datestamp)
                if start_date and end_date:
                    # start_date, end_date = date_range_str
                    # start_date = datetime.strptime(start_date,'%Y-%m-%d')
                    # end_date = datetime.strptime(end_date, '%Y-%m-%d')
                    # st.text(start_date)
                    # st.text(end_date)
                    params = {
                        'date_start': start_date.strftime('%Y-%m-%d'),
                        'date_end': end_date.strftime('%Y-%m-%d'),
                        'region_code': region_code,
                    }
                    st.text(region_code)
                    availability_response = httpx.get(f'{ELEC_LCA_API_URL}/generation', params=params)
                    if availability_response.status_code >= 300 or availability_response.status_code < 200:
                        logging.warning(f'Calculation not successful. Status code: {availability_response.status_code}')
                        st.text('Calculation Error')
                        return

                    generation_json = availability_response.json()

                    generation_df = pd.DataFrame.from_dict(generation_json)
                    if generation_df.empty:
                        st.text('No data available')

                    else:
                        generation_df_w_gen_names = generation_df.merge(cache.generation_types,
                                                                        left_on='GenerationTypeId',
                                                                        right_on='Id')
                        del generation_df
                        generation_df_w_gen_names.drop(['Id'], axis=1, inplace=True)
                        generation_df_w_gen_names.rename({'Name': 'ElectricityType'}, axis=1, inplace=True)

                        st.subheader('Electricty Generation')
                        st.area_chart(generation_df_w_gen_names, x='DateStamp', y='AggregatedGeneration',
                                      color='ElectricityType')
                        with st.expander('Show generation data'):
                            st.dataframe(generation_df_w_gen_names)
            except ValueError:
                st.text(f'No data for {region_code}, try a different region code')

        st.subheader('Environmental Impacts')
        st.text(
            'Note that environmental impacts only cover generation of electricity that has known type. Electricity production that is classifier as "Unknown / not specified" in the chart above is ommited from calculation ')
        impact_category_tabs = st.tabs([x for x in cache.impact_categories['Name']])
        for i, tab in enumerate(impact_category_tabs):
            with tab:
                impact_category_name = cache.impact_categories.loc[i, 'Name']
                st.text(impact_category_name)
                calc_params = {
                    'date_start': start_date,
                    'region_code': region_code,
                    'impact_category_id': i + 1
                }
                impact_calc_response = httpx.get(f'{ELEC_LCA_API_URL}/calculate', params=calc_params)
                if impact_calc_response.status_code >= 300 or impact_calc_response.status_code < 200:
                    st.text(impact_calc_response.text)
                    logging.warning(f'Calculation not successful. Status code: {impact_calc_response.status_code}')
                    st.text('Calculation Error')
                    return

                impact_results_json = impact_calc_response.json()

                impact_results_df = pd.DataFrame.from_dict(impact_results_json)

                if impact_results_df.empty:
                    st.text('No data available')

                else:
                    impact_results_df_w_gen_names = impact_results_df.merge(cache.generation_types,
                                                                            left_on='ElectricityGenerationTypeId',
                                                                            right_on='Id')
                    del impact_results_df
                    impact_results_df_w_gen_names.drop(['Id'], axis=1, inplace=True)
                    impact_results_df_w_gen_names.rename({'Name': 'ElectricityType'}, axis=1, inplace=True)
                    impact_unit = impact_results_df_w_gen_names.ImpactCategoryUnit.iloc[0]
                    functional_unit = impact_results_df_w_gen_names.PerUnit.iloc[0]
                    st.text(f"Total impact of {region_code} on {impact_category_name} over {start_date} - {end_date}")
                    st.area_chart(impact_results_df_w_gen_names, x='DateStamp', y=f'EnvironmentalImpact',
                                  color='ElectricityType', x_label='Datestamp',
                                  y_label=f'{impact_category_name[:15]} ({impact_unit})')
                    with st.expander('Show impact data'):
                        st.dataframe(impact_results_df_w_gen_names)


if __name__ == '__main__':
    main()
