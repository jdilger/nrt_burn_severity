#%%
import ee
from datetime import datetime, timedelta
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


def config_mode(featColl: ee.FeatureCollection):
    # historical mode or realtime mode depending on how recent the most recent fire in the collection is
    fires = ee.FeatureCollection(featColl)
    newest_fire = fires.sort('Discovery', False).first()
    newest_fire_date = datetime.fromisoformat(newest_fire.getString('Discovery').getInfo())
    
    current_date = datetime.utcnow()
    difference = current_date - newest_fire_date

    if difference < timedelta(days=365):
        mode = 'realtime'
    else:
        mode= 'historical'

    return mode

def get_fire_info_from_feature_v2(feat: ee.Feature, run_mode):
    # construct pre and post start and end dates depending on mode
    feature = ee.Feature(feat)
    region = feature.geometry()

    if run_mode == 'realtime':
        # realtime mode
        pre_start = ee.String(ee.Date(feature.getString('Discovery')).advance(-365, 'day').format("Y-M-d")) # 1 year prior, same day of discovery
        pre_end = ee.String(ee.Date(feature.getString('Discovery')).advance(-275, 'day').format("Y-M-d"))  # 1 year prior, 90 days after discovery
        post_start = feature.getString('Discovery')  # actual fire discovery date
        post_end = ee.String(ee.Date(feature.getString('Discovery')).advance(90, 'day').format("Y-M-d"))   # 90 days after discovery
  
    else:
        # historical mode
        pre_start = ee.String(ee.Date(feature.getString('Discovery')).advance(-455, 'day').format("Y-M-d")) # 1 year prior, 90 days before fire discovery
        pre_end = ee.String(ee.Date(feature.getString('Discovery')).advance(-365, 'day').format("Y-M-d"))  # 1 year prior
        post_start = ee.String(ee.Date(feature.getString('Discovery')).advance(275, 'day').format("Y-M-d")) # 1 year later, 90 days before fire discovery
        post_end = ee.String(ee.Date(feature.getString('Discovery')).advance(365, 'day').format("Y-M-d")) # 1 year later

    return region, pre_start, pre_end, post_start, post_end