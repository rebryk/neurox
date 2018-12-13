import json

import rumps

SETTINGS_PATH = 'settings.json'

DEFAULT_SETTINGS = {
    'url': 'https://platform.staging.neuromation.io/api/v1',
    'job_params': '',
    'token': None
}


def load_settings(app: rumps.App):
    settings = dict()
    settings.update(DEFAULT_SETTINGS)

    try:
        with app.open(SETTINGS_PATH) as file:
            settings.update(json.load(file))
    except:
        pass

    return settings


def save_settings(app: rumps.App):
    try:
        with app.open(SETTINGS_PATH, 'w') as file:
            json.dump(app.settings, file)
    except Exception:
        pass
