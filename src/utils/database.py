import pandas as pd
from flask_mongoengine import MongoEngine
from pprint import pprint
from typing import List

import pymongo
from pymongo import UpdateOne

from ..utils.settings import (
    MONGO_URI, MONGODB_DB, MONGODB_USERNAME, MONGODB_PASSWORD, USER, gc
)
from ..utils.api import get_thumbnail_as_b64, get_neuroTK_projectDatasets, get_projects

db = MongoEngine()
mc = pymongo.MongoClient(
    MONGO_URI, username=MONGODB_USERNAME, password=MONGODB_PASSWORD
)
mc = mc[
    MONGODB_DB
]  ### Attach the mongo client object to the database I want to store everything

# NOTE: to delete specific collection from mongo, in CLI use:
# "mongo" -> "use [collection_name]" -> "db.dropDatabase()"
# or mc.collection.drop()


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def upsert_image_records(records):
    ops = []
    for record in records:
        ops.append(UpdateOne({"_id": record["_id"]}, {"$set": record}, upsert=True))

    for chunk in chunks(ops, 500):
        result = mc["image_cache"].bulk_write(chunk)

    return result


def upsert_single_image_record(record):
    mc["image_cache"].bulk_write(
        [UpdateOne({"_id": record["_id"]}, {"$set": record}, upsert=True)]
    )


def get_records_with_images():
    image_records = list(mc["image_cache"].find({"thumbnail": {"$exists": "true"}}))
    return image_records


def fetch_and_cache_image_thumb(imageId):
    if item := list(
        mc["image_cache"].find(
            {"$and": [{"_id": imageId}, {"thumbnail": {"$exists": "true"}}]}
        )
    ):
        thumb = item[0]["thumbnail"]

    else:
        thumb = get_thumbnail_as_b64(item_id=imageId)

        record = {"_id": imageId, "thumbnail": thumb}
        upsert_single_image_record(record)

    return thumb


# -------------------------------------------------------------------------------------------------


def getUniqueParamSets(annotationName):
    ### Given an annotationName, this will generate a list of unique parameter sets that were used for the analysis
    ### One thing to think about, not all annotations were algorithmically generated so will need to come up with logic
    ### To figure this out in the future..
    # # Select your collection
    collection = mc["annotationData"]

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


def getUniqueParamSets(annotationName):
    ### Given an annotationName, this will generate a list of unique parameter sets that were used for the analysis
    ### One thing to think about, not all annotations were algorithmically generated so will need to come up with logic
    ### To figure this out in the future..
    # # Select your collection
    collection = mc["annotationData"]

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
    collection = mc["annotationData"]

    # Define the aggregation pipeline
    pipeline = [
        {
            "$group": {
                "_id": "$annotation.name",
                "total": {"$sum": 1},
                "with_elements": {
                    "$sum": {
                        "$cond": [{"$ifNull": ["$annotation.elements", False]}, 1, 0]
                    }
                },
            }
        },
        {
            "$project": {
                "annotationName": "$_id",
                "count": "$total",
                "count_with_elements": "$with_elements",
                "_id": 0,
            }
        },
    ]

    # s# # Execute the aggregation pipeline
    results = list(collection.aggregate(pipeline))
    return results


def getElementSizeForAnnotations(annotation):
    """Not Named well, but this will get the sum of the lengths of the elements.points arrays in all of the annotation documents"""
    # Define the aggregation pipeline
    collection = mc["annotationData"]
    pipeline = [
        {"$match": {"annotation.name": "gray-matter-fixed"}},
        {
            "$project": {
                "annotationName": 1,
                "totalPoints": {
                    "$cond": [
                        {
                            "$and": [
                                {"$isArray": "$annotation.elements"},
                                {"$gt": [{"$size": "$annotation.elements"}, 0]},
                            ]
                        },
                        {
                            "$sum": {
                                "$map": {
                                    "input": "$annotation.elements",
                                    "as": "element",
                                    "in": {
                                        "$cond": [
                                            {"$isArray": "$$element.points"},
                                            {"$size": "$$element.points"},
                                            0,
                                        ]
                                    },
                                }
                            }
                        },
                        0,
                    ]
                },
            }
        },
    ]

    # Execute the aggregation pipeline
    results = list(collection.aggregate(pipeline))

    totalPointCounts = []
    print(results[0])
    # Print or further process the results
    for result in results:
        print(f"Document ID: {result['_id']}, Total Points: {result['totalPoints']}")
        totalPointCounts.append(int(result["totalPoints"]))
    return totalPointCounts


