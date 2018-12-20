import json


class Settings:
    DEFAULT_SETTINGS = {
        'job_params': '',
        'port': '',
        'presets': []
    }

    def __init__(self, path: str):
        self.path = path
        self.settings = dict()
        self.settings.update(self.DEFAULT_SETTINGS)

    def __getitem__(self, item):
        return self.settings.get(item)

    def __setitem__(self, key, value):
        self.settings[key] = value

    def load(self):
        try:
            with open(self.path) as file:
                self.settings.update(json.load(file))
        except Exception as e:
            pass

    def save(self):
        try:
            with open(self.path, 'w') as file:
                json.dump(self.settings, file)
        except Exception as e:
            pass

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, *args):
        self.save()
