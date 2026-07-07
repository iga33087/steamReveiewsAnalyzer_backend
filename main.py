from fastapi import FastAPI,Response
from lib.Review import Review
from lib import Mongo
from lib import Global
from routers import Model
from routers import Report

app = FastAPI()


@app.get("/genReport")
def genReport(response: Response,id: str,model: str,size: int):
    try:
        t1 = Review(Global.getAppId(id),model,size)
        return {'id':t1.reportId}
    except Exception as e:
        response.status_code = 400
        return {'error':str(e)}

@app.get("/getReport")
def getReport(id: str):
    res = Mongo.findOne('test','report',query = {'_id':Mongo.toObjectId(id)})
    return res

@app.get("/test1")
def test1(response: Response):
    try:
        res = Mongo.find('test','report',query = {'_id':Mongo.toObjectId('6a02f41375fb9c018a6b24b9')})
        return res
    except Exception as e:
        response.status_code = 400
        return {'error':str(e)}

app.include_router(Model.router)
app.include_router(Report.router)