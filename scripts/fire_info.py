# structure:
# { "fireName":{
#     "start":str date
#     "end": str date
#     "pre_start": str date
#     "pre_end": str date
#     }
#    }

fire_dict = {
    "tamarack":{
        "region" : [r"projects/sig-misc-ee/assets/fire_response_2021/perimeters/20210729_Tamarack_KMZ_perimeter_only"],
        "start": ["2021-07-04"],
        "end": [None],
        "pre_start": '2020-06-01',
        "pre_end": '2020-09-01',
        },
    "dixie":{
        "region" : [r"projects/sig-misc-ee/assets/fire_response_2021/perimeters/20210810_Dixie_KMZ_perimeter_only"],
        "start": ["2021-07-14"],
        "end": [None],
        "pre_start": '2020-06-01',
        "pre_end": '2020-09-01',
        },
    "beckwourth":{
        "region" : [r"projects/sig-misc-ee/assets/fire_response_2021/perimeters/20210722_Beckwourth_IR_perimeter_only"],
        "start": ["2021-07-04"],
        "end": [None],
        "pre_start": '2020-06-01',
        "pre_end": '2020-09-01',
        },
    
   }    

def get_fire_by_name(fire_name:str,current_date : str = None)->tuple:
    fire_name = fire_name.lower()
    if current_date is None:
        fire_end = fire_dict[fire_name]["end"][0]
    elif isinstance(current_date,str):
        fire_end = current_date
    
    fire_start = fire_dict[fire_name]["start"][0]
    region = fire_dict[fire_name]["region"][0]
    pre_end = fire_dict[fire_name]["pre_end"]
    pre_start = fire_dict[fire_name]["pre_start"]

    return (region, fire_start, fire_end, pre_start, pre_end)