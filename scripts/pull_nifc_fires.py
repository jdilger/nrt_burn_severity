#%%
import os
import geopandas as gpd
import pandas as pd
from datetime import datetime, timedelta
from ws_to_gdf import to_gdf, parse_crs_extent


# if were to make this script a callable function - arguments for function
year_choice = str(2020)
acre_min = 500

# web service url of NIFC fires
url = 'https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Fire_History_Perimeters_Public/FeatureServer/0'

extent, spatialref = parse_crs_extent(url)

today_string = str(datetime.now()).split(' ')[0].replace('-', '_')
out_path = r'C:\FireFactor\T2Fuels\nrt_burn_severity\data\shp'
file_prefix = 'nifc_fires_all'
out_shp = f'{out_path}\{file_prefix}_{today_string}.shp'

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

# dsubset columns by index position..

# OBJECTID 0
# Incident Name 1
# GIS Acres 4
# Acres Auto-calculated 8
# Containment Date Time 14
# Fire Discovery Date Time 32
# Fire Out Date Time 34
# Initial Response Date Time 54
gdf = gdf.iloc[:,[0,1,4,8,14,32,34,54,105]]


gdf.iloc[:,[4,5,6,7]] = gdf.iloc[:,[4,5,6,7]].fillna(value=0)
# note: since i replaced NaN's with 0, those 0's will be converted to a datetime value of '1969-12-31 19:00:00' b/c datetime is computed as time since epoch since jan 1 1970

#couldn't figure out how to do this in one line
gdf.iloc[:,4] = pd.to_datetime(gdf.iloc[:,4].apply(lambda d: datetime.fromtimestamp(int(d)/1000).strftime('%Y-%m-%d %H:%M:%S')) )
gdf.iloc[:,5] = pd.to_datetime(gdf.iloc[:,5].apply(lambda d: datetime.fromtimestamp(int(d)/1000).strftime('%Y-%m-%d %H:%M:%S')) )
gdf.iloc[:,6] = pd.to_datetime(gdf.iloc[:,6].apply(lambda d: datetime.fromtimestamp(int(d)/1000).strftime('%Y-%m-%d %H:%M:%S')) )
gdf.iloc[:,7] = pd.to_datetime(gdf.iloc[:,7].apply(lambda d: datetime.fromtimestamp(int(d)/1000).strftime('%Y-%m-%d %H:%M:%S')) )

gdf = gdf.rename(columns={'poly_Incid': 'Name', 
                        'poly_GISAc':'GISAcres', 
                        'poly_Acres': 'AcresAutoCalc', 
                        'irwin_Cont':'Containment', 
                        'irwin_Fi_9':'Discovery',
                        'irwin_Fi11':'Out',
                        'irwin_In_7':'Response'})



start = pd.to_datetime(f'{year_choice}-01-01')
end = pd.to_datetime(f'{year_choice}-12-31')
gdf_yr = gdf[( ( (gdf.Discovery >= start) & (gdf.Discovery <= end ) )| ( (gdf.Response >= start) & (gdf.Response <= end) ) & \
                ( (gdf.Containment >= start) & (gdf.Containment <= end) ) | ( (gdf.Out >= start) & (gdf.Out <= end) ) ) ]
gdf_yr = gdf_yr[gdf_yr.AcresAutoCalc >= acre_min]

# need to create 4 new fields: start, end, pre_start, pre_end to match the pre-before, pre-after, post-before, post-after time constraints for filtering image collections in John's functions
# (start and end refer to post-fire start and end)

#make two copies
gdf_yrv1 = gdf_yr.copy(deep=True)
gdf_yrv2 = gdf_yr.copy(deep=True) 
gdf_yrv3 = gdf_yr.copy(deep=True)
#%%
####################### OPTION 1 ################################
# pre-img filter = 1 yr prior 3mo window straddling Discovery date
# post-img filter = 1 yr later, 3mo window straddling Discovery date
#   ex: fire Discovery date is 2020-08-17,
#   pre-img window would be 2019-07-17 to 2019-09-17
#   post_img window would be 2021-07-17 to 2021-09-17

gdf_yrv1.loc[:,'start'] = gdf_yrv1['Discovery'] + timedelta(days= 335)      # 1yr later, 30 days before
gdf_yrv1.loc[:,'end'] = gdf_yrv1['Discovery'] + timedelta(days = 395)       # 1yr later, 30 days after
gdf_yrv1.loc[:,'pre_start'] = gdf_yrv1['Discovery'] - timedelta(days=395)   # 1yr earlier, 30 days before
gdf_yrv1.loc[:,'pre_end'] = gdf_yrv1['Discovery'] - timedelta(days=335)     # 1yr earlier, 30 days after

