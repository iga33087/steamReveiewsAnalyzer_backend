import json
from typing import TypedDict
from pymongo import MongoClient
from bson import json_util, ObjectId
from lib import Global

uri = Global.mongoBase

class Movie(TypedDict):
    name: str
    year: int

def find(dataBase,collection,query = {}):
    try:
        client = MongoClient(uri)
        database = client.get_database(dataBase)
        movies = database.get_collection(collection)
        res = movies.find(query)
        res = json_util.dumps(list(res))
        client.close()
        return json.loads(res)
    except Exception as e:
        raise Exception(e)

def findOne(dataBase,collection,query = {}):
    try:
        client = MongoClient(uri)
        database = client.get_database(dataBase)
        movies = database.get_collection(collection)
        res = movies.find()
        res = json_util.dumps(list(res))
        client.close()
        return json.loads(res)
    except Exception as e:
        raise Exception(e)

def add(dataBase,collection,data):
    try:
        client = MongoClient(uri)
        database = client.get_database(dataBase)
        movies = database.get_collection(collection)
        res = movies.insert_one(data)
        client.close()
        return {"id":str(res.inserted_id)}
    except Exception as e:
        raise Exception(e)

def toObjectId(value: str | ObjectId) -> ObjectId:
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(value)
    except Exception as e:
        raise Exception(e)
