# DSA settings.
import os, girder_client
from dotenv import load_dotenv
from pathlib import Path

# Load .env variables to environment.
load_dotenv(dotenv_path='src/.env', override=True)


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
token_info = gc.get('token/current')

# Find the user ID that owns the token.
try:
    for user_info in token_info['access']['users']:
        USER = gc.getUser(user_info['id'])['login']
        break
except KeyError:
    USER = 'Could not match API token to user.'

JC_WINDOWS = True
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
