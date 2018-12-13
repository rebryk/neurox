import rumps

from neurox.client import NewJobUpdate, StatusUpdate, JobDescription, NeuroxClient
from neurox.settings import load_settings, save_settings
from neurox.utils import get_icon
from neurox.windows import TokenRequestWindow, CreateJobWindow


class NeuroxApp(rumps.App):
    UPDATE_DELAY = 2
    VERSION = '0.1'
    ABOUT = f'NeuroX (version {VERSION}) by Rebryk'

    def __init__(self, *args, **kwargs):
        super().__init__('Neurox', *args, icon=get_icon('icon'), **kwargs)
        self.client = None
        self.settings = None

    def initialize(self):
        self.settings = load_settings(self)
        token = self.settings['token']

        while self.client is None:
            if token is None:
                response = TokenRequestWindow().run()
                token = str(response.text)

            try:
                self.client = NeuroxClient(self.settings['url'], token)
                rumps.notification('Successful authentication', '', 'You have successfully connected to the platform')
                self.settings['token'] = token
                save_settings(self)
            except Exception:
                token = None
                rumps.notification('Authentication error', '', 'Try to use another token')

    def create_job(self, *args, **kwargs):
        response = CreateJobWindow(self.settings['job_params']).run()

        if response.clicked:
            self.settings['job_params'] = str(response.text)
            save_settings(self)

            exitcode, out, err = self.client.submit_raw(self.settings['job_params'])

            if exitcode != 0:
                rumps.notification('Failed to submit the job', '', 'You may be using the wrong parameters')

    def kill_job(self, job_id: str, *args, **kwargs):
        del self.menu[job_id]
        self.client.kill(job_id)

    def render_job_item(self, job: JobDescription):
        item = rumps.MenuItem(job.id)
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
        item.add(rumps.MenuItem('Kill', lambda *args, **kwargs: self.kill_job(job.id, *args, **kwargs)))
        return item

    def render_menu(self):
        quit_button = self.menu.get('Quit')
        self.menu.clear()

        self.menu.add(rumps.MenuItem(self.ABOUT))
        self.menu.add(rumps.separator)

        for job in self.client.get_active_jobs():
            self.menu.add(self.render_job_item(job))

        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem('Create job...', self.create_job))
        self.menu.add(quit_button)

    @rumps.timer(UPDATE_DELAY)
    def update(self, *args, **kwargs):
        if self.client is None:
            self.initialize()

        updates = self.client.update()

        for update in updates:
            if isinstance(update, StatusUpdate):
                rumps.notification('Job status has changed', update.job_id, f'New status: {update.status}')

            if isinstance(update, NewJobUpdate):
                rumps.notification('New job is created', update.job_id, f'Status: {update.status}')

        self.render_menu()
