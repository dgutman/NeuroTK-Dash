# package imports
import os
from dotenv import load_dotenv

cwd = os.getcwd()
dotenv_path = os.path.join(cwd, "src", os.getenv("ENVIRONMENT_FILE", ".env"))
load_dotenv(dotenv_path=dotenv_path, override=True)

APP_HOST = os.environ.get("HOST")
APP_PORT = int(os.environ.get("PORT", 5000))
DEV_TOOLS_PROPS_CHECK = bool(os.environ.get("DEV_TOOLS_PROPS_CHECK"))
API_KEY = os.environ.get("API_KEY", None)
DSA_BASE_Url = os.environ.get("DSA_BASE_Url", None)
MONGO_URI = os.environ.get("MONGO_URI", None)
ROOT_FOLDER_ID = os.environ.get("ROOT_FOLDER_ID", None)
ROOT_FOLDER_TYPE = os.environ.get("ROOT_FOLDER_TYPE", None)
MONGODB_USERNAME = os.environ.get("MONGODB_USERNAME", "docker")
MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD", "docker")
