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
from neurox.windows import job_window_builder, local_port_window_builder


class NeuroxApp(rumps.App):
    UPDATE_DELAY = 1
    MAX_UPDATE_CYCLE_LEN = 30
    VERSION = '0.1'
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
            response = local_port_window_builder.build().run()

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

    def render_job_item(self, job: JobDescription):
        item = rumps.MenuItem(job.id, lambda *args, **kwargs: pyperclip.copy(job.id))
        item.set_icon(get_icon(job.status), dimensions=(12, 12))

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
            item.add(rumps.MenuItem('Open link', lambda _: webbrowser.open(job.url)))

        if job.ssh:
            item.add(rumps.MenuItem('Connect SSH', lambda _: self.connect_ssh(job)))

        item.add(rumps.MenuItem('Kill', lambda _: self.kill_job(job)))
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
        self.menu.add(quit_button)

    @staticmethod
    def show_updates(updates: List[StatusUpdate or NewJobUpdate]):
        for update in updates:
            if isinstance(update, StatusUpdate):
                rumps.notification('Job status has changed', update.job_id, f'New status: {update.status}')

            if isinstance(update, NewJobUpdate):
                rumps.notification('New job is created', update.job_id, f'Status: {update.status}')

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