# to ensure all fires get same assessment, need to remove fires whose post-fire image composite would 
# require imagery that theoretically wouldn't be available yet. 
# there appears to be a 7-8 day lag from date of collection to Earth Engine ingestion for 
# the default Landsat collection that John's nrt tool uses ('LANDSAT/LC08/C01/T1_TOA')

# So make post fire img composite right bound be certain # days before today's date to be safe
post_end_cut_off = pd.to_datetime(datetime.now()) - timedelta(days=5)
# exclude fire records whose 'end' value is beyond the cutoff
before_cutoff = len(gdf_yrv1)
gdf_yrv1 = gdf_yrv1[gdf_yrv1.end <= post_end_cut_off]
after_cutoff = len(gdf_yrv1)
print(f'removing {before_cutoff - after_cutoff} fires requiring future non-existent imagery')
# convert datetime to string dtype
gdf_yrv1.loc[:,['Discovery','start', 'end', 'pre_start', 'pre_end']] = gdf_yrv1[['Discovery','start', 'end', 'pre_start', 'pre_end']].astype('str')
# convert to yyyy-mm-dd format
gdf_yrv1.loc[:, 'start'] = [x.split(' ')[0] for x in gdf_yrv1['start']]
gdf_yrv1.loc[:, 'end'] = [x.split(' ')[0] for x in gdf_yrv1['end']]
gdf_yrv1.loc[:, 'pre_start'] = [x.split(' ')[0] for x in gdf_yrv1['pre_start']]
gdf_yrv1.loc[:, 'pre_end'] = [x.split(' ')[0] for x in gdf_yrv1['pre_end']]
gdf_yrv1.loc[:, 'Discovery'] = [x.split(' ')[0] for x in gdf_yrv1['Discovery']]

#subset columns
gdf_finalv1 = gdf_yrv1[['OBJECTID', 'Name', 'AcresAutoCalc', 'Discovery','start', 'end', 'pre_start', 'pre_end', 'geometry']]
# write to shp
file_name = f'nifc_fires_{year_choice}_gte500acres_v1.shp'
out_file = f'{os.path.join(out_path,file_name)}'
print(f'writing out to {out_file}')
#gdf_finalv1.to_file(out_file)
# %%
####################### OPTION 2 ################################
# copying Miller (2007) as much as possible, pre-fire img is as close to the fire alarm date on that same year
#   and post-fire img is as close to 1yr anniversary of that fire's alarm date

# pre-img filter = 3mo window leading up to Discovery date 
# post-img filter = 3mo window leading up to Discovery date, 1 year later
#   ex: fire discovery date is 2020-08-17,
#   pre-img window would be 2020-05-17 to 2020-08-16
#   post_img window would be 2021-05-17 to 2021-08-16

gdf_yrv2.loc[:,'start'] = gdf_yrv2['Discovery'] + timedelta(days= 275)      # next year, 90 days before calendar date 
gdf_yrv2.loc[:,'end'] = gdf_yrv2['Discovery'] + timedelta(days = 364)       # next year,  1 day before calendar date
gdf_yrv2.loc[:,'pre_start'] = gdf_yrv2['Discovery'] - timedelta(days=90)   # same year, 90 days before calendar date
gdf_yrv2.loc[:,'pre_end'] = gdf_yrv2['Discovery'] - timedelta(days=1)     # same year, 1 day before calendar date

# to ensure all fires get same assessment, need to remove fires whose post-fire image composite would 
# require imagery that theoretically wouldn't be available yet. 
# there appears to be a 7-8 day lag from date of collection to Earth Engine ingestion for 
# the default Landsat collection that John's nrt tool uses ('LANDSAT/LC08/C01/T1_TOA')

# So make post fire img composite right bound be certain # days before today's date to be safe
post_end_cut_off = pd.to_datetime(datetime.now()) - timedelta(days=5)
# exclude fire records whose 'end' value is beyond the cutoff
before_cutoff = len(gdf_yrv2)
gdf_yrv2 = gdf_yrv2[gdf_yrv2.end <= post_end_cut_off]
after_cutoff = len(gdf_yrv2)
print(f'removing {before_cutoff - after_cutoff} fires requiring future non-existent imagery')

