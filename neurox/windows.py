from typing import Tuple

import rumps

from neurox.utils import get_icon


class WindowBuilder:
    def __init__(self,
                 message: str = '',
                 title: str = '',
                 default_text: str = '',
                 ok: str = None,
                 cancel: str = None,
                 dimensions: Tuple[int, int] = (320, 160)):
        self.message = message
        self.title = title
        self.default_text = default_text
        self.ok = ok
        self.cancel = cancel
        self.dimensions = dimensions

    def build(self) -> rumps.Window:
        window = rumps.Window(message=self.message,
                              title=self.title,
                              default_text=self.default_text,
                              ok=self.ok,
                              cancel=self.cancel,
                              dimensions=self.dimensions)
        window.icon = get_icon('icon')
        return window


port_window_builder = WindowBuilder(title='Enter local port',
                                    ok='Connect',
                                    cancel='Cancel',
                                    default_text='1489',
                                    dimensions=(300, 23))

job_window_builder = WindowBuilder(message='Specify job parameters',
                                   title='Create job',
                                   ok='Submit',
                                   cancel='Cancel',
                                   dimensions=(300, 100))

preset_name_window_builder = WindowBuilder(message='Enter preset name',
                                           title='Preset settings',
                                           cancel='Cancel',
                                           dimensions=(300, 23))

preset_params_window_builder = WindowBuilder(message='Enter job params',
                                             title='Preset settings',
                                             dimensions=(300, 100))

job_description_window_builder = WindowBuilder(message='Enter job description',
                                               title='Job description',
                                               ok='Submit',
                                               cancel='Cancel',
                                               dimensions=(300, 23))
