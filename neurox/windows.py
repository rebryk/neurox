import rumps

from neurox.utils import get_icon


class TokenRequestWindow(rumps.Window):
    def __init__(self):
        super().__init__(title='Enter your token', ok='Connect', dimensions=(300, 50))
        self.icon = get_icon('icon')


class LocalPortWindow(rumps.Window):
    def __init__(self):
        super().__init__(title='Enter', ok='Connect', cancel='Cancel', default_text='1489', dimensions=(300, 23))
        self.icon = get_icon('icon')


class CreateJobWindow(rumps.Window):
    def __init__(self, job_params: str = ''):
        super().__init__(message='Specify job parameters',
                         title='Create job',
                         default_text=job_params,
                         ok='Submit',
                         cancel='Cancel',
                         dimensions=(300, 100))
        self.icon = get_icon('icon')
