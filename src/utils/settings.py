# DSA settings.
import os, girder_client
from dotenv import load_dotenv
from pathlib import Path


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
gc.authenticate(apiKey=API_KEY)

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
