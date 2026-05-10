import requests
from urllib.parse import quote
from datetime import date
from lib import Global

prompt = """
你現在是一個專業的評論分析者，上面是某一款遊戲的steam評論，請從上面這些評論來詳細統整出這款遊戲的整體評價和優缺點，並且著重在不同語系的玩家分別有甚麼評價，以下為需要嚴格遵守的prompt：
1. 用繁體中文回覆，輸出格式嚴格限定用JSON，格式為{"summary":...,"positive":[...],"negative":[...],"score":{"story":...,"system":...,"music":...,"creative":...,"replayability":...,"difficulty":...,"avg":...}}。
2. summary為遊戲的整體評價和優缺點，要用Markdown。
3. positive為用陣列整理出遊戲有哪些優點，別用Markdown，且字數限定在6個字以內。
4. negative為用陣列整理出遊戲有哪些缺點，別用Markdown，且字數限定在6個字以內。
5. 在score裡面的story為遊戲的劇情故事給出評分，範圍是0~10分。
6. 在score裡面的system為遊戲的戰鬥系統或系統設計給出評分，範圍是0~10分。
7. 在score裡面的music為遊戲的配樂及音效表現給出評分，範圍是0~10分。
8. 在score裡面的creative為遊戲的創新表現給出評分，範圍是0~10分。
9. 在score裡面的replayability為遊戲的耐玩性給出評分，範圍是0~10分。
10. 在score裡面的difficulty為遊戲的難度給出評分，範圍是0~10分。
11. score的avg為story、system、music、creative、replayability、difficulty總和的平均值
"""

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
            while res['cursor'] not in cursor and len(self.data) < Global.reveiwsLimit:
                cursor.append(res['cursor'])
                obj['cursor'] = res['cursor']
                self.data.extend(res['reviews'])
                res = requests.get(f'{Global.steamApiBase}{self.id}',params=obj).json()
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
        headers = {}
        data = {
            'model': Global.modelName,
            "stream": False,
            'messages': [{'role': 'user', 'content': f'{self.getReveiwsArr()} {prompt}'}]
        }
        res = requests.post(f'{Global.OllamaBase}/api/chat',headers=headers,json=data).json()
        return Global.jsonRegex(res['message']['content'])
    
    def getData(self):
        return {'total':self.total,'countryObj':self.getCountryObj(),'timeObj':self.getTimeObj(),'data':self.getReveiwsArr()}