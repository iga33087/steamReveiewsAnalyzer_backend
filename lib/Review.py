import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import quote
from datetime import date
from lib import Mongo
from lib import Global
from typing import List, Annotated
from pydantic import BaseModel, Field

class GameReviewReport(BaseModel):

    class ReviewItem(BaseModel):
        title: Annotated[str, Field(ge=0, le=6, description="Names of the Advantages and Disadvantages")]
        score: Annotated[int, Field(ge=0, le=100, description="The score for each pros and cons item is determined by the number of reviews that mention it; the more reviews that mention it, the higher the score. 0 is the lowest, and 100 is the highest.")]

    class ScoreDetails(BaseModel):
        story: Annotated[int, Field(ge=0, le=10, description="Rate the game's storyline, with 0 being the lowest and 10 being the highest.")]
        system: Annotated[int, Field(ge=0, le=10, description="Rate the game's combat system or overall system design, with 0 being the lowest and 10 being the highest.")]
        music: Annotated[int, Field(ge=0, le=10, description="Rate the game's soundtrack and sound effects on a scale where 0 is the lowest and 10 is the highest.")]
        creative: Annotated[int, Field(ge=0, le=10, description="Rate the game's innovative performance, with 0 being the lowest and 10 being the highest.")]
        replayability: Annotated[int, Field(ge=0, le=10, description="Rate the game's replay value, with 0 being the lowest and 10 being the highest.")]
        difficulty: Annotated[int, Field(ge=0, le=10, description="Rate the game's difficulty, with 0 being the lowest and 10 being the highest.")]
        avg: Annotated[int, Field(ge=0, le=10, description="The average of the sum of story, system, music, creativity, replayability, and difficulty")]

    summary: str = Field(..., description="A text summary of the game's overall review, using Markdown")
    positive: List[ReviewItem] = Field(..., description="List of Positive Rating Labels")
    negative: List[ReviewItem] = Field(..., description="List of Negative Rating Labels")
    score: ScoreDetails = Field(..., description="Detailed Scores by Dimension")

prompt = """
You are now a professional game reviewer. Your task is to thoroughly analyze the Steam reviews for a specific game to summarize its overall reception and its strengths and weaknesses, with a focus on how players from different language regions have rated it. The following prompt must be strictly followed:

1. Respond in Traditional Chinese
"""

class Review:
    def __init__(self, id, model, size):
        self.id = id
        self.model = model
        self.size = size
        self.info = {}
        self.data = []
        self.total = {}
        self.report = {}
        self.reportId = ''
        self.genStartTime = datetime.now().timestamp()
        print('genStartTime',self.genStartTime)
        self.fetchInfo()
        print('fetchInfo Completed')
        self.fetchData()
        print('fetchData Completed')
        self.fetchLLMReport()
        print('fetchLLMReport Completed')
        self.genEndTime = datetime.now().timestamp()
        print('genEndTime',self.genEndTime)
        self.postToDB()

    def fetchInfo(self):
        try:
            res = requests.get(f'{Global.steamStoreBase}{self.id}').text
            soup = BeautifulSoup(res)
            self.info['name'] = soup.find(class_="apphub_AppName").get_text(separator=" ", strip=True)
            self.info['img'] = soup.find(class_="game_header_image_full")['src']
        except Exception as e:
            raise(e)

    def fetchData(self):
        try:
            res = {'cursor':'*','reviews':[]}
            cursor = []
            obj = {
                'json':1,
                'filter':'recent',
                'num_per_page':100,
                'language':'all',
                'purchase_type':'all',
                'cursor':'*'
            }
            while res['cursor'] not in cursor and len(self.data) < self.size:
                cursor.append(res['cursor'])
                obj['cursor'] = res['cursor']
                self.data.extend(res['reviews'])
                res = requests.get(f'{Global.steamApiBase}{self.id}',params=obj).json()
                if 'review_score' in res['query_summary']:
                    self.total = res['query_summary']
        except Exception as e:
            raise(e)

    def fetchLLMReport(self):
        try:
            headers = {}
            data = {
                'model': self.model,
                "stream": False,
                'messages': [{'role': 'user', 'content': f'{self.getReveiwsArr()} {prompt}'}],
                'format': GameReviewReport.model_json_schema(),
                'options': {
                  'temperature': 0.0
                }
            }
            res = requests.post(f'{Global.ollamaBase}/api/chat',headers=headers,json=data).json()
            #self.report = Global.jsonRegex(res['message']['content'])[0]
            self.report = json.loads(res['message']['content'].replace("```json", "").replace("```", "").strip())
            return self.report
        except Exception as e:
            print(777777,e)
            raise(e)

    def postToDB(self):
        try:
            res = Mongo.add('test','report',self.getData())
            self.reportId = res['id']
            print('postToDB',self.reportId)
        except Exception as e:
            raise(e)

    def getCountryObj(self):
        res = {}
        for x in self.data:
            if x['language'] not in res:
                res[x['language']]={'voted_up':0,'voted_down':0}
            if x['voted_up']:
                res[x['language']]['voted_up'] += 1
            else:
                res[x['language']]['voted_down'] += 1
        return res

    def getTimeObj(self):
        res = {}
        for x in self.data:
            dateTime = date.fromtimestamp(x['timestamp_created']).strftime("%Y/%m/%d")
            if dateTime not in res:
                res[dateTime] = {'all':{'voted_up':0,'voted_down':0}}
            if x['language'] not in res[dateTime]:
                res[dateTime][x['language']]={'voted_up':0,'voted_down':0}
            if x['voted_up']:
                res[dateTime]['all']['voted_up'] += 1
                res[dateTime][x['language']]['voted_up'] += 1
            else:
                res[dateTime]['all']['voted_down'] += 1
                res[dateTime][x['language']]['voted_down'] += 1
        return res

    def getReveiwsArr(self):
        res = []
        for x in self.data:
            obj = {
                'review': x['review'],
                'language': x['language'],
                'positives': x['voted_up'],
            }
            res.append(obj)
        return res

    def getData(self):
        getTimeObj = self.getTimeObj()
        return {
            'info':self.info,
            'total':self.total,
            'model':self.model,
            'size':self.size,
            'report':self.report,
            'countryObj':self.getCountryObj(),
            'timeObj':getTimeObj,
            'genStartTime':self.genStartTime,
            'genEndTime':self.genEndTime,
            'timeRange':{
                'start':list(getTimeObj.keys())[-1],
                'end':list(getTimeObj.keys())[0]
            },
            'createTime': datetime.now().timestamp()
        }