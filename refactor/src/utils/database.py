import pandas as pd
from flask_mongoengine import MongoEngine
from .settings import MONGO_URI, MONGODB_DB
from flask import Flask
import pymongo


# initialize the app with the extension

db = MongoEngine()


## Since the annotations do not have a very rigid schema and have weird fields, not sure if I want a class or not

mc = pymongo.MongoClient(MONGO_URI)
mc = mc[MONGODB_DB]  ### Attach the mongo client object to the database I want to store everything



def insertAnnotationData( annotationItems, projectName):
    ### This will insert all of the annotations pulled from the DSA and also insert a projectName to keep things bundled/separate
    ## Add the projectName to all of the annotations as well
    annotationItems = [dict(item, **{'projectName':projectName}) for item in annotationItems]
    ### The collection for annotations is called.. annotations!
    print(len(annotationItems))
    mc['annotationData'].insert_many(annotationItems,upsert=True)
    return len(annotationItems)


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
