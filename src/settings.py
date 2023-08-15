import os, json, girder_client

DSA_BASE_URL = "https://megabrain.neurology.emory.edu/api/v1"

DSA_API_KEY = os.getenv("DSAKEY")
SAMPLE_PROJECT_FOLDER = "64dbd2a87920606b462e5b85"
DEBUG_MODE = True

gc = girder_client.GirderClient(apiUrl=DSA_BASE_URL)

if DSA_API_KEY:
    _ = gc.authenticate(apiKey=DSA_API_KEY)
    print(_)
