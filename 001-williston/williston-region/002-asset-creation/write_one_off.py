import json
import os
import re
from pprint import pprint

import asset
import ee
from config import CFG
from google.auth.transport.requests import AuthorizedSession

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))


def main():
    session = AuthorizedSession(ee.data.get_persistent_credentials())
    ee_asset = CFG.ee_collection
    destination = CFG.project_folder
    URIS = [
        "gs://ee-cloud-backed-assests/williston-basin-cogs/090/sen2_l2a_img00fillavg_y2018y2019_t090074_cog.tif",
        "gs://ee-cloud-backed-assests/williston-basin-cogs/078/sen2_l2a_img00fillavg_y2018y2019_t078095_cog.tif"
    ]
    for uri in URIS:
        head, tail = os.path.split(uri)
        name = tail.split(".tif")[0]
        index = re.compile(r"\d\d\d\d\d\d").search(uri).group()
        row, col = index[:3], index[3:]
        request = asset.eeCloudRequest(uri)
        request['properties'] = {
            'row': int(row),
            'col': int(col)
        }

        POST = asset.CreateCloudBackedAsset(
            session=session,
            request=request
        )

        response = POST.post(
            project_folder=destination,
            asset_id=f"{ee_asset}/{name}"
        )
        pprint(json.loads(response.content))

        out_dir = f'logging/{row}'
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        with open(f"{out_dir}/{row}-{col}-response.content.txt", 'wb') as file:
            file.write(response.content)


if __name__ == "__main__":
    os.chdir(CURRENT_DIR)
    main()
