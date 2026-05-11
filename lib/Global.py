import re
import json

reveiwsLimit = 100
steamApiBase = 'https://store.steampowered.com/appreviews/'
steamStoreBase = 'https://store.steampowered.com/app/'
modelName = 'gemma3:4b'
OllamaBase = 'http://localhost:11434'

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