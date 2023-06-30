import json
import warnings
import requests
import geopandas as gpd
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import urllib3
import re
"""This is a web-service to Geopandas GeoDataFrame module. 
It is used in the pull_* CLI scripts to download data from a web feature service to a local shapefile"""
warnings.simplefilter("ignore")

def parse_crs_extent(url):
    # parse extent info and spatial ref info from HTML using beautifulsoup
    req = urllib3.PoolManager()

    with req.request('GET', url, preload_content=False) as r:
        soup = BeautifulSoup(r, 'html.parser')
        spatialref = int(re.findall('\d{4,6}', soup.find(string=re.compile('Spatial Reference')))[1]) #get second crs number in Spatial Extent item
        
        xmin, ymin, xmax, ymax = [float(x.split()[1]) for x in soup.find_all(string = re.compile('XMin|YMin|XMax|YMax'))] #get just the numbers from each extent item
        extent = {'xmin': xmin,
        'ymin': ymin,
        'xmax': xmax,
        'ymax': ymax}

    return extent, spatialref

def to_gdf(url):
    # change baseurl to the service url
    BASEURL = url #url string passed to the function

    r = requests.get(BASEURL+"/queryDomains",params=dict(f="json"),verify=False)
    service_metadata = r.json()

    if 'error' in service_metadata.keys():
        
        extent, spatialref = parse_crs_extent(url)
        
    else:
        # check to make sure the services has the capabilities we need
        is_queriable = "Query" in service_metadata["capabilities"]
        supports_geojson = "geoJSON" in service_metadata["supportedQueryFormats"]
        has_advanced_queries = service_metadata["supportsAdvancedQueries"]

        # raise error is any capability is not avaiable
        if all((is_queriable, supports_geojson, has_advanced_queries)) is False:
            raise RuntimeError("Service being accessed does not support the required functionality for data API pull")

        # get extent and spatial reference information to query for features
        extent = {k:v for k,v in service_metadata["extent"].items() if k.startswith("x") or k.startswith("y")}
        spatialref = service_metadata["extent"]["spatialReference"]["wkid"]

    # send request to get object ids for explict requests
    idquery = dict(
    outSR=spatialref,
    geometry=json.dumps(extent),
    geometryType="esriGeometryEnvelope",
    returnIdsOnly=True,
    f="JSON"
    )

    r = requests.get(BASEURL+"/query",params=idquery,verify=False)

    # get object ids as list
    objectids= r.json()["objectIds"]

    # need to chunk into multiple queries to avoid really long urls
    # long urls cannot be sent and will return errors, this helps prevent that
    oidchunks = [objectids[x:x+20] for x in range(0, len(objectids), 20)]

    # function to request features based on object ids
    # this is required so we can send concurrent requests based on chunks of ids
    def getfeatures(oids):

        featurequery = dict(
            objectIds=','.join(map(str, oids)),
            outSR=spatialref,
            geometry=json.dumps(extent),
            geometryType="esriGeometryEnvelope",
            outFields = '*',
            f="GeoJSON"
        )

        r = requests.get(BASEURL+"/query",params=featurequery,verify=False)

        feature_dict = r.json()

        # check if the result is in fact a FeatureCollection GeoJSON
        # for some reason services return 200 with a dict of 400 error...WTF ESRI...
        if "features" in feature_dict.keys():
            return feature_dict["features"]
        else:
            return []

    # send multiple concurrent requests based on object id chunks
    # set max workers to number of parallel requests, 8 is usually good
    with ThreadPoolExecutor(max_workers=8) as executor:
    # get a generator that spawns the request threads
        gen = executor.map(getfeatures, oidchunks)

    # unpack list of lists
    features = [item for sublist in list(gen) for item in sublist]

# convert list of features to geopandas format for processing
    gdf = gpd.GeoDataFrame.from_features(features)
    return gdf
    # do whatever formatting needed with the geodataframe

# %%
# #testing
# url = 'https://services1.arcgis.com/Pat8LQYI0Udhgy4G/ArcGIS/rest/services/NMVeg_July2017/FeatureServer/5'
# extent, spatialref = parse_crs_extent(url)
# print(extent, '\n', spatialref)
# gdf = to_gdf(url)
# gdf
# %%