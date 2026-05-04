import requests
from urllib.parse import quote
from datetime import date

steamApiBase = 'https://store.steampowered.com/appreviews/'
openWebUIApiBase = 'http://localhost:3000'
openWebUIApiKey = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjUwMDgxN2U0LWU4YmItNGY4MC04OTk3LTQyYTgxNzk5NTFkMyIsImV4cCI6MTc3ODY3ODc2NSwianRpIjoiZjFkODU1YWEtNDA1ZS00NGI5LWEwZDUtZmVlZDFlYjZjODdmIn0.KxPyh3_P2nBHyd4zGKLfuCaSdnd2w2LHnwfCvOATtTE'

class Review:
    def __init__(self, id):
        self.id = id
        self.data = []
        self.total = {}
        self.fetchData()

    def fetchData(self):
        res = {'cursor':'*','reviews':[]}
        cursor = []
        obj = {
            'json':1,
            'filter':'recent',
            'num_per_page':100,
            'language':'all',
            'cursor':'*'
        }
        while res['cursor'] not in cursor:
            cursor.append(res['cursor'])
            obj['cursor'] = res['cursor']
            self.data.extend(res['reviews'])
            res = requests.get(f'{steamApiBase}{self.id}',params=obj).json()
            if 'review_score' in res['query_summary']:
                self.total = res['query_summary']
    
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

    def getLLMReport(self):
        headers = {
            'Authorization': openWebUIApiKey,
            'Content-Type': 'application/json'
        }
        data = {
            'model': 'llama3:latest',
            'messages': [{'role': 'user', 'content': f'{self.getReveiwsArr()} 這是某一款遊戲的steam評論，幫我從上面這些評論來統整出這款遊戲的整體評價，用中文回覆'}]
        }
        res = requests.post(f'{openWebUIApiBase}/api/chat/completions',headers=headers,json=data).json()
        return res
    
    def getData(self):
        return {'total':self.total,'countryObj':self.getCountryObj(),'timeObj':self.getTimeObj(),'data':self.getReveiwsArr()}