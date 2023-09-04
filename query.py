import os
from datetime import datetime, timedelta

from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt

# Define copernicus open access hub connection
api = SentinelAPI('s5pguest', 's5pguest', 'https://s5phub.copernicus.eu/dhus/')

# Define aoi as wkt
area = geojson_to_wkt(read_geojson('thailand_boundary_simple.geojson'))     # geojson downloaded from: https://cartographyvectors.com/map/1048-thailand-detailed-boundary

# Define time variables for filtering
current_date = datetime.now()
one_week_ago = current_date - timedelta(days=7)
two_weeks_ago = current_date - timedelta(days=14)

# Query nrt available products from api, searching by aoi, time, and query keywords
query_nrt_offl_products = api.query(
    area,
    date=(one_week_ago, current_date),
    platformname='Sentinel-5',
    producttype={'L2__NO2___', 'L2__HCHO__', 'L2__SO2___', 'L2__CO____'}
)

# Query offl only products from api, searching by aoi, time, and query keywords
query_offl_only_products = api.query(
    area,
    date=(two_weeks_ago, one_week_ago),     # CH4 updated “within about 5 days after sensing”
    platformname='Sentinel-5',
    producttype='L2__CH4___'
)

# Define and create (if necessary) directory to download the raw files to
raw_dir = 'Products_Raw/'
os.makedirs(raw_dir, exist_ok=True)

# Download all products from the queries
api.download_all(query_nrt_offl_products, directory_path=raw_dir)
api.download_all(query_offl_only_products, directory_path=raw_dir)

print('Successfully downloaded all product files\nChecking for outdated product files...')

# Define products that only have nrt and offl availability
offl_nrt_products = [raw_dir + filename for filename in os.listdir(raw_dir) if not filename.startswith('S5P_OFFL_L2__CH4____')]

# Define products that only have offl availability
offl_only_products = [raw_dir + filename for filename in os.listdir(raw_dir) if filename.startswith('S5P_OFFL_L2__CH4____')]

# Delete products with nrt availibility that are over 1 week old
for file in offl_nrt_products:
    filename = os.path.basename(file)
    file_date = datetime.strptime(filename[20:28], '%Y%m%d')
    if file_date < one_week_ago:
        os.remove(file)
        print(f'Deleted: {file}')

# Delete offl only products that are over 2 weeks old
for file in offl_only_products:
    filename = os.path.basename(file)
    file_date = datetime.strptime(filename[20:28], '%Y%m%d')
    if file_date < two_weeks_ago:
        os.remove(file)
        print(f'Deleted: {file}')
