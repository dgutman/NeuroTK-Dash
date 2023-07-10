# notes
"""
This file is for creating a requests session so you can securely load in your api key.
We then create a session and add the api key to the header.
Depending on the API you are using, you might need to modify the value `x-api-key`.
"""

# package imports
import os
import requests
import json
import girder_client

# local imports
from .settings import DSA_BASE_Url, ROOT_FOLDER_ID, ROOT_FOLDER_TYPE

print(ROOT_FOLDER_ID)


### SIGNIFICANT CHANGE TO DO
### NEED TO USE THE girder_client API to pull all of the data instead of requests, makes life much easier

gc = girder_client.GirderClient(apiUrl=DSA_BASE_Url)


def getItemAnnotations(itemId):
    ### Given an item ID from the DSA, grabs relevant annotation data
    ## This will also have functionality to normalize/cleanup results that are stored in the annotation object
    ## For now I am focusing on pulling out the PPC data
    annotationSet = gc.get(f"annotation?itemId={itemId}")
    print(annotationSet)
    return annotationSet


def getItemSetData(num_of_items=0):
    url = f"{DSA_BASE_Url}/resource/{ROOT_FOLDER_ID}/items?type={ROOT_FOLDER_TYPE}&limit={num_of_items}"
    print(url)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        # Process the data as needed
        return data
    else:
        print("Error:", response.status_code)
        return None


def getThumbnail(imgId):
    url = f"{DSA_BASE_Url}/item/{imgId}/tiles/thumbnail"
    return url
