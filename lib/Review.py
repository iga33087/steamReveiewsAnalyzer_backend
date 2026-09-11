import json
import requests
import asyncio
import httpx
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import quote
from datetime import date
from lib import Mongo
from lib import Global
from typing import List, Annotated
from pydantic import BaseModel, Field

chunkPrompt = """
你是一個遊戲評論摘要分析器。

請遵守以下規則：
1. 必須使用繁體中文。
2. 不得使用英文作為自然語言回答。
3. 不得使用簡體中文。
4. 只根據提供的評論進行摘要。
5. 不要加入評論中不存在的資訊。
"""

reportPrompt = """
你是一個專業的遊戲評論分析器。

你的任務是分析 Steam 玩家評論摘要，並產生遊戲整體評價報告。

嚴格遵守以下規則：

【語言】
1. 所有自然語言內容必須使用繁體中文。
2. 禁止使用簡體中文。
3. 禁止使用英文作為自然語言回答。
4. title、summary 等所有文字欄位都必須使用繁體中文。
5. JSON 的 key 必須嚴格按照 JSON Schema，不得自行修改。

【資料】
1. 只能根據提供的評論內容進行分析。
2. 不得捏造評論中不存在的資訊。
3. positive 必須整理玩家提到的優點。
4. negative 必須整理玩家提到的缺點。
5. score 必須根據評論中實際出現的資訊評分。

【輸出】
1. 必須嚴格符合提供的 JSON Schema。
2. 不得輸出 Markdown code block。
3. 最終輸出只能是一個 JSON object。
4. 產生出來的報告必須大於500個字。
5. 排版必須工整，以條列式一條一條用Markdown整理出結論
"""

class GameReviewReport(BaseModel):

    class ReviewItem(BaseModel):
        title: Annotated[str, Field(min_length=1, max_length=20, description="優點或缺點的名稱，請保持精簡，必須使用繁體中文")]
        score: Annotated[int, Field(ge=0, le=100, description="優點或缺點的分數，最低0分，最高100分，越多評論提到分數就越高")]

    class ScoreDetails(BaseModel):
        story: Annotated[int, Field(ge=0, le=10, description="針對遊戲故事進行評分，最低0分，最高10分")]
        system: Annotated[int, Field(ge=0, le=10, description="針對遊戲系統進行評分，最低0分，最高10分")]
        music: Annotated[int, Field(ge=0, le=10, description="針對遊戲音樂及音效表現進行評分，最低0分，最高10分")]
        creative: Annotated[int, Field(ge=0, le=10, description="針對遊戲創新性進行評分，最低0分，最高10分")]
        replayability: Annotated[int, Field(ge=0, le=10, description="針對遊戲耐玩性進行評分，最低0分，最高10分")]
        difficulty: Annotated[int, Field(ge=0, le=10, description="針對遊戲難度進行評分，最低0分，最高10分")]
        avg: Annotated[int, Field(ge=0, le=10, description="針對遊戲的故事、系統、音樂及音效、創新性、耐玩性、難度分數取出平均值，不能有小數點，取整數")]

    summary: Annotated[str, Field(min_length=500, description="分析評論統整出來的結論，必須用Markdown，必須大於500個字，排版必須工整")]
    positive: List[ReviewItem] = Field(..., description="遊戲的優點列表")
    negative: List[ReviewItem] = Field(..., description="遊戲的缺點列表")
    score: ScoreDetails = Field(..., description="遊戲各項指標的分數")

