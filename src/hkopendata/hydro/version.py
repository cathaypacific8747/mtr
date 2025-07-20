from datetime import datetime
from typing import List

import httpx
from pydantic_xml import BaseXmlModel, element, wrapped

from . import API_ENDPOINT, DATA_DIR, DEFAULT_PARAMS

_FP = DATA_DIR / "version.xml"


class Facility(BaseXmlModel):
    facility_key: str = element()
    facility_version: int = element()


class Layer(BaseXmlModel):
    layer_key: str = element()
    layer_version: int = element()


class PlaceName(BaseXmlModel):
    place_name_key: str = element()
    place_name_version: str = element()


# govhk.mardep.eseago.data.model.NameValuePairsX0 (UpdateBean.kt)
class Version(BaseXmlModel, tag="result"):
    """Latest metadata for tiles"""

    file_name: str = element()
    file_size: int = element()
    file_hash: str = element()
    file_version: int = element()
    file_remarks: str = element()
    file_upload_dt: datetime = element()
    xyztiles_version: int = element()
    xyztiles_upload_dt: datetime = element()
    harbour_facilities: List[Facility] = wrapped(
        "harbour_facilities", element(tag="facility")
    )
    place_name: PlaceName = element()
    thematic_layers: List[Layer] = wrapped("thematic_layers", element(tag="layer"))

    @staticmethod
    async def fetch_raw(client: httpx.AsyncClient) -> str:
        request = httpx.Request(
            "GET",
            f"{API_ENDPOINT}/check_version",
            params=DEFAULT_PARAMS,
        )
        response = await client.send(request)
        response.raise_for_status()
        return response.text

    @staticmethod
    async def download(client: httpx.AsyncClient) -> None:
        xml = await Version.fetch_raw(client)
        _FP.parent.mkdir(parents=True, exist_ok=True)
        with open(_FP, "w") as f:
            f.write(xml)

    @staticmethod
    def load() -> "Version":
        with open(_FP, "r") as f:
            return Version.from_xml(f.read())
