# nrt_burn_severity
Workflow for generating burn severity maps in google earth engine from user-provided fire perimeters

![NRT_readme_pic_conus](https://user-images.githubusercontent.com/51868526/162246851-099b789a-7942-4b0f-8989-f62c8386660d.JPG)

Steps to Map Burn Severity:
1. Download Fire Perimeter vector data from a reliable source. 
    * On Our latest use of this repository, we used pull_nifc_fires.py, but we also have CLI scripts for CalFIRE and MTBS fire perimeters. 
2. Upload those Fire Perimeters to GEE as a FeatureCollection.
3. Use the BS_Mapper.ipynb to produce categorical burn severity ee.Image's, plugging the Fire Perimeter ee.FeatureCollection(s) in as the inputs. Then export either to GEE Asset or Google Drive.

NOTE: For use in FireFactor product cycle, export yearly CONUS-wide BS to ee.Images under this GEE Asset folder: `projects/pyregence-ee/assets/workflow_assets/` and use the base name prefix - BS_[perimetersSource]_[YEAR]. Those ee.Image's will be consumed by this CLI script for FireFactor: [https://github.com/pyregence/landfire/blob/main/src/CreateDistLayer/create_dist_wildfire.py](https://github.com/pyregence/landfire/blob/main/src/CreateDistLayer/create_dist_wildfire.py). 