from pathlib import Path
from typing import AsyncGenerator

import aiofiles
import httpx
from pydantic_xml import BaseXmlModel, element
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from . import API_ENDPOINT, DEFAULT_PARAMS


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

        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task("Downloading", total=content_length)
            async for chunk in response.aiter_bytes():
                yield chunk
                progress.update(
                    task, advance=response.num_bytes_downloaded - bytes_downloaded
                )
                bytes_downloaded = response.num_bytes_downloaded

    @staticmethod
    async def download(client: httpx.AsyncClient, fp: Path) -> None:
        async with aiofiles.open(fp, "wb") as f:
            async for chunk in OfflineTiles.fetch(client):
                await f.write(chunk)
