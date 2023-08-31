import os
from datetime import datetime, timedelta
from glob import glob
from os.path import join

import cartopy
import cartopy.crs as ccrs
import cartopy.feature as cf
import imageio.v2 as imageio
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from matplotlib_scalebar.scalebar import ScaleBar
from sklearn.metrics.pairwise import haversine_distances

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
    'HCHO': ['tropospheric_HCHO_column_number_density', 'Tropospheric HCHO column number density', 0, 0.0007, 'mol / m$^{2}$'],
    'NO2': ['tropospheric_NO2_column_number_density', 'Tropospheric vertical column of NO2', 0, 0.0002, 'mol / m$^{2}$'],
    'SO2': ['SO2_column_number_density', 'SO2 vertical column density', 0, 0.003, 'mol / m$^{2}$'],
    'CH4': ['CH4_column_volume_mixing_ratio_dry_air', 'Column averaged dry air mixing ratio of methane', 1400, 2000, 'ppbv'],
    'CO': ['CO_column_number_density', 'Vertically integrated CO column density', 0, 0.05, 'mol / m$^{2}$']
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

    # Plot the results
    print(f'Plotting {product} concentration to PNG...')

    # Define the data to plot
    data = L3_1W_col_mean
    # Set figure size
    fig = plt.figure(figsize=(10, 13))

    # Main map
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax.set_extent([95, 108, 5, 21])
    im = data.plot.pcolormesh(ax=ax, transform=ccrs.PlateCarree(), cmap='magma_r',
                              vmin=product_attributes[product][2], vmax=product_attributes[product][3],
                              x='longitude', y='latitude', zorder=3)
    im.colorbar.remove()    # (colorbar added later)

    # Add scalebar
    A = [100 * np.pi / 180., 14 * np.pi / 180.]  # Latitude of interest ~14 deg, longitude 100
    B = [101 * np.pi / 180., 14 * np.pi / 180.]  # Latitude of interest ~14 deg, longitude 101
    dx = 6371000 * haversine_distances([A, B])[0, 1]
    ax.add_artist(ScaleBar(dx=dx, units='m', length_fraction=0.2, location='lower right', sep=5, pad=0.4, border_pad=1,
                           box_alpha=0.4))

    # Add text
    ax.text(0, 1.07, f'Average {product} concentrations', fontsize=17, transform=ax.transAxes)
    if product in offl_only_products:
        start_date = two_weeks_ago
        end_date = one_week_ago
    else:
        start_date = one_week_ago
        end_date = current_date
    dates_str = f'{start_date.date()} – {end_date.date()}'
    ax.text(0, 1.02, f'Thailand, {dates_str}', fontsize=13, transform=ax.transAxes)
    ax.text(
        0.45, -0.13,
        'Data: ESA Sentinel-5P / TROPOMI\nCredits: Contains Copernicus data (2023) processed by GIC AIT',
        fontsize=10, color='gray', multialignment='right', transform=ax.transAxes
    )

    # Add countries and boundaries
    states_provinces = cf.NaturalEarthFeature(
        category='cultural',
        name='admin_0_countries',
        scale='10m',
        facecolor='#DEDEDE')
    ax.add_feature(states_provinces, edgecolor='black')
    ax.coastlines('10m', zorder=3)
    ax.add_feature(cartopy.feature.BORDERS.with_scale('10m'), zorder=3)

    # Set colorbar properties
    cbar_ax = fig.add_axes([0.15, 0.05, 0.25, 0.01])  # left, bottom, width, height
    cbar = plt.colorbar(im, cax=cbar_ax, orientation='horizontal')
    cbar.locator = plt.MaxNLocator(nbins=4)
    cbar.set_label(fr'{product_attributes[product][1]} ({product_attributes[product][4]})', labelpad=-50, fontsize=11, loc='left')
    cbar.outline.set_visible(False)

    # Set plot frame
    gl = ax.gridlines(draw_labels=True, linewidth=1, color='gray', alpha=0.3, linestyle=':')
    gl.top_labels = False
    gl.right_labels = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER

    # Create a directory (including parent directory if necessary) with the name of the current date
    img_output_dir = f'Output/{current_date.strftime("%Y_%m_%d")}'
    os.makedirs(img_output_dir, exist_ok=True)

    # Save the image in the new directory
    plt.savefig(f'{img_output_dir}/{product}_{start_date.strftime("%Y_%m_%d")}-{end_date.strftime("%Y_%m_%d")}.png', bbox_inches='tight', dpi=600)
    print('Done')

# Create a gif
output_dir = 'Output/'

output_files = {
    'HCHO': [filename for filename in sorted(list(glob(join(output_dir, '**', '*HCHO*.png'), recursive=True)))],
    'NO2': [filename for filename in sorted(list(glob(join(output_dir, '**', '*NO2*.png'), recursive=True)))],
    'SO2': [filename for filename in sorted(list(glob(join(output_dir, '**', '*SO2*.png'), recursive=True)))],
    'CH4': [filename for filename in sorted(list(glob(join(output_dir, '**', '*CH4*.png'), recursive=True)))],
    'CO': [filename for filename in sorted(list(glob(join(output_dir, '**', '*CO*.png'), recursive=True)))]
}

images = {
    'HCHO': [],
    'NO2': [],
    'SO2': [],
    'CH4': [],
    'CO': []
}

for product, files in output_files.items():
    for filename in files:
        images[product].append(imageio.imread(filename))
    imageio.mimsave(f'Output/{product}.gif', images[product], loop=0, duration=1000)
    print(f'{product}.gif generated')
