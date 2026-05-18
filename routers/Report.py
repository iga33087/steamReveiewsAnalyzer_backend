import requests
from fastapi import APIRouter
from lib import Global
from lib import Mongo

router = APIRouter()

@router.get("/report")
def model():
    res = Mongo.find('test','report',query = {})
    return res

@router.get("/report/{id}")
def getReport(id: str):
    res = Mongo.findOne('test','report',query = {'_id':Mongo.toObjectId(id)})
    return res