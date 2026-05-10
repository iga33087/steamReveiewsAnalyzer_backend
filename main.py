from fastapi import FastAPI,Response
from lib.Review import Review
from routers import Model

app = FastAPI()

@app.get("/")
def home():
    t1 = Review('2246340')
    return t1.getData()

@app.get("/test")
def test():
    t1 = Review('2246340')
    return t1.getLLMReport()

@app.get("/test1")
def test1(response: Response):
    try:
        return {'test':111}
    except Exception as e:
        response.status_code = 400
        return {'error':str(e)}

app.include_router(Model.router)