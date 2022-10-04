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

export_opts = {
                'crs': {
                    'conus': 'EPSG:5070',
                    'single_fire': 'EPSG:3857'},
                
                'crs_transform': {
                    'conus': [30, 0, -2362425.0, 0, -30, 3177435],
                    'single_fire': None},

                'dimensions': {
                    'conus': [154208, 97283],
                    'single_fire': None
                },
                
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


def exportImgtoAsset(img, desc, region, asset_folder, export_type, export:bool=False, **kwargs):
    '''Exports img to asset using using export options dependent on export_type chosen ('conus' or 'single_fire')'''
    
    if export_type == 'conus':

        dimensions= export_opts.get('dimensions')[export_type]                               
        crs= export_opts.get('crs')[export_type]
        crs_transform= export_opts.get('crs_transform')[export_type]

        task = ee.batch.Export.image.toAsset(image = img,
                                        description=desc,
                                        assetId= asset_folder + '/' + desc,
                                        pyramidingPolicy={'SEVERITY':'mode'},
                                        dimensions= dimensions,                               
                                        crs= crs,
                                        crs_transform = crs_transform,
                                        maxPixels= 1e13
                                        )
    elif export_type == 'single_fire':
        
        region = img.geometry()
        scale = kwargs.get('scale', __defaults[kwargs.get('default')]['exportScale'])

        task = ee.batch.Export.image.toAsset(image = img,
                                        description=desc,
                                        assetId= asset_folder + '/' + desc,
                                        pyramidingPolicy={'SEVERITY':'mode'},
                                        scale = scale,
                                        region = region,
                                        maxPixels= 1e13
                                        )

    else:
        raise RuntimeError("Must select export_type")
    
    if export == True:
        task.start()
        print(f'export task started: {asset_folder}/{desc}')
    else:
        print(f'would export to {asset_folder}/{desc}')
        print('set export = True to when ready')
        

def exportImgtoDrive(img, desc, region, export_type, folder:str='BurnSeverity_outputs', export:bool=False, **kwargs):
    '''Exports img to Google Drive using export options dependent on export_type chosen ('conus' or 'single_fire')'''
    
    if export_type == 'conus':
        dimensions= export_opts.get('dimensions')[export_type]                               
        crs= export_opts.get('crs')[export_type]
        crs_transform= export_opts.get('crs_transform')[export_type]
        
        task = ee.batch.Export.image.toDrive(image= img,
                                            description= desc,
                                            folder= folder,
                                            fileNamePrefix= desc,
                                            dimensions = dimensions,
                                            crs = crs,
                                            crs_transform = crs_transform,
                                            maxPixels= 1e13,
                                            formatOptions={'cloudOptimized':True}
                                            )

    elif export_type == 'single_fire': 
        
        scale = kwargs.get('scale', __defaults[kwargs.get('default')]['exportScale'])
        
        task = ee.batch.Export.image.toDrive(image= img,
                                            description= desc,
                                            folder= folder,
                                            fileNamePrefix= desc,
                                            region = region,
                                            scale = scale,
                                            maxPixels= 1e13,
                                            formatOptions={'cloudOptimized':True}
                                            )
    else:
        raise RuntimeError("Must select export_type")
    
    if export == True:
        task.start()
        print(f'export task started: {folder}/{desc}')
    
    else:
        print(f'would export to {folder}/{desc}')
        print('set export = True to when ready')