# convert datetime to string dtype
gdf_yrv2.loc[:,['Discovery','start', 'end', 'pre_start', 'pre_end']] = gdf_yrv2[['Discovery','start', 'end', 'pre_start', 'pre_end']].astype('str')

# convert to yyyy-mm-dd format
gdf_yrv2.loc[:, 'start'] = [x.split(' ')[0] for x in gdf_yrv2['start']]
gdf_yrv2.loc[:, 'end'] = [x.split(' ')[0] for x in gdf_yrv2['end']]
gdf_yrv2.loc[:, 'pre_start'] = [x.split(' ')[0] for x in gdf_yrv2['pre_start']]
gdf_yrv2.loc[:, 'pre_end'] = [x.split(' ')[0] for x in gdf_yrv2['pre_end']]
gdf_yrv2.loc[:, 'Discovery'] = [x.split(' ')[0] for x in gdf_yrv2['Discovery']]
#subset columns
gdf_finalv2 = gdf_yrv2[['OBJECTID', 'Name', 'AcresAutoCalc', 'Discovery','start', 'end', 'pre_start', 'pre_end', 'geometry']]

file_name = f'nifc_fires_{year_choice}_gte500acres_v2.shp'
out_file = f'{os.path.join(out_path,file_name)}'
print(f'writing out to {out_file}')
#gdf_finalv2.to_file(out_file)
# %%
####################### OPTION 3 ################################
# pre-img filter = 1 yr prior 3mo window leading up to Discovery date
# post-img filter = 1 yr later, 3mo window leading up to Discovery date
#   ex: fire Discovery date is 2020-08-17,
#   pre-img window would be 2019-05-17 to 2019-08-17
#   post_img window would be 2021-05-17 to 2021-08-17

gdf_yrv3.loc[:,'start'] = gdf_yrv3['Discovery'] + timedelta(days= 275)      # 1yr later and 90 days before
gdf_yrv3.loc[:,'end'] = gdf_yrv3['Discovery'] + timedelta(days = 365)       # 1yr later
gdf_yrv3.loc[:,'pre_start'] = gdf_yrv3['Discovery'] - timedelta(days=455)   # 1yr earlier and 90 days before
gdf_yrv3.loc[:,'pre_end'] = gdf_yrv3['Discovery'] - timedelta(days=365)     # 1yr earlier

# to ensure all fires get same assessment, need to remove fires whose post-fire image composite would 
# require imagery that theoretically wouldn't be available yet. 
# there appears to be a 7-8 day lag from date of collection to Earth Engine ingestion for 
# the default Landsat collection that John's nrt tool uses ('LANDSAT/LC08/C01/T1_TOA')

# So make post fire img composite right bound be certain # days before today's date to be safe
post_end_cut_off = pd.to_datetime(datetime.now()) - timedelta(days=5)
# exclude fire records whose 'end' value is beyond the cutoff
before_cutoff = len(gdf_yrv3)
gdf_yrv3 = gdf_yrv3[gdf_yrv3.end <= post_end_cut_off]
after_cutoff = len(gdf_yrv3)
print(f'removing {before_cutoff - after_cutoff} fires requiring future non-existent imagery')
# convert datetime to string dtype
gdf_yrv3.loc[:,['Discovery','start', 'end', 'pre_start', 'pre_end']] = gdf_yrv3[['Discovery','start', 'end', 'pre_start', 'pre_end']].astype('str')

# convert to yyyy-mm-dd format
gdf_yrv3.loc[:, 'start'] = [x.split(' ')[0] for x in gdf_yrv3['start']]
gdf_yrv3.loc[:, 'end'] = [x.split(' ')[0] for x in gdf_yrv3['end']]
gdf_yrv3.loc[:, 'pre_start'] = [x.split(' ')[0] for x in gdf_yrv3['pre_start']]
gdf_yrv3.loc[:, 'pre_end'] = [x.split(' ')[0] for x in gdf_yrv3['pre_end']]
gdf_yrv3.loc[:, 'Discovery'] = [x.split(' ')[0] for x in gdf_yrv3['Discovery']]
#subset columns
gdf_finalv3 = gdf_yrv3[['OBJECTID', 'Name', 'AcresAutoCalc', 'Discovery','start', 'end', 'pre_start', 'pre_end', 'geometry']]
# write to shp
file_name = f'nifc_fires_{year_choice}_gte500acres_v3.shp'
out_file = f'{os.path.join(out_path,file_name)}'
print(f'writing out to {out_file}')
#gdf_finalv3.to_file(out_file)
# %%
