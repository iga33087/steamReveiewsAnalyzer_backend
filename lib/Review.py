import requests
from urllib.parse import quote
from datetime import date

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
            res = requests.get(f'https://store.steampowered.com/appreviews/{self.id}',obj).json()
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
    
    def getData(self):
        return {'total':self.total,'countryObj':self.getCountryObj(),'timeObj':self.getTimeObj()}