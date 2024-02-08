import boto3
import os
import logging
from botocore.exceptions import ClientError
import numpy as np
from osgeo import gdal
from dotenv import load_dotenv
import requests

load_dotenv()
s3 = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
gdal.UseExceptions()

import os
from sklearn.cluster import KMeans

def calculate_ndmi(nir, swir, **kwargs):
    ndmi_expression = "(A - B) / (A + B)"
    ndmi_band = "/tmp/ndmi.tif"
    gdal_calc_cmd = f"gdal_calc.py -A '{nir}' -B '{swir}' --outfile={ndmi_band} --calc=\"{ndmi_expression}\""
    os.system(gdal_calc_cmd)
    return ndmi_band

def calculate_msavi2(nir, red, **kwargs):
    msavi2_expression = "(2 * A + 1 - sqrt((2 * A + 1)**2 - 8 * (A - B))) / 2"
    msavi2_band = "/tmp/msavi2.tif"
    gdal_calc_cmd = f"gdal_calc.py -A {nir} -B {red} --outfile={msavi2_band} --calc='{msavi2_expression}'"
    os.system(gdal_calc_cmd)
    return msavi2_band

def process_image(msavi2, ndmi, output_bucket_name):
    try:
        msavi2 = gdal.Open(msavi2)
        ndmi = gdal.Open(ndmi)

        kmeans = KMeans(n_clusters=6)
        kmeans.fit(np.column_stack((msavi2.GetRasterBand(1).ReadAsArray().ravel(), ndmi.GetRasterBand(1).ReadAsArray().ravel())))
        labels = kmeans.labels_
        unique_labels = np.unique(labels)
        labels = labels.reshape(msavi2.RasterYSize, msavi2.RasterXSize)
        logger.info(unique_labels)

        driver = gdal.GetDriverByName('GTiff')
        
        output_ds = driver.Create("/tmp/labels.tif", msavi2.RasterYSize, msavi2.RasterXSize, 1, gdal.GDT_Byte)
        output_ds.SetGeoTransform(msavi2.GetGeoTransform())
        output_ds.SetProjection(msavi2.GetProjection())
        output_ds.GetRasterBand(1).WriteArray(labels)
        output_ds = None
        
        if output_bucket_name:
            s3.upload_file('/tmp/labels.tif', output_bucket_name, 'labels.tif')
        
        return True
    except ClientError as e:
        logger.error(e)
        return False

def resample_band(input_path, x_res, y_res):
    input_ds = gdal.Open(input_path)
    
    out_path = input_path.replace('.tif', '_resampled.tif')
    
    gdal.Warp(out_path, input_ds, xRes=x_res, yRes=y_res)
    # remove input file
    os.remove(input_path)
    input_ds = None
    return out_path

def handler(event, context):
    date = event.get('date', "2024-01-01T00:00:00.000Z/2024-03-05T00:00:00.000Z")
    coords = event.get('coordinates', "31.102,36.793")
    bbox = generate_bbox_from_lat_lon(*map(float, coords.split(',')), 0.00000001)
    sentinel_handler(date, bbox)

def get_sentinel_image(date, bbox):
    url = f"https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items?limit=12&datetime={date}&bbox={bbox}"
    response = requests.get(url)
    if response.status_code == 200:
        images = response.json()["features"]
        sorted_images = sorted(images, key=lambda x: x['properties']['eo:cloud_cover'])
        one_image = sorted_images[0] if sorted_images else None
        nir =one_image["assets"]["nir"]["href"]
        swir = one_image["assets"]["swir22"]["href"]
        red = one_image["assets"]["red"]["href"]
        # download the images to /tmp
        for band in [nir, swir, red]: #use full path
            local_file = f'/tmp/{one_image["id"]}_{os.path.basename(band)}'
            if not os.path.exists(local_file):
                response = requests.get(band)
                with open(f'/tmp/{one_image["id"]}_{os.path.basename(band)}', 'wb') as f:
                    f.write(response.content)
        return {
            "nir": f'/tmp/{one_image["id"]}_B08.tif',
            "swir": f'/tmp/{one_image["id"]}_B12.tif',
            "red": f'/tmp/{one_image["id"]}_B04.tif'
        }

def sentinel_handler(date, bbox):
    sentinel_image = get_sentinel_image(date, bbox)
    if sentinel_image:
        sentinel_image['swir'] = resample_band(sentinel_image['swir'], 10, 10)
        msavi2 = calculate_msavi2(**sentinel_image)
        ndmi = calculate_ndmi(**sentinel_image)

        process_image(msavi2, ndmi, os.getenv('OUTPUT_BUCKET_NAME'))

def generate_bbox_from_lat_lon(lat, lon, radius):
    return f"{lon - radius},{lat - radius},{lon + radius},{lat + radius}"

if __name__ == "__main__":
    handler({}, {})

