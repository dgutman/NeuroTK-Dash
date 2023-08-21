"""Given a set of imageIDs this will run positive pixel count on a set of images"""
import pymongo
#from ..utils.database import mc

mc = pymongo.MongoClient('localhost',27017)
db = mc['dsaCache']  ### Attach the mongo client object to the database I want to store everything

collection = db['annotationData']


pipeline = [
    {
        "$group": {
            "_id": "$annotation.name",
            "count": {"$sum": 1}
        }
    },
    {
        "$sort": {
            "count": -1
        }
    }
]

# Execute the aggregation pipeline
results = list(collection.aggregate(pipeline))

# Print the results
for result in results:
    print(result["_id"], result["count"])
# mc['annotationData'].find_one()['annotation']['description']['params']
