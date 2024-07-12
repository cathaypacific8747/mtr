import httpx
import rich

from .tiles import OfflineTiles, _OfflineTilesVersion
from .version import Version


async def main():
    async with httpx.AsyncClient() as client:
        # await Version.download(client)
        # metadata = Version.load()
        # rich.print(metadata)
        # x = await _OfflineTilesVersion.fetch(client)
        # rich.print(_OfflineTilesVersion.from_xml(x).request)
        await OfflineTiles.download(client)


if __name__ == "__main__":
    import asyncio

    response = asyncio.run(main())
