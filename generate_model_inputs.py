#%%
import ee
import scripts.analysis_functions as af
import scripts.get_image_collections as gic
import scripts.fire_info as fi

def remap_evt_yr(featColl):
    featCol = ee.FeatureCollection(featColl)
    fire_yr_in = ee.List.sequence(1984,2019)
    fire_yr_out = ee.List.repeat(2001,18)\
                    .cat(ee.List.repeat(2008,7))\
                    .cat(ee.List.repeat(2010,2))\
                    .cat(ee.List.repeat(2012,2))\
                    .cat(ee.List.repeat(2016,7))
    return featCol.remap(fire_yr_in, fire_yr_out, 'fire_yr')

def get_evt(feat):
    feature = ee.Feature(feat)
    evt_yr = feature.getNumber('fire_yr')
    evt = ee.ImageCollection("projects/pyregence-ee/assets/conus/landfire/evt")
    return evt.filter(ee.Filter.calendarRange(evt_yr, evt_yr, 'year')).first().clip(feature.geometry())


def get_gridmet(feat) -> ee.Image:
    gridmet_bands = ['th', 'tmmn', 'tmmx', 'vs', 'erc', 'bi', 'fm100', 'fm1000']
    gridmet_bands_rename = ['wind_dir', 't_min', 't_max', 'wind_velocity', 'enrg_release', 'burn_ind', '100hr_moisture', '1000hr_moisture']
    gridmet = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET").select(gridmet_bands, gridmet_bands_rename)
    
    feature = ee.Feature(feat)
    start = feature.getString('gridmet_st')
    end = feature.getString('gridmet_en')
    
    return ee.Image(gridmet.filterDate(start,end).mean().clip(feature.geometry()))

def get_mtbs_bs(feat) -> ee.Image:
    mtbs_bs = ee.ImageCollection("projects/pyregence-ee/assets/conus/mtbs/burn-severity-corrected-10062021")
    feature = ee.Feature(feat)

    fire_yr = ee.Number.parse(ee.String(feature.getString('Ig_Date')).slice(0,4))
    return ee.Image(mtbs_bs.filter(ee.Filter.calendarRange(fire_yr, fire_yr, 'year')).first().clip(feature.geometry()) )

def bi_calc(feat) -> ee.Image:
    
    feature = ee.Feature(feat)
    region, post_start, post_end, pre_start, pre_end, pre_scene_id, post_scene_id = fi.get_fire_info_from_feature(feature) 
    
    # landsatCol : None, t2, bestls
    # None=T1 real time toa, t2=None+ T1 real time toa, bestls=T1 toa
    # cloudBustingMethod : None, bust
    # None=No cloud masking/busting, bust=cloud busting
    # sensor : landsat, sentinel2
    sensor = "landsat"
    
    pre_collection = gic.get_image_collection(sensor,region,pre_start,pre_end, pre_scene_id, landsatCol='bestls',cloudBustingMethod='bust')
    pre_img = gic.get_composite(pre_collection,gic.make_pre_composite,pre_start,pre_end)
  
    post_collection = gic.get_image_collection(sensor,region,post_start,post_end, post_scene_id, landsatCol='bestls', cloudBustingMethod='bust') #changed landsatCol, cloudBustingMethod, added pre_ and post_scene_id vars, 
    post_img = gic.get_composite(post_collection,gic.make_pre_composite,post_start, post_end) # changed to make_pre_composite since that takes a mean comoposite
    
    pre_nbr = af.nbr(pre_img)
    post_nbr = af.nbr(post_img)
    
    dnbr = af.dnbr(pre_nbr, post_nbr).select('dNBR')
    rdnbr = af.rdnbr(pre_img,post_img).select('RdNBR')

    return ee.Image(rdnbr).addBands(dnbr).clip(region)

def construct_stack(featColl):
    features = ee.FeatureCollection(featColl)
    gridmet_stack = ee.ImageCollection(features.map(get_gridmet)).mosaic()
    mtbs_bs_stack = ee.ImageCollection(features.map(get_mtbs_bs)).mosaic()
    bi_stack = ee.ImageCollection(features.map(bi_calc)).mosaic()
    evt_stack = ee.ImageCollection(remap_evt_yr(features).map(get_evt)).mosaic()
    
    return ee.Image(mtbs_bs_stack).addBands(bi_stack).addBands(gridmet_stack).addBands(evt_stack)

#%%
# test that each function works
# burn index function not working
# fires = ee.FeatureCollection("projects/pyregence-ee/assets/conus/mtbs/mtbs_perims_date_processed")
# fires_subset = fires.filter(ee.Filter.eq('Ig_Date', '2018-07-27'))

# print(fires_subset.size().getInfo())

# fires_bi_imgs = ee.ImageCollection(fires_subset.map(bi_calc))
# print(fires_bi_imgs.first().getInfo())

# # %%
# # troubleshooting
# fire_test = fires_subset.first()
# print(fire_test.getInfo()['properties'])
# region, post_start, post_end, pre_start, pre_end = fi.get_fire_info_from_feature(fire_test)

# sensor = "landsat"
# pre_collection = gic.get_image_collection(sensor,region,pre_start,pre_end,landsatCol='bestls',cloudBustingMethod='bust')
# print(pre_collection.size().getInfo())
# pre_img = gic.get_composite(pre_collection,gic.make_pre_composite,pre_start,pre_end)
# print(pre_img.bandNames().getInfo())

# post_collection = gic.get_image_collection(sensor,region,post_start,post_end,landsatCol=None)
# print(post_collection.size().getInfo())
# post_img = gic.get_composite(post_collection,gic.make_nrt_composite,sensor)
# print(post_img.bandNames().getInfo())

# # here where get Image.rename() bands length mismatch
# dnbr = af.dnbr(pre_img, post_img).select('dNBR')
# rdnbr = af.rdnbr(pre_img,post_img).select('RdNBR')

# print(dnbr.getInfo())

# %%

# gridmet function testing
