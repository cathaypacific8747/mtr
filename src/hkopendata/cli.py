from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import rich
import typer
from rich.logging import RichHandler

logging.basicConfig(
    level="INFO", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    help="A CLI for working with open geospatial data in Hong Kong.",
)


@app.command()
def hydro_download() -> None:
    """Download hydro tiles"""
    import httpx

    from .cache import PATH_CACHE
    from .hydro.tiles import OfflineTiles
    from .hydro.version import Version

    async def main() -> None:
        async with httpx.AsyncClient() as client:
            await Version.download(client)
            metadata = Version.load()
            rich.print(metadata)
            fp = PATH_CACHE / "hydro" / metadata.file_name
            await OfflineTiles.download(client, fp)

    asyncio.run(main())


@app.command()
def ocf_download(path_base: Path | None = None) -> None:
    """Download hourly and daily weather data"""
    from .cache import PATH_CACHE
    from .weather import run

    asyncio.run(run.ocf_download(path_base or PATH_CACHE / "ocf_runs"))


@app.command()
def ocf_plot_hourly_wind(path_base: Path | None = None) -> None:
    """Plot hourly wind data"""
    from .cache import PATH_CACHE
    from .weather import run

    run.ocf_plot_hourly_wind(path_base or PATH_CACHE / "ocf_runs")


if __name__ == "__main__":
    app()
