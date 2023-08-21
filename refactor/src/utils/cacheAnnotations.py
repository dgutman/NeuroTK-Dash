import pymongo

mc = pymongo.MongoClient()
db = mc['dsaCache']


annots = db['annotationData']
fullAnnotats = db['annotationDataWelements']


print(annots.find_one({"annotation.name":"gray-matter-from-xmls"}))
