import pandas as pd
from flask_mongoengine import MongoEngine
from .settings import MONGO_URI
from flask import Flask

# initialize the app with the extension
## So this seems like this should be done in the app.py and imported...

# db = MongoEngine({"config": {"MONGODB_HOST": MONGO_URI}})
### So this is all wrong, I need to the flask app context or this doesn't seem to work..
# app = Flask(__name__)

db_settings = {"DB": "DSACache", "host": "mongodb://docker:docker@mongodb:27017/DSACache"}  #
# {## just do db = {}

db = MongoEngine()


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
