from fastapi import FastAPI
from lib.Review import Review

app = FastAPI()

@app.get("/")
def read_root():
    t1 = Review('2719200')
    return t1.getData()

@app.get("/test")
def read_item():
    t1 = Review('2719200')
    return t1.getLLMReport()