import os

import pandas as pd
import pytest

from greykite.common.constants import TIME_COL
from greykite.common.data_loader import DataLoader
from greykite.common.testing_utils import assert_equal


def test_init():
    dl = DataLoader()
    assert dl.available_datasets == dl.get_data_inventory()


def test_get_data_home():
    dl = DataLoader()
    # Default parameters
    data_home = dl.get_data_home()
    assert os.path.basename(os.path.normpath(data_home)) == "data"

    # With subdirectory
    data_home = dl.get_data_home(data_sub_dir="daily")
    assert os.path.basename(os.path.normpath(data_home)) == "daily"

    # Error due to non existing folder
    data_dir = "/home/data"
    with pytest.raises(ValueError, match=f"Requested data directory '{data_dir}' does not exist."):
        dl.get_data_home(data_dir=data_dir)


def test_get_data_names():
    dl = DataLoader()
    # Returns empty set as there is no .csv file in 'data' folder
    data_path = dl.get_data_home()
    file_names = dl.get_data_names(data_path=data_path)
    assert file_names == []

    data_path = dl.get_data_home(data_sub_dir="daily")
    file_names = dl.get_data_names(data_path=data_path)
    assert set(file_names) == {
        "daily_temperature_australia",
        "daily_demand_order",
        "daily_female_births",
        "daily_istanbul_stock",
        "daily_peyton_manning"}


def test_get_aggregated_data():
    dl = DataLoader()
    test_df = pd.DataFrame({
        TIME_COL: pd.date_range("2020-01-01 00:00", "2020-12-31 23:00", freq="1H"),
        "col1": 1,
        "col2": 2,
        "col3": 3,
        "col4": 4,
        "col5": 5,
    })
    agg_func = {"col1": "sum", "col2": "mean", "col3": "median", "col4": "min", "col5": "max"}
    # For each frequency,
    # (1) make sure the `TIME_COL` column is correctly included
    # (2) verify the aggregation part works correctly
    # Daily aggregation
    df = dl.get_aggregated_data(test_df, agg_freq="daily", agg_func=agg_func)
    assert df.shape == (366, len(agg_func) + 1)
    assert (df["col1"] != 24).sum() == 0
    assert (df["col2"] != 2).sum() == 0
    assert (df["col3"] != 3).sum() == 0
    assert (df["col4"] != 4).sum() == 0
    assert (df["col5"] != 5).sum() == 0
    # Weekly aggregation
    df = dl.get_aggregated_data(test_df, agg_freq="weekly", agg_func=agg_func)
    assert df.shape == (53, len(agg_func) + 1)
    assert (df["col1"] != 24*7).sum() == 2
    assert (df["col2"] != 2).sum() == 0
    assert (df["col3"] != 3).sum() == 0
    assert (df["col4"] != 4).sum() == 0
    assert (df["col5"] != 5).sum() == 0
    # Monthly aggregation
    df = dl.get_aggregated_data(test_df, agg_freq="monthly", agg_func=agg_func)
    assert df.shape == (12, len(agg_func) + 1)
    assert (df["col1"].isin([24*29, 24*30, 24*31])).sum() == 12
    assert (df["col2"] != 2).sum() == 0
    assert (df["col3"] != 3).sum() == 0
    assert (df["col4"] != 4).sum() == 0
    assert (df["col5"] != 5).sum() == 0

    df = test_df.drop(columns=[TIME_COL])
    with pytest.raises(ValueError, match=f"{TIME_COL}"):
        dl.get_aggregated_data(df, agg_freq="monthly", agg_func=agg_func)


def test_get_data_inventory():
    dl = DataLoader()
    file_names = dl.get_data_inventory()
    assert set(file_names) == {
        "online_retail",
        "minute_energy_appliance",
        "minute_household_power",
        "minute_yosemite_temps",
        "hourly_parking",
        "hourly_traffic_volume",
        "hourly_bikesharing",
        "hourly_beijing_pm",
        "daily_temperature_australia",
        "daily_demand_order",
        "daily_female_births",
        "daily_istanbul_stock",
        "daily_peyton_manning",
        "monthly_shampoo",
        "monthly_sunspot"
    }


