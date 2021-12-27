import os
from threading import local
import geopandas as gpd
import pandas as pd
from datetime import datetime
import requests, shutil
import argparse
import logging

logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S %p",
    level=logging.WARNING,
)
logger = logging.getLogger(__name__)

# set verbosity level to INFO if user runs with verbose flag
logger.setLevel(logging.INFO)

def main():
# initalize new cli parser
    parser = argparse.ArgumentParser(
        description="Pull annual fire perimeter data from CALFIRE FRAP."
    )

    parser.add_argument(
        "-y",
        "--year",
        type=int,
        help="year of fires",
    )

    parser.add_argument(
        "-a",
        "--acres",
        type=int,
        help="acreage minimum to filter by",
    )

    parser.add_argument(
        "-o",
        "--outdir",
        type=str,
        help="local repo directory",
    )

    args = parser.parse_args()

    dir = args.outdir
    year_choice = args.year
    acre_min = args.acres
    
    data_dir = os.path.join(dir, 'data')
    download_url = 'https://frap.fire.ca.gov/media/50dgwqrb/fire20_1.zip'
    today_string = datetime.utcnow().strftime("%Y-%m-%d").replace("-", "")
    
    logger.info(f'Year Filter: {args.year} | Acreage Minimum: {args.acres}')

    import warnings
    warnings.simplefilter(action='ignore', category=Warning)
    # cheating bc i keep getting this common warning, haven't found what is throwing the warning:
    # C:\ProgramData\Anaconda3\envs\gee\lib\site-packages\pandas\core\indexing.py:1773: SettingWithCopyWarning:
    # A value is trying to be set on a copy of a slice from a DataFrame.
    # Try using .loc[row_indexer,col_indexer] = value instead
    # See the caveats in the documentation: https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
    # self._setitem_single_column(ilocs[0], value, pi)

    # download zipfile and extract .gdb if haven't today
    zip_file = os.path.join(data_dir,f'calfire_fires_zip_{today_string}.zip')
    if not os.path.exists(zip_file):
        data = requests.get(download_url)
        with open(zip_file, 'wb')as file:
            file.write(data.content)
        shutil.unpack_archive(zip_file, data_dir, "zip")

    gdb = os.path.join(data_dir, 'fire20_1.gdb')
    gdf = gpd.read_file(gdb, layer='firep20_1')

    gdf = gdf.rename(columns = {
                                'YEAR_':'Year',
                                'STATE': 'State',
                                'AGENCY': 'Agency',
                                'UNIT_ID': 'Unit_ID',
                                'FIRE_NAME': 'Fire_Name',
                                'INC_NUM': 'Incident',
                                'ALARM_DATE': 'Discovery',
                                'GIS_ACRES': 'Acres' 
                                } )

    gdf.loc[:,'OBJECTID'] = gdf.index
    gdf.loc[:,'Discovery'] = gdf.loc[:,'Discovery'].dropna()
    gdf.loc[:,'Discovery'] = pd.to_datetime(gdf.loc[:,'Discovery'], errors='coerce').fillna(value='1970-01-01')
    gdf.loc[:,'Discovery'] = gdf.loc[:,'Discovery'].apply(lambda x: str(x)[0:10])
    gdf.loc[:,'Discovery'] = pd.to_datetime(gdf.loc[:,'Discovery'])

    # filter by year choice
    start = pd.to_datetime(f'{year_choice}-01-01')
    end = pd.to_datetime(f'{year_choice}-12-31')
    gdf_yr = gdf[ (gdf.loc[:,'Discovery'] >= start) & (gdf.loc[:,'Discovery'] <= end ) ]
    gdf_yr.loc[:,'Discovery'] = gdf_yr.loc[:,'Discovery'].astype('str')
    
    # filter by acreage if provided
    if not acre_min == None:
        gdf_yr = gdf_yr[gdf_yr['Acres'] >= acre_min]

    #subset columns
    gdf_final = gdf_yr[['OBJECTID', 'Year', 'State', 'Agency', 'Unit_ID', 'Fire_Name', 'Incident','Acres', 'Discovery','geometry']]

    logger.info(f'Saving shapefile with {gdf_final.shape[0]} records')

    # write to shp
    file_name = f'calfire_frap_fires_{year_choice}_{today_string}.shp'
    out_file = os.path.join(data_dir, 'shp', file_name)
    logger.info(f'writing out to {out_file}')
    gdf_final.to_file(out_file)

    # cleanup
    os.remove(zip_file)
    shutil.rmtree(gdb)

if __name__ == "__main__":
    main()