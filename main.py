import asyncio
import time
from fastapi import FastAPI,Response
from lib.Review import Review
from lib import Mongo
from lib import Global
from routers import Model
from routers import Report

app = FastAPI()


@app.get("/genReport")
async def genReport(response: Response,id: str,model: str,size: int,refer:bool):
    try:
        reviewObj = Review(Global.getAppId(id),model,size,refer)
        await reviewObj.main()
        return {'id':reviewObj.reportId}
    except Exception as e:
        response.status_code = 400
        return {'error':str(e)}

@app.get("/getReport")
def getReport(id: str):
    res = Mongo.findOne('test','report',query = {'_id':Mongo.toObjectId(id)})
    return res

@app.get("/test")
def test(response: Response):
    try:
        time.sleep(3)
        return 'OK'
    except Exception as e:
        return {'error':str(e)}

@app.get("/test1")
async def test1(response: Response):
    try:
        await asyncio.sleep(3)
        return 'OK'
    except Exception as e:
        return {'error':str(e)}

app.include_router(Model.router)
app.include_router(Report.router)