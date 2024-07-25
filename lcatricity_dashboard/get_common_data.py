import datetime
from dataclasses import dataclass

import pandas as pd
import sqlalchemy


@dataclass
class BasicDataCache:
    """A cache of common data"""
    generation_types: pd.DataFrame
    generation_type_mappings: pd.DataFrame
    regions: pd.DataFrame
    impact_categories: pd.DataFrame
    retrieved_timestamp: datetime.datetime


def load_common_data_from_db(sql_engine) -> BasicDataCache:
    """Load common data from the database and return as a BasicDataCache object"""
    generation_types = pd.read_sql(sqlalchemy.text('SELECT * FROM public."ElectricityGenerationTypes"'), sql_engine)
    generation_type_mappings = pd.read_sql(sqlalchemy.text('SELECT * FROM public."ElectricityGenerationTypesMapping"'),
                                           sql_engine)
    regions = pd.read_sql(sqlalchemy.text('SELECT * FROM public."Regions"'), sql_engine)
    retrieved_timestamp = datetime.datetime.now(datetime.timezone.utc)
    impact_categories = pd.read_sql(sqlalchemy.text('SELECT * FROM public."ImpactCategories"'), sql_engine)
    return BasicDataCache(generation_types=generation_types,
                          regions=regions,
                          generation_type_mappings=generation_type_mappings,
                          impact_categories=impact_categories,
                          retrieved_timestamp=retrieved_timestamp)
