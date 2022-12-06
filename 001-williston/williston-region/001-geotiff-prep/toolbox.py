import glob
import os
import re
import time
from abc import ABC
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Set

import numpy as np
import yaml
from osgeo import gdal


class Tool(ABC):
    pass


class TileToCOG(Tool):
    def __init__(self, input_dir: str, glob_pattern: str, tmp_dir: str = None) -> None:
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
                tile001001_cog.tif
                tile001002_cog.tif
            002\
                tile002001_cog.tif
                tile002002_cog.tif

        Note: tile<6 digit number>: the number refers to its x,y position in the grid
        given tile001001, means this tile it at x = 001 row 1, y = 001 col 1


        Args:
            config_filename (str): _description_
        """
        super().__init__()

        ###############################################
        #             Helper Functions                #
        ###############################################

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

        def as_cog(filename: str, out_dir: str = None):
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

        ################################################
        #         Tool Protocol Starts Here            #
        ################################################

        # set defualts
        tmp_dir = 'dump' if tmp_dir is None else tmp_dir

        indexs = get_row_idxs(
            top=input_dir
        )

        tiles = get_tile_by_row(
            row_indexs=indexs,
            target_dir=input_dir,
            glob_pattern=glob_pattern
        )

        if not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)

        for row, tiles in tiles.items():
            print(f"Converting: {row}")
            out_dirs = [os.path.join(self._dump, _) for _ in range(len(row))]
            with ProcessPoolExecutor() as exec:
                exec.map(as_cog, tiles, out_dirs)
            out_dirs = None
            time.sleep(3)
        print(f"Tool Exits")
