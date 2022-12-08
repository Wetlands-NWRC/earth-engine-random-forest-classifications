import json
import os
import re
import time
from pprint import pprint
from typing import Any, Dict, List

import ee
import yaml
from google.auth.transport.requests import AuthorizedSession


class eeCloudRequest(dict):
    def __init__(self, uri: str) -> None:
        super().__init__({
            'type': 'IMAGE',
            'gcs_location': {
                'uris': [uri]
            }
        })

    def __setitem__(self, __key: str, __value: str) -> None:
        return super(eeCloudRequest, self).__setitem__(__key, __value)


class CreateCloudBackedAsset:
    def __init__(self, session: AuthorizedSession, request: List[eeCloudRequest]) -> None:
        """ Used to help write cloud optimized Geotiifs to earth engine
        image collection (user defined)
        """
        self._session = session
        self._request = request

    def post(self, project_folder: str, asset_id: str) -> None:
        url = 'https://earthengine.googleapis.com/v1alpha/projects/{}/assets?assetId={}'

        response = self._session.post(
            url=url.format(project_folder, asset_id),
            data=json.dumps(self._request)
        )

        return response


if __name__ == '__main__':
    os.chdir(os.path.abspath(os.path.dirname(__file__)))

    with open("assets.yml") as stream:
        document: Dict[str, Any] = yaml.safe_load(stream)

    for section, config in document.items():
        for asset_config in config.values():
            row = asset_config.get('row')
            col = asset_config.get('col')

            req = eeCloudRequest(
                uri=asset_config.pop('uri')
            )

            req['properties'] = {
                'row': row,
                'col': col
            }

            asset_name = asset_config.pop('Name')

            POST = CreateCloudBackedAsset(
                session=AuthorizedSession(
                    ee.data.get_persistent_credentials()),
                request=req
            )
            response = POST.post(
                project_folder="fpca-336015",
                asset_id=f"test-collection/{asset_name}"
            )

            pprint(json.loads(response.content))

            out_dir = f'logging/{row}'
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)

            with open(f"{out_dir}/{row}-{col}-response.content.txt", 'wb') as file:
                file.write(response.content)
        time.sleep(15)
