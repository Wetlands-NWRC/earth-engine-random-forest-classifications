import os
import re

from helpers import *

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))


def main():
    infile = r"X:\archiveImagery\sentinel\sen2comp_bc_v01\reg01_williston_fill01avg\reg01\tile078095\sen2_l2a_img00fillavg_y2018y2019_t078095.tif"
    head, tail = os.path.split(infile)

    pattern = re.compile(r'\d\d\d\d\d\d')
    row = pattern.search(tail).group()[:3]
    out_dir = os.path.join('./tmp/', row)

    to_cof(
        filename=infile,
        out_dir=out_dir
    )


if __name__ == "__main__":
    os.chdir(CURRENT_DIR)
    main()