class Review:
    def __init__(self, id, model, size,refer):
        self.retryNum = 0
        self.maxRetryNum = 3
        self.chunkSize = 10
        self.maxConcurrency= 4
        self.useReferenceReport = refer
        self.referenceReport = {}
        self.id = id
        self.model = model
        self.size = size
        self.info = {}
        self.data = []
        self.total = {}
        self.summaryChunk = []
        self.report = {}
        self.reportId = ''

    async def main(self):
        try:
            self.genStartTime = datetime.now().timestamp()
            print('genStartTime',self.genStartTime)
            self.fetchInfo()
            print('fetchInfo Completed')
            if self.useReferenceReport:
                self.fetchReferenceReport()
                print('fetchReferenceReport Completed')
            self.fetchReviews()
            print('fetchReviews Completed')
            self.summaryChunk = await self.reviewChunkToSummaryChunk()
            print('reviewChunkToSummaryChunk Completed')
            self.fetchLLMReport()
            print('fetchLLMReport Completed')
            self.genEndTime = datetime.now().timestamp()
            print('genEndTime',self.genEndTime)
            self.postToDB()
        except Exception as e:
            raise(e)

    def fetchInfo(self):
        try:
            res = requests.get(f'{Global.steamStoreBase}{self.id}').text
            soup = BeautifulSoup(res)
            self.info['name'] = soup.find(class_="apphub_AppName").get_text(separator=" ", strip=True)
            self.info['img'] = soup.find(class_="game_header_image_full")['src']
        except Exception as e:
            raise(e)

    def fetchReferenceReport(self):
        try:
          find = Mongo.findOne('test','report',query = {'mark':True})
          if find:
              self.referenceReport = Mongo.findOne('test','report',query = {'_id':Mongo.toObjectId(find['_id']['$oid'])})
        except Exception as e:
            raise(e)

    def fetchReviews(self):
        try:
            res = {'cursor':'*','reviews':[]}
            cursor = []
            obj = {
                'json':1,
                'filter':'recent',
                'num_per_page':10,
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

    async def reviewChunkToSummaryChunk(self):
        try:
            reviews = self.getReveiwsArr()
            reviewsChunks = [
                reviews[i:i+10]
                for i in range(0,len(reviews),self.chunkSize)
            ]
            semaphore = asyncio.Semaphore(self.maxConcurrency)
            async with httpx.AsyncClient(timeout=300) as client:
                tasks = [
                    self.genSummaryChunk(client, semaphore, chunk, index)
                    for index, chunk in enumerate(reviewsChunks)
                ]
                results = await asyncio.gather(*tasks)
            return results
        except Exception as e:
            raise(e)

    async def genSummaryChunk(self,client, semaphore, chunk, index):
        try:
            async with semaphore:
                headers = {}
                data = {
                    'model': self.model,
                    "stream": False,
                    'messages': [
                        {'role': 'system','content': chunkPrompt},
                        {'role': 'user', 'content': json.dumps(chunk, ensure_ascii=False)}
                    ],
                    'options': {
                      'temperature': 0.0
                    }
                }
                res = await client.post(f'{Global.ollamaBase}/api/chat',headers=headers,json=data)
                res = res.json()
                return res

        except Exception as e:
            raise(e)

    def fetchLLMReport(self):
        try:
            summaryChunk = [
                self.summaryChunk[i]['message']['content']
                for i in range(0,len(self.summaryChunk))
            ]
            headers = {}
            data = {
                'model': self.model,
                "stream": False,
                'messages': [
                    {'role': 'system','content': reportPrompt},
                    {'role': 'system', 'content': self.getReferencePrompt()},
                    {'role': 'user', 'content': json.dumps(summaryChunk, ensure_ascii=False)}
                ],
                'format': GameReviewReport.model_json_schema(),
                'options': {
                  'temperature': 0.0
                }
            }
            try:
                res = requests.post(f'{Global.ollamaBase}/api/chat',headers=headers,json=data).json()
                res = json.loads(res['message']['content'].replace("```json", "").replace("```", "").strip())
                GameReviewReport.model_validate(res)
                self.report = res
            except Exception as e:
                if(self.retryNum < self.maxRetryNum):
                    print('retry fetchLLMReport')
                    self.retryNum += 1
                    self.fetchLLMReport()
                else:
                    raise(e)

            return self.report
        except Exception as e:
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

    def getReferencePrompt(self):
        res = ''
        if self.useReferenceReport and 'report' in self.referenceReport:
            res = f'生產出來的報告文法、格式、排版、著重的地方請參考這篇：{self.referenceReport["report"]}'
        return res

    def getData(self):
        getTimeObj = self.getTimeObj()
        return {
            'info':self.info,
            'total':self.total,
            'model':self.model,
            'size':self.size,
            'summaryChunk':self.summaryChunk,
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