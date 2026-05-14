import requests
from fastapi import APIRouter
from lib import Global

router = APIRouter()

@router.get("/model")
def model():
    res = requests.get(f'{Global.ollamaBase}/api/tags').json()
    return res['models']