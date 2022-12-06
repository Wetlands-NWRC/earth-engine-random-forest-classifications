import os

import toolbox
from config import CFG

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))


def main() -> int:

    pattern = CFG.pattern
    tiles_dir = CFG.tiles

    toolbox.TileToCOG(
        input_dir=tiles_dir,
        glob_pattern=pattern
    )
    return 0


if __name__ == "__main__":
    os.chdir(CURRENT_DIR)
    main()
