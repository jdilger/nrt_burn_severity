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
        description="Pull annual fire perimeter data from MTBS burned area dataset",
        usage="python scripts/pull_mtbs_fires.py -y 2020 -a 500 -o C:\FireFactor\T2Fuels\nrt_burn_severity --cleanup"
    )

    parser.add_argument(
        "-y",
        "--year",
        type=str,
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
    parser.add_argument(
        "--cleanup",
        help="flag used to delete local files after process is complete",
        dest="cleanup",
        action="store_true",
    )
    args = parser.parse_args()

    dir = args.outdir
    year_choice = args.year
    acre_min = args.acres
    cleanup = args.cleanup

    data_dir = os.path.join(dir, 'data')
    download_url = 'https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/MTBS_Fire/data/composite_data/burned_area_extent_shapefile/mtbs_perimeter_data.zip' # path to file
    # gdb_basename = 'fire21_1.gdb'
    # layername = 'firep21_1'
    
    today_string = datetime.utcnow().strftime("%Y-%m-%d").replace("-", "")
    
    logger.info(f"Year Filter: {args.year} | Acreage Minimum: {args.acres}")

    import warnings
    warnings.simplefilter(action='ignore', category=Warning)
    # cheating bc i keep getting this common warning, haven't found what is throwing the warning:
    # C:\ProgramData\Anaconda3\envs\gee\lib\site-packages\pandas\core\indexing.py:1773: SettingWithCopyWarning:
    # A value is trying to be set on a copy of a slice from a DataFrame.
    # Try using .loc[row_indexer,col_indexer] = value instead
    # See the caveats in the documentation: https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
    # self._setitem_single_column(ilocs[0], value, pi)

    # download zipfile if haven't today
    zip_file = os.path.join(data_dir,f'{os.path.basename(download_url)}')
    if not os.path.exists(zip_file):
        logger.info(f"Downloading from {download_url}")
        data = requests.get(download_url)
        with open(zip_file, 'wb')as file:
            file.write(data.content)
  
    gdf = gpd.read_file(zip_file)
    logger.info(f"upon read-in{gdf.shape}")
    gdf = gdf.rename(columns = {
                                'Ig_Date': 'Discovery',
                                } )

    gdf.loc[:,'Discovery'] = gdf.loc[:,'Discovery'].dropna()
    gdf.loc[:,'Discovery'] = pd.to_datetime(gdf.loc[:,'Discovery'], errors='coerce').fillna(value='1970-01-01')
    gdf.loc[:,'Discovery'] = gdf.loc[:,'Discovery'].apply(lambda x: str(x)[0:10])
    logger.info(f"Discovery after fill/drop NAs\n{gdf.shape}")
    logger.info(f"dtypes\n{gdf.dtypes}")
    gdf.loc[:,'Year'] = gdf.loc[:,'Discovery'].apply(lambda x: int(str(x)[0:4]))
    logger.info(f"gdf after Year field: {gdf.shape}")
    gdf.loc[:,'Discovery'] = pd.to_datetime(gdf.loc[:,'Discovery'])
    gdf.loc[:,'Discovery'] = gdf.loc[:,'Discovery'].astype('str')
    logger.info(f"dtypes\n{gdf.dtypes}")
    
    # filter by year
    if not year_choice == None:
        gdf = gdf[gdf.Year == int(year_choice)]
        logger.info(f"gdf after Year Filter\n{gdf.shape}")
    
    # filter by acreage if provided
    if not acre_min == None:
        gdf = gdf[gdf['BurnBndAc'] >= acre_min]
        logger.info(f"gdf after Acreage filter\n{gdf.shape}")

    #subset columns
    gdf_final = gdf[['Event_ID', 'irwinID', 'Incid_Name','Incid_Type','Map_ID', 'Map_Prog', 'Asmnt_Type','BurnBndAc', 'BurnBndLat','BurnBndLon','Discovery','geometry']]

    # write to shp
    logger.info(f"Saving shapefile with {gdf_final.shape[0]} records")
    
    # if year only was given
    if not year_choice == None:
        file_name  = f'mtbs_fires_{year_choice}_{today_string}.shp'
    # if acreage thresh only was given
    elif not acre_min == None:
        file_name  = f'mtbs_fires_gte{str(acre_min)}ac_{today_string}.shp'
    # if both were given
    elif (not year_choice == None) and (not acre_min == None):
        file_name  = f'mtbs_fires_{year_choice}_gte{str(acre_min)}ac_{today_string}.shp'
    # neither were given
    else:
        file_name  = f'mtbs_fires_all_{today_string}.shp'

    
    out_file = f"{os.path.join(data_dir,'shp',file_name)}"
    logger.info(f"writing out to {out_file}")
    gdf_final.to_file(out_file)

    # cleanup
    if cleanup:
        os.remove(zip_file)

if __name__ == "__main__":
    main()