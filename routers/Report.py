import requests
from fastapi import APIRouter
from lib import Global
from lib import Mongo
from pydantic import BaseModel

router = APIRouter()

class Sort(BaseModel):
    key: str
    type: int

class Item(BaseModel):
    name: str
    limit: int
    page: int
    sort: Sort

@router.post("/report")
def model(item:Item):
    item = item.model_dump()
    data = {
      'page':item['page'],
      'limit':item['limit'],
      'info.name': Global.queryToFuzzy(item['name']),
      'sort':item['sort']
    }
    res = Mongo.find('test','report',query = data)
    return res

@router.get("/report/{id}")
def getReport(id: str):
    res = Mongo.findOne('test','report',query = {'_id':Mongo.toObjectId(id)})
    return res