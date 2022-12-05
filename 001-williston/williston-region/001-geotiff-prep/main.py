import glob
import os
import re
import time
from abc import ABC
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Set, Union

import numpy as np
import yaml
from osgeo import gdal


class Tool(ABC):
    pass


class TileToCOG(Tool):
    def __init__(self, config_filename: str) -> None:
        """A Tool class that is used to convert data cube tiles to cloud optimized tiffs.
        The tool will group the tiles by row (the first 3 numbers in the tile id), then will iteratively go over 
        each row converting all images in that row to COG. Will create a output folder struct that mimics the input data struct of
        {rowIdx: [tiles, ...]}. See example below for conceptual diagram

        the directory needs to be in this format

        Example:
        --------

        input dir struct
        root:
            tile001001 \
                tile001001.tif
            tile001002 \
                tile001002.tif
            tile002001 \
                tile002001.tif
            tile002002\
                tile002002.tif

        output dir struct
        tmp\
            001 (row index)\
                tile001001.tif
                tile001002.tif
            002\
                tile002001.tif
                tile002002.tif

        Note: tile<6 digit number>: the number refers to its x,y position in the grid
        given tile001001, means this tile it at x = 001 row 1, y = 001 col 1


        Args:
            config_filename (str): _description_
        """
        super().__init__()
        self.config_filename = config_filename

        # get a unique list of row idxs
        indexs = self.get_row_idxs()

        # format a dict to store all tiles that correspond to the row
        tiles = self.get_tile_by_row()

        for row, tiles in tiles.items():
            out_dir = [row for _ in range(len(tiles))]
            with ProcessPoolExecutor() as executor:
                executor.map(self.as_cog, tiles, out_dir)
            time.sleep(3)

    def get_row_idxs(self, top: str) -> Set[str]:
        """ returns a unique list of row indexs from the second level of the input dir """
        pattern = re.compile(r'\d\d\d')
        dirs = next(os.walk(top))[1]
        row_idxs = set([pattern.search(tile_dir).group(1) for tile_dir in dirs])
        return row_idxs

    def get_tile_by_row(self, row_indexs: List[str]) -> Dict[str, List[str]]:
        obj = {}
        for dirname, dirnames, filenames in os.walk(path):
            pass

    def as_cog(self, filename: str, out_dir: str = None):
        """Helper method that converts a single Geotiff to COG format. The output filename will be the same as the 
        input but will have the suffix _cog appended to the string. 

        Args:
            filename (str): the file name that represents the geotiff that is to be converted
            out_dir(str): the output destination
        """
        out_dir = 'tmp' if out_dir is None else out_dir

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


def dir_list(root: str):
    pass


def restructure_path(glob: List[str], tile_ids: Set):
    splits = [os.path.split(i) for i in glob]
    paths = []
    for tile_id in tile_ids:
        for head, tail in splits:
            if tile_id in head:
                paths.append(os.path.join(head, tail))

    return paths


def to_cof(filename: str, out_dir: str = None) -> None:
    # set default value
    out_dir = 'tmp' if out_dir is None else out_dir

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
