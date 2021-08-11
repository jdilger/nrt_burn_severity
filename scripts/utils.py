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