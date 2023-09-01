import os
from datetime import datetime, timedelta

import harp

# Define directory containing the raw files
raw_dir = 'Products_Raw/'

# Define and create (if necessary) directory to save the processed (L3) files to
processed_dir = 'Products_Processed/'
os.makedirs(processed_dir, exist_ok=True)

# Define time variables for filtering
current_date = datetime.now()
one_week_ago = current_date - timedelta(days=7)
two_weeks_ago = current_date - timedelta(days=14)

# Define the L2 (raw) product NetCDF files
l2_product_files = {
    'HCHO': [raw_dir + filename for filename in os.listdir(raw_dir) if 'L2__HCHO' in filename],
    'NO2': [raw_dir + filename for filename in os.listdir(raw_dir) if 'L2__NO2' in filename],
    'SO2': [raw_dir + filename for filename in os.listdir(raw_dir) if 'L2__SO2' in filename],
    'CH4': [raw_dir + filename for filename in os.listdir(raw_dir) if 'L2__CH4' in filename],
    'CO': [raw_dir + filename for filename in os.listdir(raw_dir) if 'L2__CO' in filename]
}

# Define HARP processing steps
harp_op_template = '''
                {validity}>75;
                derive(datetime_stop {{time}});
                latitude > 5 [degree_north] ; latitude < 21 [degree_north] ; longitude > 95 [degree_east] ; longitude < 110 [degree_east];
                bin_spatial(1600, 5, 0.01, 1500, 95, 0.01);
                derive(latitude {{latitude}}); derive(longitude {{longitude}});
                keep({attribute}, latitude, longitude, latitude_bounds, longitude_bounds)
            '''

# Define attributes for each pollutant (Product: [HARP field name, quality descriptor])
product_attributes = {
    'HCHO': ['tropospheric_HCHO_column_number_density', 'tropospheric_HCHO_column_number_density_validity'],
    'NO2': ['tropospheric_NO2_column_number_density', 'tropospheric_NO2_column_number_density_validity'],
    'SO2': ['SO2_column_number_density', 'SO2_column_number_density_validity'],
    'CH4': ['CH4_column_volume_mixing_ratio_dry_air', 'CH4_column_volume_mixing_ratio_dry_air_validity'],
    'CO': ['CO_column_number_density', 'CO_column_number_density_validity']
}

# Process every product file using the HARP processing steps
for product, files in l2_product_files.items():
    print(f'L2 {product} files:\n', files)
    attribute = product_attributes[product][0]
    validity = product_attributes[product][1]
    harp_op = harp_op_template.format(product, attribute=attribute, validity=validity)
    for file in files:
        l3_product_name = os.path.basename(file).replace('L2', 'L3')
        l3_product_path = os.path.join(processed_dir, l3_product_name)
        if os.path.exists(l3_product_path):
            print(f'L3 product already exists for {file}. Skipping processing.')
        else:
            try:
                harp_L2_L3 = harp.import_product(file, operations=harp_op)
                harp.export_product(harp_L2_L3, l3_product_path, file_format='netcdf')
                print(f'{file} successfully converted to L3.')
            except Exception as error:
                print(f'Error: {error}. Skipping processing for {file}.') # "Error: product contains no variables, or variables without data." when no cells of a product are greater than the minimum validity threshold
    print(f'{product} L3 processing complete')

# Define L3 products that have nrt and offl availability
offl_nrt_products = [processed_dir + filename for filename in os.listdir(processed_dir) if not filename.startswith('S5P_OFFL_L3__CH4____')]

# Define L3 products that only have offl availability
offl_only_products = [processed_dir + filename for filename in os.listdir(processed_dir) if filename.startswith('S5P_OFFL_L3__CH4____')]

# Delete L3 products with nrt availability that are over 1 week old
for file in offl_nrt_products:
    filename = os.path.basename(file)
    file_date = datetime.strptime(filename[20:28], '%Y%m%d')
    if file_date < one_week_ago:
        os.remove(file)
        print(f'Deleted: {file}')

# Delete L3 offl only products that are over 2 weeks old
for file in offl_only_products:
    filename = os.path.basename(file)
    file_date = datetime.strptime(filename[20:28], '%Y%m%d')
    if file_date < two_weeks_ago:
        os.remove(file)
        print(f'Deleted: {file}')
