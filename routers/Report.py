import requests
from fastapi import APIRouter
from lib import Global
from lib import Mongo

router = APIRouter()

@router.get("/report")
def model(page: int,limit: int,name: str):
    data = {
      'page':page,
      'limit':limit,
      'info.name': Global.queryToFuzzy(name)
    }
    res = Mongo.find('test','report',query = data)
    return res

@router.get("/report/{id}")
def getReport(id: str):
    res = Mongo.findOne('test','report',query = {'_id':Mongo.toObjectId(id)})
    return res