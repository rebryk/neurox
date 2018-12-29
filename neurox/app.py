import webbrowser
from datetime import datetime
from pathlib import Path
from typing import List
from uuid import uuid4

import pyperclip
import rumps

from neurox.client import JobDescription, StatusUpdate, NewJobUpdate, NeuroxClient
from neurox.settings import Settings
from neurox.utils import get_icon
from neurox.windows import job_description_window_builder
from neurox.windows import job_window_builder
from neurox.windows import port_window_builder
from neurox.windows import preset_name_window_builder
from neurox.windows import preset_params_window_builder


class NeuroxApp(rumps.App):
    UPDATE_DELAY = 1
    MAX_UPDATE_CYCLE_LEN = 30
    VERSION = '0.2'
    ABOUT = f'NeuroX (version {VERSION}) by Rebryk'

    def __init__(self, *args, **kwargs):
        super().__init__('Neurox', *args, icon=get_icon('icon'), **kwargs)
        self.tmp_path = Path(f'{self._application_support}/tmp')
        self.settings_path = Path(f'{self._application_support}/settings.json')

        self.client = NeuroxClient()

        self.iteration = 0
        self.update_cycle_len = 1

        self.initialize()

    def set_active_mode(self):
        self.update_cycle_len = 1

    def initialize(self):
        # Create a directory to store temporary files with commands
        if not self.tmp_path.exists():
            self.tmp_path.mkdir()

        # Clear the directory
        for file in self.tmp_path.glob('*'):
            file.unlink()

    def create_job(self, *args):
        try:
            with Settings(self.settings_path) as settings:
                job_window_builder.default_text = settings['job_params']
                response = job_window_builder.build().run()
                settings['job_params'] = str(response.text)

                if response.clicked:
                    self.client.submit_raw(settings['job_params'])
                    self.set_active_mode()
        except Exception as e:
            rumps.notification('Failed to create new job', '', str(e))

    def connect_ssh(self, job: JobDescription):
        try:
            tmp_file = str((self.tmp_path / f'{uuid4()}.sh').absolute())
            self.client.connect_ssh(job.id, tmp_file)
        except Exception as e:
            rumps.notification('SSH connection error', '', str(e))

    def remote_debug(self, job: JobDescription):
        try:
            with Settings(self.settings_path) as settings:
                port_window_builder.default_text = settings['port']
                response = port_window_builder.build().run()
                settings['port'] = str(response.text)

                if response.clicked:
                    try:
                        local_port = int(response.text)
                    except ValueError:
                        raise ValueError(f'Bad local port: {response.text}')

                    self.client.remote_debug(job.id, local_port)
        except Exception as e:
            rumps.notification('Remote debug error', '', str(e))

    def kill_job(self, job: JobDescription):
        try:
            self.client.job_kill(job.id)
            del self.menu[job.id]
            self.set_active_mode()
        except Exception as e:
            rumps.notification('Failed to kill the job', '', str(e))

    def create_preset(self, *args):
        preset = {
            'id': str(uuid4()),
            'name': '',
            'job_params': ''
        }

        while True:
            preset_name_window_builder.default_text = preset['name']
            preset_name_window_builder.ok = 'Next'
            response = preset_name_window_builder.build().run()

            if not response.clicked:
                return

            preset['name'] = response.text

            preset_params_window_builder.default_text = preset['job_params']
            preset_params_window_builder.ok = 'Create'
            preset_params_window_builder.cancel = 'Prev'
            response = preset_params_window_builder.build().run()

            if response.clicked:
                preset['job_params'] = response.text
                self.update_preset(preset)
                self.render_menu()
                return

    def submit_preset(self, preset: dict):
        job_description_window_builder.default_text = preset['name']
        response = job_description_window_builder.build().run()

        if response.clicked:
            try:
                params = f'-d \"{response.text}\" ' + preset['job_params']
                self.client.submit_raw(params)
                self.set_active_mode()
            except Exception as e:
                rumps.notification('Failed to create new job', '', str(e))

    def update_preset(self, preset: dict, remove: bool = False):
        with Settings(self.settings_path) as settings:
            new_presets = []
            is_found = False

            for it in settings['presets']:
                if it['id'] == preset['id']:
                    is_found = True
                    if not remove:
                        new_presets.append(preset)
                else:
                    new_presets.append(it)

            if not is_found and not remove:
                new_presets.append(preset)

            settings['presets'] = new_presets

    def rename_preset(self, preset: dict):
        preset_name_window_builder.default_text = preset['name']
        preset_name_window_builder.ok = 'Save'
        response = preset_name_window_builder.build().run()

        if response.clicked:
            preset['name'] = response.text
            self.update_preset(preset)
            self.render_menu()

    def change_preset(self, preset: dict):
        preset_params_window_builder.default_text = preset['job_params']
        preset_params_window_builder.ok = 'Save'
        preset_params_window_builder.cancel = 'Cancel'
        response = preset_params_window_builder.build().run()

        if response.clicked:
            preset['job_params'] = response.text
            self.update_preset(preset)
            self.render_menu()

    def remove_preset(self, preset: dict):
        self.update_preset(preset, remove=True)
        self.render_menu()

    def render_job_item(self, job: JobDescription):
        job_name = job.description if job.description else job.id
        item = rumps.MenuItem(job_name, lambda *args, **kwargs: pyperclip.copy(job.id))
        item.set_icon(get_icon(job.status), dimensions=(12, 12))

        item.add(rumps.MenuItem(f'Id: {job.id}'))
        item.add(rumps.MenuItem(f'Status: {job.status}'))
        item.add(rumps.MenuItem(f'Image: {job.image}'))
        item.add(rumps.MenuItem(f'CPU: {job.resources.cpu}'))

        if job.resources.gpu:
            item.add(rumps.MenuItem(f'GPU: {int(job.resources.gpu)} ({job.resources.gpu_model})'))

        item.add(rumps.MenuItem(f'Memory: {job.resources.memory}'))

        if job.resources.shm:
            item.add(rumps.MenuItem('Extshm: true'))

        item.add(rumps.separator)

        if job.ssh:
            item.add(rumps.MenuItem('Remote debug...', lambda _: self.remote_debug(job)))

        if job.url:
            item.add(rumps.MenuItem('Open link', lambda _: webbrowser.open(str(job.url))))

        if job.ssh:
            item.add(rumps.MenuItem('Connect SSH', lambda _: self.connect_ssh(job)))

        item.add(rumps.MenuItem('Kill', lambda _: self.kill_job(job)))
        return item

    def render_preset_item(self, preset) -> rumps.MenuItem:
        item = rumps.MenuItem(preset['name'])
        item.add(rumps.MenuItem('Submit...', lambda *args: self.submit_preset(preset)))
        item.add(rumps.MenuItem('Rename...', lambda *args: self.rename_preset(preset)))
        item.add(rumps.MenuItem('Change job...', lambda *args: self.change_preset(preset)))
        item.add(rumps.MenuItem('Remove', lambda *args: self.remove_preset(preset)))
        return item

    def render_presets_item(self) -> rumps.MenuItem:
        item = rumps.MenuItem('Presets')

        with Settings(self.settings_path) as settings:
            presets = settings['presets']

        for preset in presets:
            item.add(self.render_preset_item(preset))

        if len(presets) == 0:
            item.add(rumps.MenuItem('No presets'))

        item.add(rumps.separator)
        item.add(rumps.MenuItem('Create preset...', self.create_preset))
        return item

    def render_menu(self):
        quit_button = self.menu.get('Quit')
        self.menu.clear()

        self.menu.add(rumps.MenuItem(self.ABOUT))
        self.menu.add(rumps.separator)

        # Active jobs sorted by created time
        jobs = sorted(self.client.get_active_jobs(), key=lambda it: datetime.fromisoformat(it.history.created_at))

        if jobs:
            for job in jobs:
                self.menu.add(self.render_job_item(job))
        else:
            self.menu.add(rumps.MenuItem('No active jobs'))

        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem('Create job...', self.create_job))
        self.menu.add(self.render_presets_item())
        self.menu.add(quit_button)

    @staticmethod
    def show_updates(updates: List[StatusUpdate or NewJobUpdate]):
        for update in updates:
            if isinstance(update, StatusUpdate):
                reason = f' ({update.reason})' if update.reason else ''
                rumps.notification('Job status has changed', update.job_id, f'New status: {update.status}{reason}')

            if isinstance(update, NewJobUpdate):
                reason = f' ({update.reason})' if update.reason else ''
                rumps.notification('New job is created', update.job_id, f'Status: {update.status}{reason}')

    @rumps.timer(UPDATE_DELAY)
    def update(self, timer: rumps.Timer):
        self.iteration += 1

        if self.iteration < self.update_cycle_len:
            return

        self.iteration = 0
        self.update_cycle_len = min(2 * self.update_cycle_len, self.MAX_UPDATE_CYCLE_LEN)

        try:
            updates = self.client.update()
            self.show_updates(updates)
        except ValueError as e:
            rumps.notification('Failed to get updates', '', str(e))
        except Exception as e:
            # Ignore Internet connection problems
            pass

        self.render_menu()
