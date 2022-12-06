from dataclasses import dataclass


@dataclass
class CFG:
    gcp_root: str = None
    ee_asset: str = None
    project_folder = None
