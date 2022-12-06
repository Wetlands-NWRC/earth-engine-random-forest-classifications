import json
import re
from pprint import pprint
from typing import Any, Dict, List

import ee
from google.auth.transport.requests import AuthorizedSession


class DC_CreateCloudBackedAsset:
    def __init__(self, cloud_uris: List[str], session: AuthorizedSession) -> None:
        """ Used to help write cloud optimized Geotiifs to earth engine
        image collection (user defined)
        """
        self.uris = cloud_uris
        self.session = session
        self._requests_template = {
            'type': 'IMAGE',
            'gcs_location': {
                'uris': []
            },
            'properties': {
                'row': 0,
                'col': 0
            },
        }

    def extract_row_col(self, uri: str):
        None

    def requests(self) -> List[Dict[str, Any]]:
        # for each uri we want to parse out the row and col from URI
        requests = []
        for uri in self.uris:
            row, col = None, None
            input_request = self._requests_template

            # populate the template
            input_request.get('gcs_location').get('uris').\
                append(uri)

            input_request['properties']['row'] = row
            input_request['properties']['col'] = col

            requests.append(input_request)
            input_request = None

        return requests

    def post(self, requests: List[Dict[str, Any]]) -> None:
        project_folder = None
        asset_id = None
        url = 'https://earthengine.googleapis.com/v1alpha/projects/{}/assets?assetId={}'

        for request in request:
            response = self.session.post(
                url=url.format(project_folder, asset_id),
                data=json.dumps(request)
            )
            content = response.content
            pprint(json.loads(content))

            with open("response.content.txt", "ab") as file:
                file.write(content)

        return None
