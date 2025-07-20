import os
from pathlib import Path

from appdirs import user_cache_dir

PATH_CACHE = Path(user_cache_dir("hkopendata"))
if cache_path := os.environ.get("XDG_CACHE_HOME"):
    PATH_CACHE = Path(cache_path) / "hkopendata"
