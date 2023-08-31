# DSA settings.
import os, girder_client
from dotenv import load_dotenv
from pathlib import Path
import dash
import diskcache
from dash.long_callback import DiskcacheLongCallbackManager
import dash_bootstrap_components as dbc


cache = diskcache.Cache("./neurotk-cache")
lcm = DiskcacheLongCallbackManager(cache)


## This creates a single dash instance that I can access from multiple modules
class SingletonDashApp:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(SingletonDashApp, cls).__new__(cls)

            # Initialize your Dash app here
            cls._instance.app = dash.Dash(
                __name__,
                external_stylesheets=[
                    dbc.themes.BOOTSTRAP,
                    dbc.icons.FONT_AWESOME,
                ],
                title="NeuroTK Dashboard",
                long_callback_manager=lcm,
            )
        return cls._instance


### Creating a cache to allow for async callbacks
## May migrate to REDIS at some point ,for now using disk

cache = diskcache.Cache("./neurotk-cache-directory")
background_callback_manager = dash.DiskcacheManager(cache)


# app = dash.Dash(__name__)
# cache = Cache(app.server, config={
#     'CACHE_TYPE': 'diskcache.DiskCache'
# })
# long_callback_manager = DiskcacheLongCallbackManager(cache)


## Adding code that if I am not running in a docker environment, it will use different MONGO_DB Credentials
def is_docker():
    cgroup = Path("/proc/self/cgroup")
    return (
        Path("/.dockerenv").is_file()
        or cgroup.is_file()
        and "docker" in cgroup.read_text()
    )


cwd = os.getcwd()
dotenv_path = os.path.join(cwd, "src", os.getenv("ENVIRONMENT_FILE", ".env"))
load_dotenv(dotenv_path=dotenv_path, override=True)

APP_HOST = os.environ.get("HOST")
APP_PORT = int(os.environ.get("PORT", 5000))
DEV_TOOLS_PROPS_CHECK = bool(os.environ.get("DEV_TOOLS_PROPS_CHECK"))
API_KEY = os.environ.get("API_KEY", None)
USER = os.environ.get("USER", None)
DSA_BASE_URL = os.environ.get("DSA_BASE_URL", None)
ROOT_FOLDER_ID = os.environ.get("ROOT_FOLDER_ID", None)
ROOT_FOLDER_TYPE = os.environ.get("ROOT_FOLDER_TYPE", None)

PROJECTS_ROOT_FOLDER_ID = os.environ.get(
    "PROJECTS_ROOT_FOLDER_ID", "64dbd2667920606b462e5b83"
)


gc = girder_client.GirderClient(apiUrl=DSA_BASE_URL)
# JC API Key
# if debug:
#     print("Trying to connect to %s with %s " % (DSA_BASE_URL, API_KEY))
dsa_login_status = gc.authenticate(apiKey=API_KEY)

print(dsa_login_status)

JC_WINDOWS = False
if is_docker():
    MONGO_URI = os.environ.get("MONGO_URI", None)

    MONGODB_USERNAME = os.environ.get("MONGODB_USERNAME", "docker")
    MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD", "docker")
    MONGODB_HOST = os.environ.get("MONGODB_HOST", "mongodb")
    MONGODB_PORT = os.environ.get("MONGODB_PORT", 27017)
    MONGODB_DB = os.environ.get("MONGODB_DB", "dsaCache")
    APP_IN_DOCKER = True
elif JC_WINDOWS:
    MONGO_URI = "localhost"
    MONGODB_USERNAME = "docker"
    MONGODB_PASSWORD = "docker"
    MONGODB_HOST = "localhost"
    MONGODB_PORT = 27017
    MONGODB_DB = "dsaCache"
    APP_IN_DOCKER = False
else:
    MONGO_URI = "localhost"
    MONGODB_USERNAME = None
    MONGODB_PASSWORD = None
    MONGODB_HOST = "localhost"
    MONGODB_PORT = 27017
    MONGODB_DB = "dsaCache"
    APP_IN_DOCKER = False


AVAILABLE_CLI_TASKS = {
    "PositivePixelCount": {"name": "Positive Pixel Count", "dsa_name": "PPC"},
    "nft_detection": {"name": "NFT Detector", "dsa_name": "nft_detection"},
}
