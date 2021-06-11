# -*- coding: utf-8 -*-
"""
Created on Mon May 24 10:15:29 2021

@author: wteasley

Determine high and low daily temps from weather station records accessed from
NOAA.  Growing Degree Days (GDD) can be calculated from the data.
 
Note that the formula used here for calculating GDD uses degrees Fahrenheit.

It's a good idea to average between weather stations unless your confident a 
single nearby weather station well-represents your particular location.

A potential problems could arise from inconsistent weather station, specifically if
temperatures aren't consistently taken throughout the day to capture the true
low and high temperature.  Users should inspect their data to ensure its quality.

"""

#%% Import libraries.
import os
import numpy as np
import pandas as pd

from datetime import datetime
from datetime import date

#%% Import data.
def import_frames(file_names):
    
    dateparse = lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S')
    # Will get mixed dtype warning if "low_memory=True" (default).
    frames = [pd.read_csv(name, parse_dates=['DATE'], 
                          date_parser=dateparse, 
                          low_memory=False) for name in file_names]
    
    # Split dataframes with more than one station.
    lst = []
    for i, frame in enumerate(frames):
        if frame['STATION'].nunique() > 1:
            split = frames.pop(i)
            stations = split['STATION'].unique()
            for s in stations:
                lst.append(split[split['STATION'] == s])
    
    # Unpack split dataframes into original list.
    for val in lst:
        frames.append(val)
    
    return frames

#%% Preprocess dataframes.
def preprocess(df):
    
    # Drop blank rows and columns
    df = df.dropna(axis=1, how='all')
    
    # Only want station, date, and dry-bulb temperature data.
    df = df[['STATION', 'DATE', 'HourlyDryBulbTemperature']]
    
    # Rename 'DATE' to 'Datetime' for specificity and temp column for ease of use.
    df = df.rename(columns={'DATE': 'Datetime', 
                                      'HourlyDryBulbTemperature': 'Temp'})
    
    # Give column labels consistent casing.
    df.columns = df.columns.str.title()
    
    # Evaluate datatype of each column and change accordingly.
    # dataset.dtypes
    # Convert station column to type category.
    #dataset["Station"].nunique()
    df["Station"].astype("category")
    # Temperature column is type 'object', indicating alphanumeric values.
    # This is problematic for using numpy functions such as min/max.
    # Use "errors = coerce" to convert problematic alphanumeric values to NaN.
    df['Temp'] = pd.to_numeric(df['Temp'], errors="coerce")
    
    # Create column of dates from datetimes.
    # Series will evaluate as objects if pd.to_datetime not used.
    df['Date'] = pd.to_datetime(df['Datetime'].map(datetime.date))
    
    return df

#%% Generate dataframes with min and max temperatures for each day.
def daily_temp(df, dt):
    '''
    Instead of using interpolation to estimate temperature measurements on 
    missing days, which can be problematic, missing data is imputed using the
    mean from the nearest 20 measurements.
    '''
    # Use a pivot table to generate dataframe with high and low temp for each day.
    # daily_temps = dataset.pivot_table(values='Temp', index='Date', 
    #                                   aggfunc=[min, max])
    # Use multi-index so you can separate data by station later.
    daily_temps = df.pivot_table(values='Temp', index='Date', 
                                  aggfunc=[min, max])
    # Assign names to aggfunc columns.
    daily_temps.columns = ['Min Temp', 'Max Temp']
    
    # Impute and interpolate missing data.
    daily_temps = fill_missing_data(daily_temps)
    
    # Add station column.
    station = df['Station'].iloc[0]
    daily_temps['Station'] = station
    
    # Make function here to create GDD column for each station.
    # Slice dataframe to start at desired date.
    dt = dt.strftime("%Y-%m-%d")
    daily_temps = daily_temps.loc[dt:]
    # Create Growing Degree Days (GDD) column. 
    daily_temps['GDD'] = ((daily_temps['Min Temp'] + daily_temps['Max Temp']) / 2) - 50
    # Replace negative GDD values with 0 as to not influence the cumulative sum.
    daily_temps.loc[daily_temps['GDD'] < 0, 'GDD'] = 0
    # Create column for cumulative GDD.
    daily_temps['GDD_cumulative'] = daily_temps['GDD'].cumsum()
    # Reorder columns.
    daily_temps = daily_temps[['Station', 'Min Temp', 'Max Temp', 'GDD',
                           'GDD_cumulative']]
    
    return daily_temps

#%% Impute and interpolate data for days missing temperature measurements.
def fill_missing_data(df):
    '''
    This function imputes the mean of the nearest 10 measurements. This won't 
    work for the first and last 5 days of the range, so interpolation is used 
    in those instances.
    '''
    
    # Fill in missing dates.
    # Could use df.resample() for this?
    r = pd.date_range(start=df.index.min(), 
                      end=df.index.max())
    df = df.reindex(r).rename_axis('Date')
    # .pad() is the same as foward-fill.
    #daily_temps.reindex(r).pad().rename_axis('Date')
    
    ### Fill missing days of temperature measurements.
    # Check to see which dates were filled (will have NaN for temp):
    # daily_temps[daily_temps['Min Temp'].isnull()]
    # Replace NaN with average of nearest 10 measurements.
    # Shouldn't shorten dataframes to growing season before this point.
    # Only problem is if the first 5 days or last 5 days have NaNs, because -
    # .iloc[] will return NaN for a non-callable value.
    # Added .interpolate() after imputing to make up for this.
    ser = df[df['Min Temp'].isnull()].index
    fill_val = []
    for s in ser:
        idx = df.index.get_loc(s)
        fill_val.append(df.iloc[idx-5:idx+5].mean())
    fill_val = pd.DataFrame(fill_val, index=ser)
    df.fillna(fill_val, inplace=True)
    df[['Min Temp', 'Max Temp']] = df[['Min Temp', 'Max Temp']].interpolate()
    
    return df

#%% Main
def main():
    
    os.chdir(r"H:\2021 Samples and Garden Experiments (back up 20210524)" +
              r"\NOAA Weather Data (2021)\Github (GDD Calculator)")
    # os.chdir(r"D:\2021 Samples and Garden Experiments (back up 20210524)" +
    #           r"\NOAA Weather Data (2021)")
    
    # File name(s) passed to function "import_frames" must be a list.
    file_names = [r"20210524_FrederickCountyMunicipalAirport.csv"]
    #       r"20210524_CarrollCountyRegionalAirport.csv"]
    #file_names = [r"20210604_WeatherData_Frederick_Carroll.csv"]
    
    # User inputs desired start date.  Date should be when soil temperatures
    # reach 50 deg F (see Readme).
    start_date = datetime(2021, 4, 1)
    
    # Date variable for naming output files.
    d = date.today().strftime("%Y%m%d")
    
    # Import data.
    frames = import_frames(file_names)
    
    # Preprocess list of dataframes.
    frames = [preprocess(frame) for frame in frames]
    
    # Convert to dataframes with min/max temp and GDD.
    # All frames should have the same number of days.
    daily_temps = [daily_temp(frame, start_date) for frame in frames]
    
    # Average GDD from all stations if more than one station's data was used.
    df = pd.concat(daily_temps, axis=1)
    df2 = df.loc[:,'GDD_cumulative']
    if type(df2) == pd.DataFrame:
        # Data type of "result" is series.
        result = round(df2.mean(axis=1),0)
        result.to_csv(d + "_GDD.csv")
    # Create csv files for each individual dataframe / station.
    for i, df in enumerate(daily_temps):
        df.to_csv(d + "_GDD_" + str(i) + ".csv")
        
#%%
if __name__ == '__main__':
    main()
