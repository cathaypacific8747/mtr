from typing import AsyncGenerator

import aiofiles
import httpx
from pydantic_xml import BaseXmlModel, element
from tqdm import tqdm

from . import API_ENDPOINT, DATA_DIR, DEFAULT_PARAMS


class _OfflineTilesVersion(BaseXmlModel, tag="result"):
    file_path: str = element()
    file_key: str = element()

    @staticmethod
    async def fetch(client: httpx.AsyncClient) -> str:
        response = await client.get(
            f"{API_ENDPOINT}/map_download", params=DEFAULT_PARAMS
        )
        response.raise_for_status()
        return response.text

    @property
    def request(self) -> httpx.Request:
        return httpx.Request("GET", self.file_path + "?" + self.file_key)


class OfflineTiles:
    @staticmethod
    async def fetch(client: httpx.AsyncClient) -> AsyncGenerator[bytes, None]:
        request = _OfflineTilesVersion.from_xml(
            await _OfflineTilesVersion.fetch(client)
        ).request
        response = await client.send(
            request=request,
            stream=True,
        )
        response.raise_for_status()
        content_length = int(response.headers["Content-Length"])
        bytes_downloaded = response.num_bytes_downloaded
        with tqdm(total=content_length, unit="B", unit_scale=True) as pbar:
            async for chunk in response.aiter_bytes():
                yield chunk
                pbar.update(response.num_bytes_downloaded - bytes_downloaded)
                bytes_downloaded = response.num_bytes_downloaded

    @staticmethod
    async def download(client: httpx.AsyncClient, file_name: str) -> None:
        async with aiofiles.open(DATA_DIR / file_name, "wb") as f:
            async for chunk in OfflineTiles.fetch(client):
                await f.write(chunk)
