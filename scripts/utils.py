# utils.py
import ee

__defaults ={
    'landsat':{
        'exportScale':30,
        },
    'sentinel2':{
        'exportScale':10,
        },
    'bucket':'gee-upload',

    
}

def default_export_name(*args : str)->str:
    desc = list(map(lambda a : a.replace("-","").lower().strip(),args))
    return "_".join(desc)

def exportMapToCloud(img, desc, region, **kwargs):

    scale = kwargs.get('scale', __defaults[kwargs.get('default')]['exportScale'])
    bucket = kwargs.get('bucket',__defaults['bucket'])
    prefix = kwargs.get('prefix',None)
    crs = kwargs.get('crs',None)


    if prefix:
        fileNamePrefix = f"{prefix}/{desc}"
    else:
        fileNamePrefix = desc

    task_ordered = ee.batch.Export.image.toCloudStorage(image=img,
                                                    description=desc,
                                                    bucket=bucket,
                                                    fileNamePrefix=fileNamePrefix,
                                                    region=region,
                                                    maxPixels=1e13,
                                                    crs=crs,
                                                    scale=scale,
                                                    formatOptions={'cloudOptimized':True}
    )

    task_ordered.start()
    print("task started :",desc)



def exportImgtoAsset(img, desc, export:bool=False):
    '''Exports img using crs, crs_transform, and dimensions of LANDFIRE conus-wide raster template'''
    
    asset_path = 'projects/pyregence-ee/assets/conus/nifc/'
    
    
    if export == True:
        task = ee.batch.Export.image.toAsset(
        image = img,
        description=desc,
        assetId= asset_path+desc,
        pyramidingPolicy={'SEVERITY':'mode'},
        dimensions= [154208, 97283],                               
        crs= 'EPSG:5070',
        crs_transform= [30, 0, -2362425.000000002, 0, -30, 3177435.000000003],
        maxPixels= 1e12
        )
        
        task.start()
        print('export task started')
    
    else:
        print(f'would export to {asset_path}{desc}')
        print('set export = True to when ready')
