from dataclasses import dataclass


@dataclass
class CFG:
    tiles: str = r"X:\archiveImagery\sentinel\sen2comp_bc_v01\reg01_williston_fill01avg\reg01"
    pattern: str = "**/*.tif"
