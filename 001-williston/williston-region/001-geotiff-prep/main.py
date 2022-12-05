import glob
import os
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Set, Union

import numpy as np
import yaml
from osgeo import gdal


def set_out_file(dir: str, filename: str) -> str:
    head, tail = os.path.split(filename)
    new_name, ext = tail.split(".")
    new_name = new_name + '_cog.tif'
    return os.path.join(dir, new_name)


def difference_files(left: List[str], right: List[str]) -> Union[Set[str], None]:
    def fmt(element):
        head, tail = os.path.split(element)
        trim = tail.replace('.tif', '').replace('_cog', '')
        return trim.split("t")[-1]

    left_set, right_set = set(map(fmt, left)), set(map(fmt, right))

    dif = left_set ^ right_set
    return dif


def restructure_path(glob: List[str], tile_ids: Set):
    splits = [os.path.split(i) for i in glob]
    paths = []
    for tile_id in tile_ids:
        for head, tail in splits:
            if tile_id in head:
                paths.append(os.path.join(head, tail))

    return paths


def to_cof(filename: str, out_dir: str = 'tmp') -> None:
    # load the data
    raster: gdal.Dataset = gdal.Open(filename)
    x_size = raster.RasterXSize
    y_size = raster.RasterYSize
    n_bands = raster.RasterCount
    gt = raster.GetGeoTransform()
    proj = raster.GetProjection()
    array: np.array = raster.ReadAsArray()

    # grab the driver
    driver: gdal.Driver = gdal.GetDriverByName("GTiff")
    options = [
        "TILED=YES",
        "COMPRESS=LZW",
        "INTERLEAVE=BAND"
    ]

    # create the output image to have values burned into
    file_name_out = set_out_file(out_dir, filename)

    data_set: gdal.Dataset = driver.Create(file_name_out, x_size, y_size, n_bands, gdal.GDT_Float32,
                                           options=options)
    data_set.SetGeoTransform(gt)
    data_set.SetProjection(proj)

    # burn values
    for i in range(n_bands):
        #####
        out_band: gdal.Band = data_set.GetRasterBand(i + 1)
        out_band.WriteArray(array[i])
        data_set.BuildOverviews("NEAREST", [2, 4, 8, 16, 32, 64])
        out_band = None
        #####
    data_set = None
    print(f"{file_name_out}: converted to COG...")


if __name__ == '__main__':
    current_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(current_dir)

    with open("./config.yml", 'r') as stream:
        cfg: Dict[str, Dict[str, str]] = yaml.safe_load(stream)

    defults = cfg['Defults']
    search_dir = defults.get('input')
    tmp = defults.get('output')
    pattern = defults.get('pattern')

    tifs: List[str] = glob.glob(f"{search_dir}{pattern}")

    if not os.path.exists(tmp):
        os.mkdir(tmp)
    else:
        contents = glob.glob(f'{tmp}/*.tif')
        diff = difference_files(tifs, contents)
        tifs = restructure_path(tifs, diff)

    ####
    start = time.perf_counter()

    with ProcessPoolExecutor() as executor:
        executor.map(to_cof, tifs)

    end = time.perf_counter()
    print(f'Finished in {round(end - start, 2)} seconds')
