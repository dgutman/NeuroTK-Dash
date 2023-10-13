# DSA settings.
import os, girder_client
from dotenv import load_dotenv
from pathlib import Path
import pymongo

import dash
import diskcache
from dash.long_callback import DiskcacheLongCallbackManager
import dash_bootstrap_components as dbc


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


cache = diskcache.Cache("./src/neurotk-cache")
lcm = DiskcacheLongCallbackManager(cache)

cache = diskcache.Cache("./neurotk-cache-directory")
background_callback_manager = dash.DiskcacheManager(cache)


# Load .env variables to environment.
load_dotenv(dotenv_path="src/.env", override=True)


def is_docker():
    """
    Adding code that if I am not running in a docker environment, it will use
    different MONGO_DB Credentials.
    """
    cgroup = Path("/proc/self/cgroup")
    return (
        Path("/.dockerenv").is_file()
        or cgroup.is_file()
        and "docker" in cgroup.read_text()
    )


APP_HOST = os.environ.get("HOST")
APP_PORT = int(os.environ.get("PORT", 5000))
DEV_TOOLS_PROPS_CHECK = bool(os.environ.get("DEV_TOOLS_PROPS_CHECK"))
API_KEY = os.environ.get("API_KEY", None)
DSA_BASE_URL = os.environ.get("DSA_BASE_URL", None)
ROOT_FOLDER_ID = os.environ.get("ROOT_FOLDER_ID", None)
ROOT_FOLDER_TYPE = os.environ.get("ROOT_FOLDER_TYPE", None)

PROJECTS_ROOT_FOLDER_ID = os.environ.get(
    "PROJECTS_ROOT_FOLDER_ID", "64dbd2667920606b462e5b83"
)

# Authenticate a girder client from API token in .env.
gc = girder_client.GirderClient(apiUrl=DSA_BASE_URL)
gc.authenticate(apiKey=API_KEY)

# Get the information from current token.
token_info = gc.get("token/current")

# Find the user ID that owns the token.
try:
    for user_info in token_info["access"]["users"]:
        user = gc.getUser(user_info["id"])
        USER = user["login"]
        USER_IS_ADMIN = user["admin"]
        break
except KeyError:
    USER = "Could not match API token to user."
    USER_IS_ADMIN = False

if is_docker():
    MONGO_URI = os.environ.get("MONGO_URI", None)

    MONGODB_USERNAME = os.environ.get("MONGODB_USERNAME", "docker")
    MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD", "docker")
    MONGODB_HOST = os.environ.get("MONGODB_HOST", "mongodb")
    MONGODB_PORT = os.environ.get("MONGODB_PORT", 27017)
    MONGODB_DB = os.environ.get("MONGODB_DB", "dsaCache")
    APP_IN_DOCKER = True
elif os.environ.get("WINDOWS", None):
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
    "TissueSegmentation": {
        "name": "TissueSegmentation",
        "dsa_name": "TissueSegmentation",
    },
    "TissueSegmentation": {
        "name": "TissueSegmentation",
        "dsa_name": "TissueSegmentation",
    },
    "NFTDetection": {"name": "NFTDetection", "dsa_name": "NFTDetection"},
}

## Move database connection to here
mongoConn = pymongo.MongoClient(
    MONGO_URI, username=MONGODB_USERNAME, password=MONGODB_PASSWORD
)
dbConn = mongoConn[
    MONGODB_DB
]  ### Attach the mongo client object to the database I want to store everything
## dbConn is a connection to the dsaCache database
