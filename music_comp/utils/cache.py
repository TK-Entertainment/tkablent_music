from msgspec.json import decode as json_decode
from msgspec import DecodeError
from msgspec.json import encode as json_encode
import shutil
import threading
import queue
import os
import time

debug = False

class CacheWorker(threading.Thread):
    def __init__(self, queue: queue.Queue): 
        threading.Thread.__init__(self, name="CacheWorker")
        self._cache_path = rf"{os.getcwd()}/music_comp/search_cache.json"
        self._bak_cache_path = rf"{os.getcwd()}/music_comp/search_cache.json.bak"
        self._queue = queue
        self._timer = 70000

        """fetch from database"""
        try:
            with open(self._cache_path, "rb") as f:
                self._cache: dict = json_decode(f.read())

            shutil.copyfile(self._cache_path, self._bak_cache_path)
        except FileNotFoundError:
            with open(self._cache_path, "wb") as f:
                f.write(b"{}")
            self._cache = {}
            shutil.copyfile(self._cache_path, self._bak_cache_path)
        except DecodeError:
            with open(self._bak_cache_path, "rb") as bak_f:
                self._cache: dict = json_decode(bak_f.read())

            shutil.copyfile(self._bak_cache_path, self._cache_path)

    def run(self) -> None:
        while True:
            if self._queue.qsize() == 0:
                if self._timer == 70000:
                    self._timer = 0
                    self._purge_outdated()
                else:
                    self._timer += 1
                    time.sleep(1)
            else:
                new_data = self._queue.get()
                self.update_cache(new_data)

    def _purge_outdated(self) -> None:
        """purge outdated data"""
        data = self._cache
        for identifier in list(data.keys()):
            if time.time() - data[identifier]["timestamp"] >= 2592000:
                del data[identifier]

        with open(self._cache_path, "wb"):
            # clear whole cache file
            pass

        with open(self._cache_path, "wb") as f:
            f.write(json_encode(data))

        # self test json file
        try:
            with open(self._cache_path, "rb") as f:
                if debug: print("[DEBUG | Cache Module] Testing cache file")
                json_decode(f.read())
                if debug: print("[DEBUG | Cache Module] Cache file okay!")

            # if json is okay, then update in memory cache
            if debug: print("[DEBUG | Cache Module] Updating in memory cache")
            self._cache = data

        except DecodeError:  # revert if file fucked up
            if debug: print("[DEBUG | Cache Module] Local cache corrupted, reverting to last backup")
            shutil.copyfile(self._bak_cache_path, self._cache_path)

    def update_cache(self, new_data: dict) -> None:
        """update database"""
        try:
            with open(self._cache_path, "rb") as f:
                if debug: print("[DEBUG | Cache Module] Loading Cache from disk")
                data = json_decode(f.read())
                if debug: print("[DEBUG | Cache Module] Cache file okay!")

            shutil.copyfile(self._cache_path, self._bak_cache_path)
            if debug: print("[DEBUG | Cache Module] Overwriting backup cache file")
        except DecodeError:
            with open(self._bak_cache_path, "rb") as bak_f:
                if debug: print("[DEBUG | Cache Module] Main cache file corrupted, loading backup cache file")
                data = json_decode(bak_f.read())
                if debug: print("[DEBUG | Cache Module] Backup cache file okay!")

            shutil.copyfile(self._bak_cache_path, self._cache_path)
            if debug: print("[DEBUG | Cache Module] Overwriting main cache file with backup")


        for identifier in new_data.keys():
            if debug: print(f"[DEBUG | Cache Module] Fetched {identifier}")
            if data.get(identifier) is not None:
                if debug: print(f"[DEBUG | Cache Module] Updating {identifier}")
                data[identifier]["title"] = new_data[identifier]["title"]
                data[identifier]["length"] = new_data[identifier]["length"]
                data[identifier]["timestamp"] = new_data[identifier]["timestamp"]
            else:
                if debug: print(f"[DEBUG | Cache Module] {identifier} is not here, adding index")
                data[identifier] = dict(
                    title=new_data[identifier]["title"],
                    length=new_data[identifier]["length"],
                    timestamp=new_data[identifier]["timestamp"],
                )

        with open(self._cache_path, "wb"):
            # clear whole cache file
            pass

        with open(self._cache_path, "wb") as f:
            if debug:
                beforetime = time.time()
                print("[DEBUG | Cache Module] Writting cache file")
            f.write(json_encode(data))
            if debug:
                nowtime = time.time()
                print("[DEBUG | Cache Module] Cache writting elapsed time:", nowtime - beforetime)

        # self test json file
        try:
            with open(self._cache_path, "rb") as f:
                if debug: print("[DEBUG | Cache Module] Testing cache file")
                json_decode(f.read())
                if debug: print("[DEBUG | Cache Module] Cache file okay!")

            # if json is okay, then update in memory cache
            if debug: print("[DEBUG | Cache Module] Updating in memory cache")
            self._cache = data

        except DecodeError:  # revert if file fucked up
            if debug: print("[DEBUG | Cache Module] Local cache corrupted, reverting to last backup")
            shutil.copyfile(self._bak_cache_path, self._cache_path)

    @property
    def cache(self):
        return self._cache