import json
import os

class CacheHelper():
    def __init__(self):
        self._cache: dict = None
        self.fetch_cache()

    def fetch_cache(self) -> None:
        '''fetch from database'''
        with open(fr"{os.getcwd()}/Storage/Json/search_cache.json", 'r') as f:
            self._cache = json.load(f)

    def update_cache(self, identifier: str, title: str, length: str, timestamp) -> None:
        '''update database'''
        with open(fr"{os.getcwd()}/Storage/Json/search_cache.json", 'r') as f:
            data: dict = json.load(f)
        if data.get(identifier) is not None:
            data[identifier]['title'] = title
            data[identifier]['length'] = length
            data[identifier]['timestamp'] = timestamp
        else:
            data[identifier] = self._cache[identifier] = dict(title=title, length=length, timestamp=timestamp)
        with open(fr"{os.getcwd()}/Storage/Json/search_cache.json", 'w') as f:
            json.dump(data, f)

cache_helper = CacheHelper()