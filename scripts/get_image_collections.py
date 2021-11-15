import ee
from datetime import datetime
ee.Initialize()
# burn severity mapping
s2bandsin = ['B1','B2','B3','B4','B5','B6','B7','B8','B8A','B9','B10','B11','B12', 'QA60']
s2bandsout = ['cb','blue','green','red','re1','re2','re3','nir','re4','waterVapor','cirrus','swir1','swir2', 'QA60']

# with current L5 / L7 / L8 selection workflow in get_image_collections, there are instances where pre img used by mtbs was a different Landsat sensor than post img, 
# so i have to make sure that every collection has the same number of bands with same names, meaning remove those we don't use 
# really only need nir and swir2 for nbr  but will keep R G B and QA bands
ls8bandsin = ['B2','B3','B4','B5','B6','B7','BQA']
ls8bandsout = ['blue','green','red','nir','swir1','swir2', 'BQA']

ls4bandsin = ['B1','B2','B3','B4','B5', 'B7', 'BQA']
ls4bandsout = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'BQA']

ls5bandsin = ['B1','B2','B3','B4','B5','B7', 'BQA']
ls5bandsout = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'BQA']

ls7bandsin = ['B1','B2','B3','B4','B5', 'B7', 'BQA']
ls7bandsout = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'BQA']

#original bands list
# ls8bandsin = ['B1','B2','B3','B4','B5','B6','B7','B9','B10','B11','BQA']
# ls8bandsout = ['ca','blue','green','red','nir','swir1','swir2', 'cirrus','temp1','temp2','BQA']

# ls5bandsin = ['B1','B2','B3','B4','B5','B6','B7', 'BQA']
# ls5bandsout = ['blue', 'green', 'red', 'nir', 'swir1', 'temp1', 'swir2', 'BQA']

# ls7bandsin = ['B1','B2','B3','B4','B5','B6_VCID_1', 'B6_VCID_2', 'B7', 'BQA']
# ls7bandsout = ['blue', 'green', 'red', 'nir', 'swir1', 'temp1', 'temp2', 'swir2', 'BQA']

# cloud masking paramters
cloudThresh = 20
contractPixels = 1.5
dilatePixels =2.5

def scaleBands(img : ee.Image)-> ee.Image:
    prop = img.toDictionary()
    t = img.select( ['cb','blue','green','red','re1','re2','re3','nir','re4','waterVapor','cirrus','swir1','swir2']).divide(10000)
    t = t.addBands(img.select(['QA60'])).set(prop).copyProperties(img,['system:time_start','system:footprint'])
    return ee.Image(t)

# #Basic cloud busting function
def bustClouds(img:ee.Image)-> ee.Image:
    t = img
    cs = ee.Algorithms.Landsat.simpleCloudScore(img).select('cloud')
    out = img.mask(img.mask().And(cs.lt(cloudThresh)))
    return out.copyProperties(t)

def mask_s2_clouds(image: ee.Image)->ee.Image:
    qa = image.select('QA60').int16()
    
    # Bits 10 and 11 are clouds and cirrus, respectively.
    cloudBitMask = pow(2, 10)
    cirrusBitMask = pow(2, 11)
    
    # Both flags should be set to zero, indicating clear conditions.
    mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))
  
    # Return the masked and scaled data.
    return image.updateMask(mask)

def get_image_collection(sensorTxt: str,
    region:ee.Geometry,
    start_date:str,
    end_date:str,
    scene_id:str,
    landsatCol : str = None,
    cloudBustingMethod : str = "")-> ee.ImageCollection:
    # image collections
    s2 = ee.ImageCollection("COPERNICUS/S2")
    
    ls8toat1 = ee.ImageCollection("LANDSAT/LC08/C01/T1_RT_TOA")
    ls8toat2 = ee.ImageCollection("LANDSAT/LC08/C01/T2_TOA")
    ls8toa = ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")

    ls7toat1 = ee.ImageCollection("LANDSAT/LE07/C01/T1_RT_TOA")
    ls7toat2 = ee.ImageCollection("LANDSAT/LE07/C01/T2_TOA")
    ls7toa = ee.ImageCollection("LANDSAT/LE07/C01/T1_TOA")
    
    ls5toat2 = ee.ImageCollection("LANDSAT/LT05/C01/T2_TOA")
    ls5toa = ee.ImageCollection("LANDSAT/LT05/C01/T1_TOA")

    ls4toa = ee.ImageCollection("LANDSAT/LT04/C01/T1_TOA")
    ls4toa2 = ee.ImageCollection("LANDSAT/LT04/C01/T2_TOA")
    
    
    # #start and end dates converted to ee.Numbers to compare w/ image date ee.Numbers below
    # dt_start = ee.Number(ee.String(start_date).replace('-','', 'g'))
    # dt_end = ee.Number(ee.String(end_date).replace('-','', 'g'))

    # # image date constraints
    # ls5_dt_end = ee.Number(20120505)
    # ls8_dt_start = ee.Number(20130411)

    if sensorTxt == 'sentinel2':
        sensor =  s2.filterBounds(region) \
                        .filterDate(start_date,end_date)
        if cloudBustingMethod == 'bust':
            sensor = sensor.map(mask_s2_clouds)
        sensor = sensor.select(s2bandsin,s2bandsout) \
                            .map(scaleBands)
    
    # if sensorTxt == 'landsat': 
    #     sensor = ls8toat1
    #     if landsatCol == 't2':
    #         sensor = sensor.merge(ls8toat2)
    #     if landsatCol == 'bestls':
    #         sensor = ls8toa
    #     if cloudBustingMethod =='bust':
    #         sensor = sensor.map(bustClouds)
    # sensor = sensor.filter(ee.Filter.neq('CLOUD_COVER', -1)).select(ls8bandsin,ls8bandsout) \
    #     .filterBounds(region) \
    #         .filterDate(start_date,end_date)
    
