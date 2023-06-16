""" This will host functions related to pulling/pushing data from either girder servers
or from a local cache """
import girder_client
import pymongo

# https://github.com/Coding-with-Adam/Dash-by-Plotly/tree/master/Dash%20Components
### Will currently use wsi-deid as main server for cacheing since it's public..

## Create a database client to the mongodb container

## The name of the server is dependent on the name of the service defined in the
## docker-compose file
client = pymongo.MongoClient("mongodb", 27017)

dbName = "mongodash"  ## Name of the database in mongo I'll be using
