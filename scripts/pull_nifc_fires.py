import os
import geopandas as gpd
import pandas as pd
from datetime import datetime, timedelta
from ws_to_gdf import to_gdf, parse_crs_extent
import argparse
import logging
'''

Pulls an annual Subset of NIFC fire perimeters and does data preprocessing to set up for EE NRT Burn Severity tool

Usage Example: python pull_nifc_fires_v2.py -y 2021 -a 500 -o C:\\FireFactor\\T2Fuels\\nrt_burn_severity

Required arguments:
-y Year
-o output Directory (nrt_burn_severty repo root directory so it places shapefiles in nrt_burn_severity/data/shp/)


'''
def main():
# initalize new cli parser
    parser = argparse.ArgumentParser(
        description="Pull annual fire perimeter data from NIFC FeatureService."
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

    data_dir = os.path.join(dir, 'data', 'shp')
    today_string = datetime.utcnow().strftime("%Y-%m-%d").replace("-", "")

    # web service url of NIFC fires
    url = 'https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Fire_History_Perimeters_Public/FeatureServer/0'
    extent, spatialref = parse_crs_extent(url)

    filename_prefix = 'nifc_fires_all'
    out_shp = os.path.join(data_dir,f'{filename_prefix}_{today_string}.shp')

    if not os.path.exists(out_shp):
        print('pulling nifc fires from web service')
        #read in from web service then export to shapefile
        ws_gdf = to_gdf(url)
        ws_gdf = ws_gdf.set_crs(spatialref)
        print(f'writing out to {out_shp}')
        ws_gdf = ws_gdf.to_file(out_shp)
        #read it back in from the shapefile
        print(f'reading nifc fires from {out_shp}')    
        gdf = gpd.read_file(out_shp)

    else:
        print(f'reading nifc fires from {out_shp}')
        gdf = gpd.read_file(out_shp)

    # setup logging 
    # doing it down here bc somethign funky happening with the logger that one of ws_to_gdf module's packages uses
    # it outputs so much info about truncated field names and values that we don't need
    logging.basicConfig(
        format="%(asctime)s %(message)s",
        datefmt="%Y-%m-%d %I:%M:%S %p",
        level=logging.WARNING,
    )
    logger = logging.getLogger(__name__)

    # set verbosity level to INFO if user runs with verbose flag
    logger.setLevel(logging.INFO)

    logger.info(f'Year Filter: {args.year} | Acreage Minimum: {args.acres}')

    # subset columns by index position..
    # had to look these up from the dataset since field names get changed upon read-in
    # OBJECTID 0
    # Incident Name 1
    # GIS Acres 4
    # Acres Auto-calculated 8
    # Fire Discovery Date Time 32
    gdf = gdf.iloc[:,[0,1,4,8,32,105]]

    # in case you want these fields from nifc later they are here:
    # Containment Date Time 14
    # Fire Out Date Time 34
    # Initial Response Date Time 54

    gdf = gdf.rename(columns={'poly_Incid': 'Name', 
                            'poly_GISAc':'GISAcres', 
                            'poly_Acres': 'Acres', 
                            'irwin_Fi_9':'Discovery'})

    # fillna for Discovery date field
    gdf.loc[:,'Discovery'] = gdf.loc[:,'Discovery'].fillna(value=0)
    # note: since i replaced NaN's with 0, those 0's will be converted to a datetime value of '1969-12-31 19:00:00' 
    # b/c datetime is computed as time since epoch since jan 1 1970

    # convert time since epoch to YYYY-mm-dd
    gdf.loc[:,'Discovery'] = pd.to_datetime(gdf.loc[:,'Discovery'].apply(lambda d: datetime.fromtimestamp(int(d)/1000).strftime('%Y-%m-%d')) )

    start = pd.to_datetime(f'{year_choice}-01-01')
    end = pd.to_datetime(f'{year_choice}-12-31')
    gdf_yr = gdf[ (gdf.Discovery >= start) & (gdf.Discovery <= end ) ]
    gdf_yr.loc[:,'Discovery'] = gdf_yr.loc[:,'Discovery'].astype(str)
    
    # filter by acreage if provided
    if not acre_min == None:
        gdf_yr = gdf_yr[gdf_yr.Acres >= acre_min]

    # subset columns for final shapefile
    gdf_final = gdf_yr[['OBJECTID', 'Name', 'Acres', 'Discovery','geometry']]

    if gdf_final.shape[0] == 0:
        raise RuntimeError("Provided filters resulting in 0 records, try another set of filters")
    
    logger.info(f'Saving shapefile with {gdf_final.shape[0]} records')
    # write to shp
    if not acre_min == None:
        file_name  = f'nifc_fires_{year_choice}_gte{acre_min}ac_{today_string}.shp'
    else:
        file_name = f'nifc_fires_{year_choice}_{today_string}.shp'
    out_file = f'{os.path.join(data_dir,file_name)}'
    logger.info(f'writing out to {out_file}')
    gdf_final.to_file(out_file)

if __name__ == "__main__":
    main()