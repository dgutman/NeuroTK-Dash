# package imports
import os
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
DSA_BASE_Url = os.environ.get("DSA_BASE_Url", None)
ROOT_FOLDER_ID = os.environ.get("ROOT_FOLDER_ID", None)
ROOT_FOLDER_TYPE = os.environ.get("ROOT_FOLDER_TYPE", None)

if is_docker():
    MONGO_URI = os.environ.get("MONGO_URI", None)

    MONGODB_USERNAME = os.environ.get("MONGODB_USERNAME", "docker")
    MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD", "docker")
    MONGODB_HOST = os.environ.get("MONGODB_HOST", "mongodb")
    MONGODB_PORT = os.environ.get("MONGODB_PORT", 27017)
    MONGODB_DB = os.environ.get("MONGODB_DB", "dsaCache")
    APP_IN_DOCKER = True

else:
    MONGO_URI = "localhost"
    MONGODB_USERNAME = None
    MONGODB_PASSWORD = None
    MONGODB_HOST = "localhost"
    MONGODB_PORT = 27017
    MONGODB_DB = "dsaCache"
    APP_IN_DOCKER = False


## Create a single dictionary containing all the MONGODB_SETTINGS
MONGODB_SETTINGS = {
    "host": MONGODB_HOST,
    "username": MONGODB_USERNAME,
    "password": MONGODB_PASSWORD,
    "port": int(MONGODB_PORT),
    "db": MONGODB_DB,
}  # Replace with your MongoDB connection URI


AVAILABLE_CLI_TASKS = {
    "PositivePixelCount": {"name": "Positive Pixel Count", "dsa_name": "PPC"},
    "nft_detection": {"name": "NFT Detector", "dsa_name": "nft_detection"},
}
