import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import xarray as xr

# Define directories containing the raw and processed files
processed_dir = 'Products_Processed/'
raw_dir = 'Products_Raw/'

# Define time variables
current_date = datetime.now()
one_week_ago = current_date - timedelta(days=7)
two_weeks_ago = current_date - timedelta(days=14)

# Define offl only products
offl_only_products = ['CH4']

# Define the L2 (raw) NetCDF product files
l2_product_files = {
    'HCHO': [raw_dir + filename for filename in os.listdir(raw_dir) if 'L2__HCHO' in filename],
    'NO2': [raw_dir + filename for filename in os.listdir(raw_dir) if 'L2__NO2' in filename],
    'SO2': [raw_dir + filename for filename in os.listdir(raw_dir) if 'L2__SO2' in filename],
    'CH4': [raw_dir + filename for filename in os.listdir(raw_dir) if 'L2__CH4' in filename],
    'CO': [raw_dir + filename for filename in os.listdir(raw_dir) if 'L2__CO' in filename]
}

# Define the L3 (processed) NetCDF product files
l3_product_files = {
    'HCHO': [processed_dir + filename for filename in os.listdir(processed_dir) if 'L3__HCHO' in filename],
    'NO2': [processed_dir + filename for filename in os.listdir(processed_dir) if 'L3__NO2' in filename],
    'SO2': [processed_dir + filename for filename in os.listdir(processed_dir) if 'L3__SO2' in filename],
    'CH4': [processed_dir + filename for filename in os.listdir(processed_dir) if 'L3__CH4' in filename],
    'CO': [processed_dir + filename for filename in os.listdir(processed_dir) if 'L3__CO' in filename]
}

# Save time_coverage_start and time_coverage_end attributes from the L2 files
file_attributes = {
    file.split('/')[-1]: {
        'time_coverage_start': xr.open_dataset(file).attrs['time_coverage_start'],
        'time_coverage_end': xr.open_dataset(file).attrs['time_coverage_end'],
    } for product_files_list in l2_product_files.values() for file in product_files_list
}

# Define attributes for each pollutant (Product: [HARP field name, description, min value, max value, unit])
product_attributes = {
    'HCHO': ['tropospheric_HCHO_column_number_density', 'Tropospheric HCHO column number density', 0, 0.0007, 'mol / m$^{2}$', 'troposphere'],
    'NO2': ['tropospheric_NO2_column_number_density', 'Tropospheric vertical column of NO2', 0, 0.0002, 'mol / m$^{2}$', 'troposphere'],
    'SO2': ['SO2_column_number_density', 'SO2 vertical column density', 0, 0.003, 'mol / m$^{2}$', 'troposphere'],
    'CH4': ['CH4_column_volume_mixing_ratio_dry_air', 'Column averaged dry air mixing ratio of methane', 1400, 2000, 'ppbv', 'atmosphere'],
    'CO': ['CO_column_number_density', 'Vertically integrated CO column density', 0, 0.05, 'mol / m$^{2}$', 'atmosphere']
}

# Create a time coordinate with np datatype datetime64. Important to allow time indexing later
def preprocess(ds):
    ds['time'] = pd.to_datetime(np.array([file_attributes[ds.attrs['source_product']]['time_coverage_start']])).values
    return ds

# Iterate through every product and generate one dataset containing average concentration values
for product, files in l3_product_files.items():
    print(f'Reading {product} files...')
    try:
        L3_1W = xr.open_mfdataset(files, combine='nested', concat_dim='time', preprocess=preprocess, chunks={'time':100})
    except Exception as error:
        print(f'Error: {error}.')
        continue
    L3_1W = L3_1W.sortby('time')
    L3_1W = L3_1W.resample(time='1D').mean(dim='time', skipna=None)
    L3_1W_mean = L3_1W.mean(dim='time')
    attribute = product_attributes[product][0]
    L3_1W_col_mean = L3_1W_mean[attribute]

    if product in offl_only_products:
        start_date = two_weeks_ago
        end_date = one_week_ago
    else:
        start_date = one_week_ago
        end_date = current_date

    # Create a directory (including parent directory if necessary) with the name of the current date
    img_output_dir = f'test/{current_date.strftime("%Y_%m_%d")}'
    os.makedirs(img_output_dir, exist_ok=True)

    # Save output as EPSG:4326 GeoTIFF
    print(f'Plotting {product} concentration to GeoTIFF...')
    L3_1W_col_mean.rio.write_crs("epsg:4326", inplace=True)

    meta_data_dict = {'my_variable': 'my_value'}
    # L3_1W_col_mean.rio.update_tags(**meta_data_dict)

    L3_1W_col_mean.rio.to_raster(f'{img_output_dir}/{product}_{start_date.strftime("%Y_%m_%d")}-{end_date.strftime("%Y_%m_%d")}.tif', tags=meta_data_dict)
    print(f'Done')




