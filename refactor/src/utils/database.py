import pandas as pd
from flask_mongoengine import MongoEngine
from .settings import MONGO_URI, MONGODB_DB
from flask import Flask
import pymongo
from pymongo import UpdateOne
from pprint import pprint
from .api import get_ppc_details_simple
# initialize the app with the extension

db = MongoEngine()


## Since the annotations do not have a very rigid schema and have weird fields, not sure if I want a class or not

mc = pymongo.MongoClient(MONGO_URI)
mc = mc[MONGODB_DB]  ### Attach the mongo client object to the database I want to store everything

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def insertAnnotationData( annotationItems, projectName,debug=False):
    ### This will insert all of the annotations pulled from the DSA and also insert a projectName to keep things bundled/separate
    ## Add the projectName to all of the annotations as well
    annotationItems = [dict(item, **{'projectName':projectName}) for item in annotationItems]
    ### The collection for annotations is called.. annotations!
    print(len(annotationItems),'to be inserted or upserted into the mongo table..')
    ## See this:
    ## print(len(annot)) returns 4099
    ## len(set(x["_id"] for x in annot)) returns 1814

    ## So here's some confusion.. the annotationItems can return many more annotations than actually exist...
    ## Because an annotation can be copied between items.. meaning the same annotation is associated with many images..

    ## Evan you could/would add your code to see if the annotation is named PPC and "fix" it using our de

    ### EVAN ADD IN YOUR CODE THAT TWEAKS/DEALS WITH PPC STATS BEFORE WE INSERT THE DATA
    # for a in annotationItems:
    #     if a['annotation']['name'].contains('PPC'):
    #         then:
    #         add_ppc_stuff_to_item
    #         ['description']:
    #         pass



    operations = []
    for a in annotationItems:
        operations.append(UpdateOne({'_id': a['_id']},{"$set":a},upsert=True))
    for chunk in chunks(operations,500):
        result = mc['annotationData'].bulk_write(chunk)
        if debug: pprint(result.bulk_api_result)
    return result


def getAnnotationData_fromDB( projectName, filters=None):
    ## Can add additional filters to mongo query in the future other than projctName
    annotationData = list(mc['annotationData'].find({}))
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
