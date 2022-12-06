import os

import toolbox

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))


def main() -> int:
    tool = toolbox.TileToCOG()
    return 0


if __name__ == "__main__":
    os.chdir(CURRENT_DIR)
    main()
