import boto3
import os
import logging
from urllib.parse import unquote_plus
from botocore.exceptions import ClientError
from sklearn.cluster import OPTICS
import numpy as np
from osgeo import gdal
import requests

s3 = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def create_ndmi_array(tif_file):
    ds = gdal.Open(tif_file)
    nir_band = ds.GetRasterBand(8).ReadAsArray()
    swir_band = ds.GetRasterBand(12).ReadAsArray()
    ndmi = (nir_band - swir_band) / (nir_band + swir_band)
    return ndmi

def create_msavi2_array(tif_file):
    ds = gdal.Open(tif_file)
    red_band = ds.GetRasterBand(4).ReadAsArray()
    nir_band = ds.GetRasterBand(8).ReadAsArray()
    msavi2 = (2 * nir_band + 1 - np.sqrt((2 * nir_band + 1)**2 - 8 * (nir_band - red_band))) / 2
    return msavi2

def process_image(source_type, source_path, output_bucket_name=None):
    try:
        if source_type == 's3':
            download_path = f'/tmp/{os.path.basename(source_path)}'
            s3.download_file(source_path, download_path)
        elif source_type == 'local':
            download_path = source_path
        else:
            logger.error("Invalid source type")
            return False
        
        msavi2 = create_msavi2_array(download_path)
        ndmi = create_ndmi_array(download_path)
        optics = OPTICS(min_samples=10, xi=.05, min_cluster_size=.05)
        optics.fit(np.column_stack((msavi2.flatten(), ndmi.flatten())))
        labels = optics.labels_
        unique_labels = np.unique(labels)
        logger.info(unique_labels)
        logger.info(labels)
        ds = gdal.Open(download_path)
        driver = gdal.GetDriverByName('GTiff')
        output_path = f'/tmp/{os.path.basename(source_path)}'
        output_ds = driver.Create(output_path, ds.RasterXSize, ds.RasterYSize, 1, gdal.GDT_Byte)
        output_ds.SetGeoTransform(ds.GetGeoTransform())
        output_ds.SetProjection(ds.GetProjection())
        output_ds.GetRasterBand(1).WriteArray(labels.reshape(ds.RasterYSize, ds.RasterXSize))
        output_ds = None
        
        if source_type == 's3' and output_bucket_name:
            s3.upload_file(output_path, output_bucket_name, os.path.basename(source_path))
        
        return True
    except ClientError as e:
        logger.error(e)
        return False

def handler(event, context):
    logger.info(event)
    logger.info(context)
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        process_image('s3', f'{bucket}/{key}', os.environ.get('OUTPUT_BUCKET_NAME'))




def get_sentinel_images(date, bbox):
    url = f"https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items?limit=12&datetime={date}&bbox={bbox}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to retrieve Sentinel images. Status code: {response.status_code}")
        return None

def sentinel_handler(event, context):
    logger.info(event)
    logger.info(context)
    date = "2024-01-01T00:00:00.000Z/2024-03-05T00:00:00.000Z"
    bbox = "31.04942321777344,36.791140738852704,31.25541687011719,36.90103821354626"
    sentinel_images = get_sentinel_images(date, bbox)
    if sentinel_images:
        for image in sentinel_images:
            source_path = image['path']
            process_image('s3', source_path, os.environ.get('OUTPUT_BUCKET_NAME'))


if __name__ == "__main__":
    process_image('local', '/path/to/input-image.tif')

    
