import httpx
import rich

from .tiles import OfflineTiles
from .version import Version


async def main() -> None:
    async with httpx.AsyncClient() as client:
        await Version.download(client)
        metadata = Version.load()
        rich.print(metadata)
        await OfflineTiles.download(client, metadata.file_name)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
