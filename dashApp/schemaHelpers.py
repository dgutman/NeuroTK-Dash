import json


### To avoid editing multiple places for the same keys/values , so this will yield
### either values, for example I am going to get the enumerated list of stainIDs as my first example


schemaFile = "adrcNpSchema.json"

with open(schemaFile, "r") as fp:
    jsSchema = json.load(fp)

# print(jsSchema)

validStainList = jsSchema["properties"]["npSchema"]["properties"]["stainID"]["enum"]
print(validStainList)
