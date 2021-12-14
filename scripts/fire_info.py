#%%
import ee
ee.Initialize()
# structure:
# { "fireName":{
#     "start":str date
#     "end": str date
#     "pre_start": str date
#     "pre_end": str date
#     }
#    }

fire_dict = {
    "hennessey": {
        "region": [r"projects/pyregence-ee/assets/conus/nifc/hennessey_fire_2020"],
        #"region_date": ["2021-07-29"], # seems to be unused
        "start": ["2021-07-17"], # using discovery date or initial response date, 1 month before, a calendar year later
        "end": ['2021-09-17'], # 1 month after, a calendar year later
        "pre_start": '2019-07-17', # +1 month before start, one calendar yr back
        "pre_end": '2019-09-17', # -1 month after start, one calendar year back
    
    
    
    "tamarack": {
        "region": [r"projects/sig-misc-ee/assets/fire_response_2021/perimeters/20210729_Tamarack_KMZ_perimeter_only"],
        "region_date": ["2021-07-29"],
        "start": ["2021-07-04"],
        "end": [None],
        "pre_start": '2020-06-01',
        "pre_end": '2020-09-01',
    },
    "dixie": {
        "region": [r"projects/sig-misc-ee/assets/fire_response_2021/20210923_Dixie", r"projects/sig-misc-ee/assets/fire_response_2021/perimeters/20210810_Dixie_KMZ_perimeter_only"],
        "region_date": ["2021-09-23", "2021-08-10"],
        "start": ["2021-07-14"],
        "end": [None],
        "pre_start": '2020-06-01',
        "pre_end": '2020-09-01',
    },
    "beckwourth": {
        "region": [r"projects/sig-misc-ee/assets/fire_response_2021/perimeters/20210722_Beckwourth_IR_perimeter_only"],
        "region_date": ['2021-07-22'],
        "start": ["2021-07-04"],
        "end": [None],
        "pre_start": '2020-06-01',
        "pre_end": '2020-09-01',
    },

}}


def get_fire_by_name(fire_name: str, current_date: str = None) -> tuple:
    fire_name = fire_name.lower()
    if current_date is None:
        fire_end = fire_dict[fire_name]["end"][0]
    elif isinstance(current_date, str):
        fire_end = current_date

    fire_start = fire_dict[fire_name]["start"][0]
    region = fire_dict[fire_name]["region"][0]
    pre_end = fire_dict[fire_name]["pre_end"]
    pre_start = fire_dict[fire_name]["pre_start"]

    return (region, fire_start, fire_end, pre_start, pre_end)


# won't need fire_name bc it's going to map through one feature at a time
def get_fire_info_from_feature(feat: ee.Feature) -> tuple:
    
    region = ee.Feature(feat).geometry()

    post_start = ee.Feature(feat).getString('start')
    post_end = ee.Feature(feat).getString('end')
    pre_start = ee.Feature(feat).getString('pre_start')
    pre_end = ee.Feature(feat).getString('pre_end')

    return (region, post_start, post_end, pre_start, pre_end)
#%%
from datetime import datetime, timedelta
# new function that defines for itself the start and end date pairs depending on the set of fires its given
fires = ee.FeatureCollection("projects/pyregence-ee/assets/conus/nifc/nifc_fires_2020_gte500acres_v3")
newest_fire = datetime.fromisoformat(fires.sort('Discovery', False).first().getString('Discovery').getInfo())
print('most recent fire date in collection', newest_fire)
# if current date is more than 1 year more than most recent of discovery dates in the fire feature collection, use 
# historical mode
feature = fires.first()

current_date = datetime.utcnow()
difference = current_date - newest_fire

print(feature.getString('Discovery').getInfo())

if difference < timedelta(days=365):
    print('use realtime mode')
    
    pre_start = ee.Date(feature.getString('Discovery')).advance(-410, 'day') # 1 year prior, 45 days before fire discovery
    pre_end = ee.Date(feature.getString('Discovery')).advance(-320, 'day')  # 1 year prior, 45 days after fire discovery
    post_start = ee.Date(feature.getString('Discovery'))                    # actual fire discovery date
    post_end = None                                                         # no end time constraint

    landsat_arg = None
    cloud_arg = None
else:
    print('use historical mode')
    
    pre_start = ee.Date(feature.getString('Discovery')).advance(-455, 'day') # 1 year prior, 90 days before fire discovery
    pre_end = ee.Date(feature.getString('Discovery')).advance(-365, 'day')  # 1 year prior
    post_start = ee.Date(feature.getString('Discovery')).advance(275, 'day') # 1 year later, 90 days before fire discovery
    post_end = ee.Date(feature.getString('Discovery')).advance(365, 'day') # 1 year later

    landsat_arg = 'bestls'
    cloud_arg= 'bust'


print(pre_start.format("Y-M-d").getInfo())
print(pre_end.format("Y-M-d").getInfo())
print(post_start.format("Y-M-d").getInfo())
print(post_end.format("Y-M-d").getInfo())

print(landsat_arg)
print(cloud_arg)
#def define_dates(feat: ee.Feature):




# print(feature.getString('Discovery').getInfo())
# print(pre_start.getInfo())
# print(pre_start.format("Y-M-d").getInfo())

# %%
