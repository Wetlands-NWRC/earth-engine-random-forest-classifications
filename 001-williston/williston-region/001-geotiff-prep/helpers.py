import glob
import os
import re
import time
from typing import Dict, List, Set, Union

from osgeo import gdal


def get_row_idxs(top: str) -> Set[str]:
    """ returns a unique list of row indexs from the second level of the input dir """
    pattern = re.compile(r'\d\d\d\d\d\d')
    dirs = next(os.walk(top))[1]
    row_idxs = set([pattern.search(tile_dir).group()[:3]
                    for tile_dir in dirs])
    return row_idxs


def get_tile_by_row(row_indexs: Set[str], target_dir: str,
                    glob_pattern: str) -> Dict[str, List[str]]:
    obj = {idx: [] for idx in row_indexs}

    pattern = os.path.join(target_dir, glob_pattern)
    tifs = glob.glob(pattern, recursive=True)

    for index, array in obj.items():
        for tif in tifs:
            head, tail = os.path.split(tif)
            idx_pattern = re.compile(r'\d\d\d\d\d\d')
            dest_idx = idx_pattern.search(tail).group()[:3]
            if index == dest_idx:
                array.append(tif)
    return obj


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
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

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
