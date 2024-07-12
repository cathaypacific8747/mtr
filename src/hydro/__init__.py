from pathlib import Path

# govhk.mardep.eseago.BuildConfig
API_ENDPOINT = "https://eseago.hydro.gov.hk/v2"
VERSION = "3.0.23"
# govhk.mardep.eseago.eSeaGoApp$Companion.initialize
DEFAULT_PARAMS = {"token": "eseago", "app_version": VERSION, "os": "android"}

DATA_DIR = Path(__file__).parent / "data"
