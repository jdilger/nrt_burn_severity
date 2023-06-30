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

# NOTE: this is no longer used. All of the fire_info setting and getting is done Earth Engine server side so that 
#   we are able to parallelize the BS mapping across 10s/100s/100000s of fire perimeters in one batch job.
fire_dict = {
    "czu": {
        "region": [r"projects/pyregence-ee/assets/fires_bs_tool/czu_lightning_perim_20220815"],
        #"region_date": ["2020-08-16"], # seems to be unused
        "start": ["2021-05-16"], # using discovery date or initial response date, 1 month before, a calendar year later
        "end": ['2021-08-16'], # 1 month after, a calendar year later
        "pre_start": ['2019-05-16'], # +1 month before start, one calendar yr back
        "pre_end": ['2019-08-16'], # -1 month after start, one calendar year back
    },
    
    "hennessey": {
        "region": [r"projects/pyregence-ee/assets/conus/nifc/hennessey_fire_2020"],
        #"region_date": ["2021-07-29"], # seems to be unused
        "start": ["2021-07-17"], # using discovery date or initial response date, 1 month before, a calendar year later
        "end": ['2021-09-17'], # 1 month after, a calendar year later
        "pre_start": '2019-07-17', # +1 month before start, one calendar yr back
        "pre_end": '2019-09-17', # -1 month after start, one calendar year back
    },
    
    
    "tamarack": {
        "region": [r"projects/sig-misc-ee/assets/fire_response_2021/perimeters/20210729_Tamarack_KMZ_perimeter_only"],
        "region_date": ["2021-07-29"],
        "start": ["2021-07-04"],
        "end": [None],
        "pre_start": '2020-06-01',
        "pre_end": '2020-09-01',
    },
    "dixie": {
        "region": [r"projects/pyregence-ee/assets/fires_bs_tool/dixie_perim_20220810",r"projects/sig-misc-ee/assets/fire_response_2021/20210923_Dixie", r"projects/sig-misc-ee/assets/fire_response_2021/perimeters/20210810_Dixie_KMZ_perimeter_only"],
        "region_date": ["2021-07-13","2021-09-23", "2021-08-10"],
        "start": ["2022-04-17","2021-07-14"],
        "end": ["2022-07-16",None],
        "pre_start": ["2020-04-17",'2020-06-01'],
        "pre_end": ["2020-07-16",'2020-09-01'],
    },
    "beckwourth": {
        "region": [r"projects/sig-misc-ee/assets/fire_response_2021/perimeters/20210722_Beckwourth_IR_perimeter_only"],
        "region_date": ['2021-07-22'],
        "start": ["2021-07-04"],
        "end": [None],
        "pre_start": '2020-06-01',
        "pre_end": '2020-09-01',
    },

}


def get_fire_by_name(fire_name: str, current_date: str = None) -> tuple:
    fire_name = fire_name.lower()
    if current_date is None:
        fire_end = fire_dict[fire_name]["end"][0]
    elif isinstance(current_date, str):
        fire_end = current_date

    fire_start = fire_dict[fire_name]["start"][0]
    region = fire_dict[fire_name]["region"][0]
    pre_end = fire_dict[fire_name]["pre_end"][0]
    pre_start = fire_dict[fire_name]["pre_start"][0]

    return (region, fire_start, fire_end, pre_start, pre_end)

def config_mode(feat: ee.Feature):
    '''returns 'historical' mode or 'recent' mode depending on how recent the fire is; for collections use most recent fire feature'''
    fire = ee.Feature(feat)
    fire_date = datetime.fromisoformat(fire.getString('Discovery').getInfo())
    
    current_date = datetime.utcnow()
    difference = current_date - fire_date

    if difference < timedelta(days=276): 
        mode = 'recent'
    else:
        mode= 'historical'

    return mode

def get_fire_info_from_feature(feat: ee.Feature, run_mode):
    '''construct pre and post start and end dates depending on mode string determined by config_mode()'''
    feature = ee.Feature(feat)
    region = feature.geometry()

    if run_mode == 'recent':
        # recent mode
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

