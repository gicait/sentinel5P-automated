# Automated Sentinel-5P Data Pipeline for Pollution Monitoring

<img src="Sample_Output/NO2.gif" alt="Thailand NO2 concentrations" width="500"/>

## Usage

To execute the full processing pipeline, clone the repository, install the necessary dependencies and run [`execute.py`](execute.py). This will execute [`query.py`](query.py), [`process.py`](process.py), and [`multitemporal.py`](multitemporal.py) consecutively. The scripts can also be run manually one at a time. Make sure the scripts are all in the same folder if downloading manually. 

No modification of the scripts should be necessary for the showcased results but can be done to change the output (e.g., study area, pollutants, visualization style)

## Documentation

### [`execute.py`](execute.py)

**Description:**

This script is responsible for the high level automation of the entire workflow. It executes the three scripts [`query.py`](query.py), [`process.py`](process.py), and [`multitemporal.py`](multitemporal.py) consecutively. If any execution errors occur, the exception output is printed.

**Note:**

- The script assumes that the [`query.py`](query.py), [`process.py`](process.py), and [`multitemporal.py`](multitemporal.py) scripts are located in the same directory.

---

### [`query.py`](query.py)

**Description:**

This script is responsible for querying and downloading the Level 2 (L2) Sentinel-5P products from the [Copernicus Open Access Hub](https://scihub.copernicus.eu). It queries Near Real-Time (NRT) and Offline (OFFL) products in a user-defined AOI (defined by a GeoJSON file, parsed as WKT) and time-frame (NRT default: current date - one week ago, OFFL default: one week ago - two weeks ago). For NRT available products such as sulfur dioxide, nitrogen dioxide, carbon monoxide, and formaldehyde, the data may be a mix of NRT and OFFL products. These products are generally available 3 hours after sensing. For OFFL only available products such as methane, the data is available about 5 days after sensing. Due to this a query time-frame more recent than one week ago is not recommended for OFFL products. See the [Sentinel-5P Data Products](https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-5p/data-products) description for more product details.

All products are downloaded as NetCDF files. If it does not already exist, the script creates the directory `Products_Raw/` to store the downloaded data in. If any of the target products are already contained in this directory, they will not be downloaded again. Any products older than the specified time-frame are deleted.

**Third party dependencies:**

- [`sentinelsat`](https://github.com/sentinelsat/sentinelsat)


**Note:**

- By default, this script requires the GeoJSON file [`thailand_boundary_simple.geojson`](thailand_boundary_simple.geojson) to be in the `Support_Files/` directory to define the AOI. To use a different GeoJSON file, specify the file path in line 10.

---

### [`process.py`](process.py)

**Description:**

This script processes the downloaded Level 2 (L2) data products into Level 3 (L3) products using the [HARP](https://github.com/stcorp/harp) library and should be executed after [`query.py`](query.py). The following processing steps are performed:

- Validity filtering: The `/PRODUCT/qa_value` (HARP field name: `[product]_validity`) is used to filter the product by quality. The default value is set to 75.
- Spatial filtering: The data is filtered to the desired spatial extent of the analysis/visualization. Default: Area around Thailand (Lat Lon: 5, 95 – 21, 110).
- Spatial regridding: The data is resampled to a new raster.
- Derivations: The coverage stop time and central coordinates of each cell are derived.
- Attribute filtering: The product attributes to be kept are defined. All other attributes are filtered out. 

After processing, the L3 products are saved as NetCDF files. If it does not already exist, the script creates the directory `Products_Processed/` to store the files in. If any of the L3 target products are already contained in this directory, they will not be generated again. Any products older than the specified time-frame (same time-frames as in [`query.py`](query.py) by default) are deleted.

**Third party dependencies:**

- [`harp`](https://github.com/stcorp/harp)

**Note:**

- It is assumed that L2 products are downloaded and stored in the `Products_Raw/` directory.
- The exception "*Error: product contains no variables, or variables without data.*" occurs when no cells of an entire product are greater than the minimum validity threshold. In this case, processing is skipped and no L3 product is generated. This has been observed as a common occurrence for methane (CH4) products.

---

### [`multitemporal.py`](multitemporal.py)

**Description:**

This script takes care of averaging and visualizing the L3 processed data and should be executed after [`process.py`](process.py). The L3 product attributes, their description, value range and units are defined for the visualization. The value range may be adjusted if inadequate. The script iterates through each product, opening all product files and calculating the mean values for each cell of the attribute to be visualized. The results are plotted and saved as PNG images in the `Output/[Y_m_d]/` directory. The visualization is created using the [`cartopy`](https://github.com/SciTools/cartopy) library and can be modified based on use case/preference. The script also creates a GIF animation of previous outputs for each product in the `Output/` directory. If already present, the GIFs will be overwritten each time the script is run. By default, the eight most recent outputs are included in the GIF.

**Third party dependencies:**

- [`cartopy`](https://github.com/SciTools/cartopy)
- [`dask`](https://github.com/dask/dask)
- [`imageio`](https://github.com/imageio/imageio)
- [`matplotlib`](https://github.com/matplotlib/matplotlib)
- [`matplotlib-scalebar`](https://github.com/ppinard/matplotlib-scalebar)
- [`netcdf4`](https://github.com/Unidata/netcdf4-python)
- [`numpy`](https://github.com/numpy/numpy)
- [`pandas`](https://github.com/pandas-dev/pandas)
- [`xarray`](https://github.com/pydata/xarray)

**Note:**

- It is assumed that L3 products are already processed and stored in the `Products_Processed/` directory.
- It is assumed that L2 products are downloaded and stored in the `Products_Raw/` directory.