# trying this for now, uncomment above to fix it
    if sensorTxt == 'landsat': 
        sensor4 = ls4toa
        sensor5 = ls5toa
        sensor7 = ls7toat1
        sensor8 = ls8toat1

        if landsatCol == 't2':
            sensor4 = sensor4.merge(ls4toa2)
            sensor5 = sensor5.merge(ls5toat2)
            sensor7 = sensor7.merge(ls7toat2)
            sensor8 = sensor8.merge(ls8toat2)

        if landsatCol == 'bestls':
            sensor4 = ls4toa
            sensor5 = ls5toa
            sensor7 = ls7toa
            sensor8 = ls8toa

        if cloudBustingMethod =='bust':
            sensor4 = sensor4.map(bustClouds)
            sensor5 = sensor5.map(bustClouds)
            sensor7 = sensor7.map(bustClouds)
            sensor8 = sensor8.map(bustClouds)

        sensor4 = sensor4.filter(ee.Filter.neq('CLOUD_COVER', -1)).select(ls4bandsin,ls4bandsout) \
            .filterBounds(region) \
                .filterDate(start_date,end_date)

        sensor5 = sensor5.filter(ee.Filter.neq('CLOUD_COVER', -1)).select(ls5bandsin,ls5bandsout) \
            .filterBounds(region) \
                .filterDate(start_date,end_date)
        
        sensor7 = sensor7.filter(ee.Filter.neq('CLOUD_COVER', -1)).select(ls7bandsin,ls7bandsout) \
            .filterBounds(region) \
                .filterDate(start_date,end_date)
        
        sensor8 = sensor8.filter(ee.Filter.neq('CLOUD_COVER', -1)).select(ls8bandsin,ls8bandsout) \
            .filterBounds(region) \
                .filterDate(start_date,end_date)
       
        def slice_scene_id(img):
            image = ee.Image(img)
            slice = image.getString('LANDSAT_SCENE_ID').slice(0,4)
            return image.set('scene_id_slice',slice)
    
        sensor = sensor4.merge(sensor5).merge(sensor7).merge(sensor8).map(slice_scene_id)
        sensor = sensor.filter(ee.Filter.stringContains('scene_id_slice', scene_id))
        
    return sensor

def addDateBand(i: ee.Image)-> ee.Image:
    date = ee.Date(i.get('system:time_start'))
    yyyymmdd = date.format('YYYYMMdd')
    asnum = ee.Number.parse(yyyymmdd)
    dateimg = ee.Image.constant(asnum).int64() \
            .rename('date') \
            .updateMask(i.select(0).gt(0))
            
    return i.addBands(dateimg).set('yyyymmdd',yyyymmdd)

def add_date_band(col:ee.ImageCollection,sensorTxt: str)->ee.ImageCollection:
    
    col = col.map(addDateBand)
    return col

def make_nrt_composite(col : ee.ImageCollection, *args)-> ee.Image:

    col = col.sort('system:time_start',False)
    bands = col.first().bandNames()
    maxdate = col.first().get('yyyymmdd')

    nrt = col.reduce(ee.Reducer.firstNonNull(),4).set('yyyymmdd',maxdate)
    return nrt.rename(bands)

def maskL8(image: ee.Image)->ee.Image:
    qa = image.select('BQA')
    #   #/ Check that the cloud bit is off.
    #   # See https:#www.usgs.gov/land-resources/nli/landsat/landsat-collection-1-level-1-quality-assessment-band
    mask = qa.bitwiseAnd(1 << 4).eq(0)
    return image.updateMask(mask)

def first_img(col:ee.ImageCollection,*args)->ee.Image:
    return col.first()

def make_pre_composite(col : ee.ImageCollection, start_date : str, end_date:str)->ee.Image:
    pre = col.filterDate(start_date,end_date)    
    return pre.mean()

def get_composite(col : ee.ImageCollection, func, *args : str )-> ee.Image:
    col = add_date_band(col, args[0])
    # when using in the fc burn severity notebook the *args are server-side compute objects not strings like in other notebook, so just commented out printing
    #print(*args)
    composite = func(col,*args)
    return composite

if __name__ == '__main__':

    py_date = datetime.utcnow()
    ee_date = ee.Date(py_date)
    print(py_date)
    region = ee.Geometry.Point([-122.19661881744865, 37.06041582510092])
    sd = "2020-01-01"
    ed = "2020-12-01"
    sensorTxt ="landsat"
    ls = get_image_collection(sensorTxt,region,sd,ed,landsatCol='bestls')
    print(ls.size().getInfo())

    # nrt composite
    img = get_composite(ls,make_nrt_composite,sensorTxt)
    print(img.bandNames().getInfo())
    # nrt first
    img = get_composite(ls,first_img,sensorTxt)
    print(img.bandNames().getInfo())

    psd = '2020-01-01'
    ped = '2020-06-01'
    preimg = get_composite(ls,make_pre_composite,psd,ped)
    print(preimg.bandNames().getInfo())


