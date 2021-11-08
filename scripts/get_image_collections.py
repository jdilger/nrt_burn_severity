import ee
from datetime import datetime
ee.Initialize()
# burn severity mapping
s2bandsin = ['B1','B2','B3','B4','B5','B6','B7','B8','B8A','B9','B10','B11','B12', 'QA60']
s2bandsout = ['cb','blue','green','red','re1','re2','re3','nir','re4','waterVapor','cirrus','swir1','swir2', 'QA60']

ls8bandsin = ['B1','B2','B3','B4','B5','B6','B7','B9','B10','B11','BQA']
ls8bandsout = ['ca','blue','green','red','nir','swir1','swir2', 'cirrus','temp1','temp2','BQA']
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
    landsatCol : str = None,
    cloudBustingMethod : str = "")-> ee.ImageCollection:
    # image collections
    s2 = ee.ImageCollection("COPERNICUS/S2")
    lstoat1 = ee.ImageCollection("LANDSAT/LC08/C01/T1_RT_TOA")
    lstoat2 = ee.ImageCollection("LANDSAT/LC08/C01/T2_TOA")
    lstoa = ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")

    if sensorTxt == 'sentinel2':
        sensor =  s2.filterBounds(region) \
                        .filterDate(start_date,end_date)
        if cloudBustingMethod == 'bust':
            sensor = sensor.map(mask_s2_clouds)
        sensor = sensor.select(s2bandsin,s2bandsout) \
                            .map(scaleBands)
    if sensorTxt == 'landsat':
        sensor = lstoat1
        if landsatCol == 't2':
            sensor = sensor.merge(lstoat2)
        if landsatCol == 'bestls':
            sensor = lstoa
        if cloudBustingMethod =='bust':
            sensor = sensor.map(bustClouds)

        sensor = sensor.filter(ee.Filter.neq('CLOUD_COVER', -1)).select(ls8bandsin,ls8bandsout) \
            .filterBounds(region) \
                .filterDate(start_date,end_date)

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


