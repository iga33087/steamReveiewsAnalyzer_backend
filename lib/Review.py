import requests
from urllib.parse import quote
from datetime import date

reveiwsLimit = 500
steamApiBase = 'https://store.steampowered.com/appreviews/'
modelName = 'phi4-mini:latest'
openWebUIApiBase = 'http://10.15.1.103:3000'
openWebUIApiKey = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Ijg0NWRkYTFkLWM2ZDEtNDBmNS1iZjRhLTkyMTc5YTRkYTg2YyIsImV4cCI6MTc4MDM4MjQzMSwianRpIjoiNWEzNDVjNWQtNTJhNC00ZmU2LThjYjYtMmNhMjczM2M4MWMyIiwiaWF0IjoxNzc3OTYzMjMxfQ.Q1Rbko3emDsWmpeuWQWQstIiUgY6mV14lPRRUbjGAjU'
#prompt = '你現在是一個專業的評論分析者，上面是某一款遊戲的steam評論，請從上面這些評論來詳細統整出這款遊戲的整體評價和優缺點，用繁體中文回覆'
prompt = '你現在是一個專業的評論分析者，上面是某一款遊戲的steam評論，請從上面這些評論來詳細統整出這款遊戲的整體評價和優缺點，並且著重在不同語系的玩家分別有甚麼評價，用繁體中文回覆，輸出格式嚴格限定用JSON，格式為{"summary":...,"positive":[...],"negative":[...],"score":...}，summary為遊戲的整體評價和優缺點，positive為用陣列整理出遊戲有哪些優點，negative為用陣列整理出遊戲有哪些缺點，score為遊戲整體分數，0~10分。'

class Review:
    def __init__(self, id):
        self.id = id
        self.data = []
        self.total = {}
        self.fetchData()

    def fetchData(self):
        try:
            res = {'cursor':'*','reviews':[]}
            cursor = []
            obj = {
                'json':1,
                'filter':'recent',
                'num_per_page':100,
                'language':'all',
                'cursor':'*'
            }
            while res['cursor'] not in cursor and len(self.data) < reveiwsLimit:
                cursor.append(res['cursor'])
                obj['cursor'] = res['cursor']
                self.data.extend(res['reviews'])
                res = requests.get(f'{steamApiBase}{self.id}',params=obj).json()
                if 'review_score' in res['query_summary']:
                    self.total = res['query_summary']
        except:
            raise Exception("Error!!!")
    
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
            'model': modelName,
            'messages': [{'role': 'user', 'content': f'{self.getReveiwsArr()} {prompt}'}]
        }
        res = requests.post(f'{openWebUIApiBase}/api/chat/completions',headers=headers,json=data).json()
        return res
    
    def getData(self):
        return {'total':self.total,'countryObj':self.getCountryObj(),'timeObj':self.getTimeObj(),'data':self.getReveiwsArr()}