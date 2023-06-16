import girder_client

# import dsa_secrets as ds  #Futre vesion with auth
import os, json
import pandas as pd
import schemaHelpers as sh


## Version one will just use a static file
# dsaApiUrl = ds.dsaApiUrl
# gc = girder_client.GirderClient(apiUrl=dsaApiUrl)
# gc.authenticate(apiKey=ds.dsaApiToken)

# collectionId = "641ba814867536bb7a225533"
## Adding a cache so I don't have to keep requerying the DSA all the time
# if not os.path.isfile("cachedItemSet.json"):
#     itemSet = gc.get(f"resource/{collectionId}/items?type=collection&limit=0")
#     with open("cachedItemSet.json", "w") as fp:
#         json.dump(itemSet, fp)
#     gc.authenticate(apiKey=ds.dsaApiToken)

# else:
print("Using cached data set")
with open("cachedItemSet.json", "r") as fp:
    itemSet = json.load(fp)

df = pd.json_normalize(itemSet)
# print(df.columns)

dataSetMetrics = {}
### Generate data set metrics..
uniquePatients = df["meta.npSchema.caseID"].unique()
dataSetMetrics["uniquePatients"] = uniquePatients

totalSlides = len(itemSet)
dataSetMetrics["totalSlides"] = totalSlides

### This is a neat trick... so I can run the dataframe against the validStainList


# print(df["meta.npSchema.stainID"].isin(sh.validStainList).sum())
# print(totalSlides)
