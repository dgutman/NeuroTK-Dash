import pandas as pd
from flask_mongoengine import MongoEngine
from .settings import MONGO_URI, MONGODB_DB
import pymongo
from pymongo import UpdateOne, DeleteMany
from pprint import pprint
import dash_mantine_components as dmc

# initialize the app with the extension

db = MongoEngine()
## Since the annotations do not have a very rigid schema and have weird fields, not sure if I want a class or not
conn = pymongo.MongoClient(MONGO_URI)
conn = conn[MONGODB_DB]  ### Attach the mongo client object to the database I want to store everything

# NOTE: to delete specific collection from mongo, in CLI use:
# "mongo" -> "use [collection_name]" -> "db.dropDatabase()"


def getUniqueParamSets(annotationName):
    ### Given an annotationName, this will generate a list of unique parameter sets that were used for the analysis
    ### One thing to think about, not all annotations were algorithmically generated so will need to come up with logic
    ### To figure this out in the future..
    print(annotationName)

    # # Select your collection
    collection = conn["annotationData"]

    pipeline = [
        {"$match": {"annotation.name": annotationName}},
        {
            "$group": {
                "_id": {
                    "hue_value": "$annotation.description.params.hue_value",
                    "hue_width": "$annotation.description.params.hue_width",
                    "saturation_minimum": "$annotation.description.params.saturation_minimum",
                    "intensity_upper_limit": "$annotation.description.params.intensity_upper_limit",
                },
                "count": {"$sum": 1},
            }
        },
        {
            "$project": {
                "hue_value": "$_id.hue_value",
                "hue_width": "$_id.hue_width",
                "saturation_minimum": "$_id.saturation_minimum",
                "intensity_upper_limit": "$_id.intensity_upper_limit",
                "count": 1,
                "_id": 0,
            }
        },
        {"$sort": {"count": -1}},
    ]

    # Execute the aggregation pipeline
    results = list(collection.aggregate(pipeline))
    return results


def getAnnotationNameCount(projectName):
    """This will query the mongo database directly and get the distinct annotation names and the associated counts"""

    # # Select your collection
    collection = conn["annotationData"]

    # Define the aggregation pipeline
    pipeline = [
        {"$group": {"_id": "$annotation.name", "count": {"$sum": 1}}},
        {"$project": {"annotationName": "$_id", "count": 1, "_id": 0}},
        {"$sort": {"count": -1}},
    ]
    # Execute the aggregation pipeline
    results = list(collection.aggregate(pipeline))
    return results


def getUniqueParamSets(annotationName):
    ### Given an annotationName, this will generate a list of unique parameter sets that were used for the analysis
    ### One thing to think about, not all annotations were algorithmically generated so will need to come up with logic
    ### To figure this out in the future..
    print(annotationName)
    # # Select your collection
    collection = conn["annotationData"]

    pipeline = [
        {"$match": {"annotation.name": annotationName}},
        {
            "$group": {
                "_id": {
                    "hue_value": "$annotation.description.params.hue_value",
                    "hue_width": "$annotation.description.params.hue_width",
                    "saturation_minimum": "$annotation.description.params.saturation_minimum",
                    "intensity_upper_limit": "$annotation.description.params.intensity_upper_limit",
                },
                "count": {"$sum": 1},
            }
        },
        {
            "$project": {
                "hue_value": "$_id.hue_value",
                "hue_width": "$_id.hue_width",
                "saturation_minimum": "$_id.saturation_minimum",
                "intensity_upper_limit": "$_id.intensity_upper_limit",
                "count": 1,
                "_id": 0,
            }
        },
        {"$sort": {"count": -1}},
    ]

    # Execute the aggregation pipeline
    results = list(collection.aggregate(pipeline))

    return results


def getAnnotationNameCount(projectName):
    """This will query the mongo database directly and get the distinct annotation names and the associated counts"""

    # # Select your collection
    collection = conn["annotationData"]

    # Define the aggregation pipeline
    pipeline = [
        {"$group": {"_id": "$annotation.name", "count": {"$sum": 1}}},
        {"$project": {"annotationName": "$_id", "count": 1, "_id": 0}},
        {"$sort": {"count": -1}},
    ]
    # Execute the aggregation pipeline
    results = list(collection.aggregate(pipeline))
    return results


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def upsert_dsa_container_structure(containers):
    ops = []
    for container in containers:
        ops.append(UpdateOne({"_id": container["_id"]}, {"$set": container}, upsert=True))

    for chunk in chunks(ops, 500):
        result = conn["dsa_container_structure"].bulk_write(chunk)

    return result

def get_dsa_container_structure(filters=None):
    container_structure = list(conn["dsa_container_structure"].find({}))
    return container_structure

def insertAnnotationData(annotationItems, projectName, debug=False):
    ### This will insert all of the annotations pulled from the DSA and also insert a projectName to keep things bundled/separate
    ## Add the projectName to all of the annotations as well
    annotationItems = [dict(item, **{"projectName": projectName}) for item in annotationItems]
    ### The collection for annotations is called.. annotations!
    print(len(annotationItems), "to be inserted or upserted into the mongo table..")
    ## See this:
    ## print(len(annot)) returns 4099
    ## len(set(x["_id"] for x in annot)) returns 1814

    ## So here's some confusion.. the annotationItems can return many more annotations than actually exist...
    ## Because an annotation can be copied between items.. meaning the same annotation is associated with many images..

    operations = []
    for a in annotationItems:
        operations.append(UpdateOne({"_id": a["_id"]}, {"$set": a}, upsert=True))
    for chunk in chunks(operations, 500):
        result = conn["annotationData"].bulk_write(chunk)
        if debug:
            pprint(result.bulk_api_result)
    return result


def getAnnotationData_fromDB(projectName, filters=None):
    ## Can add additional filters to mongo query in the future other than projctName
    annotationData = list(conn["annotationData"].find({}))
    return annotationData


class Records(db.Document):
    _id = db.StringField()
    name = db.StringField()
    blockID = db.StringField()
    caseID = db.StringField()
    regionName = db.StringField()
    stainID = db.StringField()

    def to_dict(self):
        return {
            "_id": self._id,
            "name": self.name,
            "blockID": self.blockID,
            "caseID": self.caseID,
            "regionName": self.regionName,
            "stainID": self.stainID,
        }


def insert_records(records):
    Records.objects().delete()
    for record in records:
        _id = record["_id"]
        name = record["name"]
        blockID = str(record["blockID"]) if not pd.isna(record["blockID"]) else None
        caseID = str(record["caseID"]) if not pd.isna(record["caseID"]) else None
        regionName = str(record["regionName"]) if not pd.isna(record["regionName"]) else None
        stainID = str(record["stainID"]) if not pd.isna(record["stainID"]) else None

        record_obj = Records(
            _id=_id,
            name=name,
            blockID=blockID,
            caseID=caseID,
            regionName=regionName,
            stainID=stainID,
        )
        record_obj.save()
    print("Records inserted successfully")


def get_all_records_df():
    records = Records.objects.all()
    records = [record.to_dict() for record in records]
    df = pd.DataFrame(records)
    return df