def test_get_df():
    dl = DataLoader()
    # Daily data
    data_path = dl.get_data_home(data_dir=None, data_sub_dir="daily")
    df = dl.get_df(data_path=data_path, data_name="daily_peyton_manning")
    assert list(df.columns) == [TIME_COL, "y"]
    assert df.shape == (2905, 2)

    # Hourly data
    data_path = dl.get_data_home(data_dir=None, data_sub_dir="hourly")
    df = dl.get_df(data_path=data_path, data_name="hourly_parking")
    assert list(df.columns) == ["SystemCodeNumber", "Capacity", "Occupancy", "LastUpdated"]
    assert df.shape == (35717, 4)

    # Error due to wrong file name
    data_path = dl.get_data_home(data_dir=None, data_sub_dir="daily")
    file_path = os.path.join(data_path, "parking.csv")
    file_names = dl.get_data_names(data_path=data_path)
    with pytest.raises(ValueError, match=fr"Given file path '{file_path}' is not found. Available datasets "
                                         fr"in data directory '{data_path}' are \{file_names}\."):
        dl.get_df(data_path=data_path, data_name="parking")


def test_load_peyton_manning():
    dl = DataLoader()
    df = dl.load_peyton_manning()
    assert list(df.columns) == [TIME_COL, "y"]
    assert df.shape == (2905, 2)


def test_load_hourly_parking():
    dl = DataLoader()
    df = dl.load_parking(system_code_number=None)
    assert list(df.columns) == ["LastUpdated", "Capacity", "Occupancy", "OccupancyRatio"]
    assert df.shape == (1328, 4)

    df = dl.load_parking(system_code_number="NIA South")
    assert list(df.columns) == ["SystemCodeNumber", "Capacity", "Occupancy", "LastUpdated", "OccupancyRatio"]
    assert df.shape == (1204, 5)


def test_load_hourly_bikesharing():
    dl = DataLoader()
    df = dl.load_bikesharing()
    assert list(df.columns) == ["date", TIME_COL, "count", "tmin", "tmax", "pn"]
    assert df.shape == (78421, 6)

    agg_func = {"count": "sum", "tmin": "min", "tmax": "max", "pn": "mean"}
    df = dl.load_bikesharing(agg_freq="daily", agg_func=agg_func)
    assert TIME_COL in df.columns
    assert df.shape == (3269, len(agg_func) + 1)
    df = dl.load_bikesharing(agg_freq="weekly", agg_func=agg_func)
    assert TIME_COL in df.columns
    assert df.shape == (468, len(agg_func) + 1)
    df = dl.load_bikesharing(agg_freq="monthly", agg_func=agg_func)
    assert TIME_COL in df.columns
    assert df.shape == (109, len(agg_func) + 1)


def test_load_hourly_beijing_pm():
    dl = DataLoader()
    df = dl.load_beijing_pm()
    assert list(df.columns) == [
        TIME_COL, "year", "month", "day", "hour", "pm", "dewp",
        "temp", "pres", "cbwd", "iws", "is", "ir"]
    assert df.shape == (43824, 13)

    agg_func = {"pm": "mean", "dewp": "mean", "temp": "max", "pres": "mean", "iws": "sum", "is": "sum", "ir": "sum"}
    df = dl.load_beijing_pm(agg_freq="daily", agg_func=agg_func)
    assert TIME_COL in df.columns
    assert df.shape == (1826, len(agg_func) + 1)
    df = dl.load_beijing_pm(agg_freq="weekly", agg_func=agg_func)
    assert TIME_COL in df.columns
    assert df.shape == (262, len(agg_func) + 1)
    df = dl.load_beijing_pm(agg_freq="monthly", agg_func=agg_func)
    assert TIME_COL in df.columns
    assert df.shape == (60, len(agg_func) + 1)


def test_load_data():
    dl = DataLoader()
    df = dl.load_data(data_name="daily_peyton_manning")
    expected_df = dl.load_peyton_manning()
    assert_equal(df, expected_df)

    df = dl.load_data(data_name="hourly_parking", system_code_number="Shopping")
    expected_df = dl.load_parking(system_code_number="Shopping")
    assert_equal(df, expected_df)

    # Error due to unavailable data name
    data_name = "dummy"
    data_inventory = dl.get_data_inventory()
    with pytest.raises(ValueError, match=fr"Input data name '{data_name}' is not recognized. "
                                         fr"Must be one of \{data_inventory}\."):
        dl.load_data(data_name=data_name)
