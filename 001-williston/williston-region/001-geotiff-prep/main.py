from helpers import *
from config import CFG
import os
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.append(".")


CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))


def main():
    pattern = CFG.pattern
    search_dir = CFG.tiles

    row_indexs = get_row_idxs(
        top=search_dir
    )

    tiles_x_rows = get_tile_by_row(
        row_indexs=row_indexs,
        target_dir=search_dir,
        glob_pattern=pattern
    )

    print(f"\n{'Starting Conversion':#^30}")
    with ProcessPoolExecutor() as executor:
        for rows, tifs in tiles_x_rows.items():
            print(f"Row: {rows}")
            out = [os.path.join('tmp', f'{str(rows)}')
                   for _ in range(len(tifs))]
            executor.map(to_cof, tifs, out)


if __name__ == '__main__':
    os.chdir(CURRENT_DIR)
    main()