def set_dates_recent_mode(feat: ee.Feature):
    '''construct pre and post start and end dates using historic fire mode'''
    feature = ee.Feature(feat)
    
    pre_start = ee.Date(feature.getString('Discovery')).advance(-365, 'day') # 1 year prior, same day of discovery# 1 year prior, same day of discovery
    pre_start_readable = ee.String(ee.Date(pre_start).format('YYYYMMdd')) 
    
    pre_end = ee.Date(feature.getString('Discovery')).advance(-275, 'day')  # 1 year prior, 90 days after discovery
    pre_end_readable = ee.String(ee.Date(pre_end).format('YYYYMMdd')) # also wasn't cast as a string before - fixed

    # post_start = ee.Date(ee.String(feature.getString('Discovery')).replace('-','','g'))  # actual fire discovery date
    # post_start_readable = ee.String(feature.getString('Discovery')).replace('-','','g')
    post_start = ee.Date(feature.getString('Discovery')).advance(1, 'day')  # actual fire discovery date ## do same Date.advance routine as others
    post_start_readable = ee.String(ee.Date(post_start).format('YYYYMMdd'))

    post_end = ee.Date(feature.getString('Discovery')).advance(90, 'day')   # 90 days after discovery
    post_end_readable = ee.String(ee.Date(post_end).format('YYYYMMdd'))
    
    return feature.set('pre_start',pre_start,'pre_start_readable',pre_start_readable,
                        'pre_end',pre_end, 'pre_end_readable', pre_end_readable,
                        'post_start',post_start, 'post_start_readable', post_start_readable,
                        'post_end',post_end, 'post_end_readable', post_end_readable)

def set_dates_historic_mode(feat: ee.Feature):
    '''construct pre and post start and end dates using recent fire mode'''
    feature = ee.Feature(feat)
    
    pre_start = ee.Date(feature.getString('Discovery')).advance(-455, 'day') # 1 year prior, 90 days before fire discovery
    pre_start_readable = ee.String(ee.Date(pre_start).advance(-455, 'day').format('YYYYMMdd')) # 1 year prior, 90 days before fire discovery

    pre_end = ee.Date(feature.getString('Discovery')).advance(-365, 'day')  # 1 year prior
    pre_end_readable = ee.String(ee.Date(pre_end).format('YYYYMMdd'))  # 1 year prior

    post_start = ee.Date(feature.getString('Discovery')).advance(275, 'day') # 1 year later, 90 days before fire discovery
    post_start_readable = ee.String(ee.Date(post_start).format('YYYYMMdd')) # 1 year later, 90 days before fire discovery

    post_end = ee.Date(feature.getString('Discovery')).advance(365, 'day') # 1 year later
    post_end_readable = ee.String(ee.Date(post_end).format('YYYYMMdd')) # 1 year later

    return feature.set('pre_start',pre_start,'pre_start_readable',pre_start_readable,
                        'pre_end',pre_end, 'pre_end_readable', pre_end_readable,
                        'post_start',post_start, 'post_start_readable', post_start_readable,
                        'post_end',post_end, 'post_end_readable', post_end_readable)

def set_windows(feat: ee.Feature):
    '''sets pre/post date windows in the feature's properties following ruleset based on recency of Fire Date'''
    fire = ee.Feature(feat)
    fire_date = ee.Date(fire.getString('Discovery'))
    
    current_date = ee.Date(datetime.now())
    difference = current_date.difference(fire_date,'day')
    # if fire date is more than a year ago we can use historical mode (1 yr pre 1 yr post) 
    # otherwise we have to use recent mode
    mode = ee.Algorithms.If(difference.gte(365),ee.String('historical'),ee.String('recent'))
    fire = fire.set('mode',mode)
    fire = ee.Algorithms.If(ee.String(mode).equals('recent'),set_dates_recent_mode(fire),set_dates_historic_mode(fire))
    return fire