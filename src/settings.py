# DSA settings.
import os, girder_client

# DSA variables.
DSA_BASE_URL = "https://megabrain.neurology.emory.edu/api/v1"

# DSA_API_KEY = os.getenv("DSAKEY")

gc = girder_client.GirderClient(apiUrl=DSA_BASE_URL)

# JC API Key
gc.authenticate(apiKey="")

# Neurotk API Key
# gc.authenticate(apiKey='')

# Hard code the user for now.
USER = "jvizcar"

# ID to the Projects folder in the NeuroTK collection.
PROJECTS_FLD_ID = "64dbd2667920606b462e5b83"

# SAMPLE_PROJECT_FOLDER = "64dbd2a87920606b462e5b85"

# if DSA_API_KEY:
#     _ = gc.authenticate(apiKey=DSA_API_KEY)
#     print(_)
