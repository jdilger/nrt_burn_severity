#%%
import os
import geopandas as gpd
from numpy import datetime64
import pandas as pd
from datetime import datetime, timedelta
# adapted from pull_nifc_fires.py, just have to do way less to the mtbs perims data than the nifc fires, 
# keeping all fires, only need to compute start, end, pre_start, and pre_end fields

gdf = gpd.read_file(r'C:\Users\Kyle Woodward\Downloads\mtbs_perimeter_data\mtbs_perims_DD.shp')
#%%
#convert time since epoch to yyyy-mm-dd dateteime string format
#gdf.loc[:'Ig_Date_str'] = pd.to_datetime(gdf.loc[:,'Ig_Date'].apply(lambda d: datetime.fromtimestamp(int(d)/1000).strftime('%Y-%m-%d %H:%M:%S')) )
gdf.loc[:,'Ig_Date'] = pd.to_datetime(gdf.Ig_Date)

####################### OPTION 1 ################################
# pre-img filter = 1 yr prior 3mo window straddling Discovery date
# post-img filter = 1 yr later, 3mo window straddling Discovery date
#   ex: fire Discovery date is 2020-08-17,
#   pre-img window would be 2019-07-17 to 2019-09-17
#   post_img window would be 2021-07-17 to 2021-09-17

gdf.loc[:,'start'] = gdf['Ig_Date'] + timedelta(days= 335)      # 1yr later, 1 mo before
gdf.loc[:,'end'] = gdf['Ig_Date'] + timedelta(days = 395)       # 1yr later, 1 mo after
gdf.loc[:,'pre_start'] = gdf['Ig_Date'] - timedelta(days=395)   # 1yr earlier, 1 mo before
gdf.loc[:,'pre_end'] = gdf['Ig_Date'] - timedelta(days=335)     # 1yr earlier, 1 mo after
gdf.loc[:,'gridmet_start'] = gdf['Ig_Date'] - timedelta(days=14)
gdf.loc[:,'gridmet_end'] = gdf['Ig_Date'] + timedelta(days=14)
# to ensure all fires get same assessment, need to remove fires whose post-fire image composite would 
# require imagery that theoretically wouldn't be available yet. 
# there appears to be a 7-8 day lag from date of collection to Earth Engine ingestion for 
# the default Landsat collection that John's nrt tool uses ('LANDSAT/LC08/C01/T1_TOA')

# So make post fire img composite right bound be 10 days before today's date to be safe
post_end_cut_off = pd.to_datetime(datetime.now()) - timedelta(days=10)
# exclude fire records whose 'end' value is beyond the cutoff
before_cutoff = len(gdf)
gdf = gdf[gdf.end <= post_end_cut_off]
after_cutoff = len(gdf)
print(f'removing {before_cutoff - after_cutoff} fires requiring future non-existent imagery')
# convert datetime to string dtype
gdf.loc[:,['start', 'end', 'pre_start', 'pre_end', 'gridmet_start', 'gridmet_end']] = gdf[['start', 'end', 'pre_start', 'pre_end', 'gridmet_start', 'gridmet_end']].astype('str')

# convert to yyyy-mm-dd format
gdf.loc[:, 'start'] = [x.split(' ')[0] for x in gdf['start']]
gdf.loc[:, 'end'] = [x.split(' ')[0] for x in gdf['end']]
gdf.loc[:, 'pre_start'] = [x.split(' ')[0] for x in gdf['pre_start']]
gdf.loc[:, 'pre_end'] = [x.split(' ')[0] for x in gdf['pre_end']]
gdf.loc[:, 'gridmet_start'] = [x.split(' ')[0] for x in gdf['gridmet_start']]
gdf.loc[:, 'gridmet_end'] = [x.split(' ')[0] for x in gdf['gridmet_end']]
gdf.loc[:,'Ig_Date'] = gdf.Ig_Date.astype(str)
gdf.loc[:,'fire_yr'] = [x.split(' ')[0].split('-')[0] for x in gdf['Ig_Date']]
gdf.loc[:,'fire_yr'] = gdf.fire_yr.astype(int)

#%%
#subset columns
#gdf_finalv1 = gdf[['OBJECTID', 'Name', 'AcresAutoCalc', 'start', 'end', 'pre_start', 'pre_end', 'geometry']]
# write to shp
out_path = r'C:\FireFactor\T2Fuels\data\pyregence-ee\conus\mtbs\raster'
file_name = f'mtbs_perims_date_cleaned.shp'
out_file = f'{os.path.join(out_path,file_name)}'
gdf.to_file(out_file)



# %%
