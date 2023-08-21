# Global variables.
import os, girder_client

# URL to the API of the DSA instance being used.
DSA_API_URL = "https://megabrain.neurology.emory.edu/api/v1"

# Authenticate girder client.
gc = girder_client.GirderClient(apiUrl=DSA_API_URL)

### DEVEL ###
DSA_API_KEY = os.getenv("DSAKEY")

gc.authenticate(apiKey=DSA_API_KEY)
USER = "jvizcar"
PROJECTS_FLD_ID = "64dbd2667920606b462e5b83"
