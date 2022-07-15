import enum
import json
import os

SAVE_PATH = './save.json'

class StorageKey:
    RootDirs = 'RootDirs'
    LastPath = 'LastPath'

class LocalStorager:
    def __init__(self, path):
        self.path = path
        self.storage = {}
        if os.path.exists(path):
            with open(path, 'r') as f:
                self.storage = json.load(f)

    def load(self, key):
        if self.storage is None:
            return None
        return self.storage.get(key, None)

    def save(self, key, value):
        self.storage[key] = value
        with open(self.path, 'w') as f:
            json.dump(self.storage, f, indent=4)


localStorage = LocalStorager(SAVE_PATH)