def insertAnnotationData(annotationItems, userName, debug=False):
    ### This will insert all of the annotations pulled from the DSA and also insert a projectName to keep things bundled/separate
    ## Add the projectName to all of the annotations as well
    annotationItems = [dict(item, **{"userName": userName}) for item in annotationItems]
    ### The collection for annotations is called.. annotations!
    ## See this:
    ## print(len(annot)) returns 4099
    ## len(set(x["_id"] for x in annot)) returns 1814

    ## So here's some confusion.. the annotationItems can return many more annotations than actually exist...
    ## Because an annotation can be copied between items.. meaning the same annotation is associated with many images..

    operations = []
    for a in annotationItems:
        operations.append(UpdateOne({"_id": a["_id"]}, {"$set": a}, upsert=True))
    for chunk in chunks(operations, 500):
        result = mc["annotationData"].bulk_write(chunk)
        if debug:
            pprint(result.bulk_api_result)
    return result


def getAnnotationData_fromDB(projectName, filters=None):
    ## Can add additional filters to mongo query in the future other than projctName
    annotationData = list(mc["annotationData"].find({}))
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
        regionName = (
            str(record["regionName"]) if not pd.isna(record["regionName"]) else None
        )
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


def getProjects(fld_id: str, forceRefresh: bool = False) -> List[dict]:
    """Get a list of NeuroTK folders for the user.

    Args:
        fld_id: DSA id of NeuroTK Projects folder.
        forceRefresh: Referesh the mongo database if needed.

    Returns:
        List of project metadata.

    """
    # Mongo collection.
    collection = mc['projectList']

    # Get the project in collection.
    projectListKey = f'{USER}/{fld_id}'
    projectList = list(collection.find({"projectList": projectListKey}))

    if projectList and not forceRefresh:
        return projectList
    else:
        # Delete the current mongo document.
        if projectList:
            collection.delete_many({"projectList": projectListKey})

        # Loop through public and then private folders.
        projects = get_projects(gc, fld_id)
        projects = {p['_id']: p for p in projects}

        projects = [
            dict(projects[imageId], **{"projectList": projectListKey})
            for imageId in projects
        ]

        ### Now insert the bundle into mongo
        operations = []
        for a in projects:
            operations.append(
                UpdateOne({"_id": a["_id"]}, {"$set": a}, upsert=True)
            )
        for chunk in chunks(operations, 500):
            _ = collection.bulk_write(chunk)

        ## Going to return the just inserted item Set..
        projectList = list(collection.find({"projectList": projectListKey}))

        return projectList


def getProjectDataset(
        projectName: str, projectFolderId: str, forceRefresh: bool = False
    ) -> List[dict]:
    """
    Given a projectName, return the data from local mongo database if it exists
    otherwise pull from DSA using girder_client and add to mongo database.
    """
    # Mongo collection.
    collection = mc["projectImages"]

    # Get the project in collection.
    projectImages = list(collection.find({"projectName": projectName}))

    if projectImages and not forceRefresh:
        # Return existing project.
        return projectImages
    else:
        if projectImages:
            collection.delete_many({"projectName": projectName})

        # Get data from DSA.
        projectDatasetDict = get_neuroTK_projectDatasets(projectFolderId)

        ## This is a dictionary keyed by the image itemId... needs to be flattened before mongo insert..
        ## Also don't forget to add the projectName or things will go badly

        ## This only will run if the project actually has datasets, it's possible
        ## to create a blank project that has not been populated yet..
        if projectDatasetDict:
            projectDataSetItems = [
                dict(projectDatasetDict[imageId], **{"projectName": projectName})
                for imageId in projectDatasetDict
            ]
            
            """Snippet of code that replaces "." with "-" when in the key of 
            dictionary."""
            for i in range(len(projectDataSetItems)):
                d = projectDataSetItems[i]

                for k in list(d.keys()):
                    v = d[k]

                    if '.' in k:
                        new_k = k.replace('.', '-')

                        del d[k]

                        d[new_k] = v

                projectDataSetItems[i] = d

            ### Now insert the bundle into mongo
            operations = []
            for a in projectDataSetItems:
                operations.append(
                    UpdateOne({"_id": a["_id"]}, {"$set": a}, upsert=True)
                )
            for chunk in chunks(operations, 500):
                _ = collection.bulk_write(chunk)

            ## Going to return the just inserted item Set..
            projectImages = list(collection.find({"projectName": projectName}))

            return projectImages
        else:
            return None


def lookup_jobInfo_for_user_task( imageIdList, search_dict):
    ### Given a list of imageIds, the username which we get some gc.settings
    ### and a seach dict of the parameter set we are interested in, this will
    ## return the status for every image in the list, as well as jobSubmitTime if we can find it
    ## Need to cast all the values to a string and also add the _original_params to the key
    str_search_dict = {f"_original_params.{k}": str(v) for k, v in search_dict.items()}
    ## Adding in userKey to the lookup dictionary
    str_search_dict['user'] = USER

    record_set = collection.find_one(str_search_dict)
    print(len(record_set))

    pass