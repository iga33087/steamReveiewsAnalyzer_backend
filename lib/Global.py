import re
import json

steamApiBase = 'https://store.steampowered.com/appreviews/'
steamStoreBase = 'https://store.steampowered.com/app/'
ollamaBase = 'http://localhost:11434'
mongoBase = 'mongodb://root:example@localhost:27017'

def jsonRegex(text):
    try:
        results = []
        regex = r"```json\s+([\s\S]*?)```"
        matches = re.findall(regex,text)
        for match in matches:
            try:
                json_data = json.loads(match.strip())
                results.append(json_data)
            except json.JSONDecodeError as e:
                raise(e)
        return results
    except Exception as e:
        raise(e)

def getAppId(text):
    match = re.search(r"(\d+)",text)
    if match:
        app_id = match.group(1)
        return app_id
    else:
        raise Exception('Error Input')

def queryToFuzzy(text):
    try:
        pattern = re.compile(f".*{text}.*",re.IGNORECASE)
        res = {"$regex": pattern}
        return res
    except Exception as e:
        raise(e)