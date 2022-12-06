from dataclasses import dataclass


@dataclass
class CFG:
    tiles: str = r"P:\projects\williston-testing\reg01"
    pattern: str = "**/*.tif"
    output: str = "./dump"
