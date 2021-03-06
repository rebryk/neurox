from functools import wraps
from typing import Callable

from rumps import Window
from rumps.rumps import Response

from neurox.utils import get_icon
from .alert import Alert


def autorun(func: Callable, icon: str = 'icon'):
    @wraps(func)
    def wrapper(*args, **kwargs) -> Response:
        window = func(*args, **kwargs)
        window.icon = get_icon(icon)
        return window.run()

    return wrapper


class Windows:
    @staticmethod
    @autorun
    def create_job(params: str) -> Window:
        return Window(title='Create job',
                      message='Specify job parameters',
                      default_text=params,
                      ok='Next',
                      cancel='Cancel',
                      dimensions=(300, 100))

    @staticmethod
    @autorun
    def job_description(description: str, cancel: str = 'Cancel') -> Window:
        return Window(title='Job description',
                      message='Enter job description',
                      default_text=description,
                      ok='Submit',
                      cancel=cancel,
                      dimensions=(300, 23))

    @staticmethod
    @autorun
    def kill_job() -> Alert:
        return Alert(title='Are you sure?',
                     message='Do you want to kill the job?',
                     ok='Yes',
                     cancel='Cancel')

    @staticmethod
    @autorun
    def port(port: str) -> Window:
        return Window(title='Enter local port',
                      default_text=port,
                      ok='Connect',
                      cancel='Cancel',
                      dimensions=(300, 23))

    @staticmethod
    @autorun
    def preset_name(name: str, ok: str) -> Window:
        return Window(title='Preset settings',
                      message='Enter preset name',
                      default_text=name,
                      ok=ok,
                      cancel='Cancel',
                      dimensions=(300, 23))

    @staticmethod
    @autorun
    def preset_params(params: str, ok: str, cancel: str) -> Window:
        return Window(title='Preset settings',
                      message='Specify job parameters',
                      default_text=params,
                      ok=ok,
                      cancel=cancel,
                      dimensions=(300, 100))

    @staticmethod
    @autorun
    def remove_preset() -> Alert:
        return Alert(title='Are you sure?',
                     message='Do you want to remove the preset?',
                     ok='Yes',
                     cancel='Cancel')

    @staticmethod
    @autorun
    def auth(auth: str) -> Window:
        return Window(title='Settings',
                      message='Specify neuromation API token',
                      default_text=auth,
                      ok='Save',
                      cancel='Cancel',
                      dimensions=(300, 70))

    @staticmethod
    @autorun
    def username(username: str) -> Window:
        return Window(title='Settings',
                      message='Specify neuromation username',
                      default_text=username,
                      ok='Save',
                      cancel='Cancel',
                      dimensions=(300, 23))

    @staticmethod
    @autorun
    def url(url: str) -> Window:
        return Window(title='Settings',
                      message='Specify neuromation API URL',
                      default_text=url,
                      ok='Save',
                      cancel='Cancel',
                      dimensions=(300, 23))

    @staticmethod
    @autorun
    def rsa_path(rsa_path: str) -> Window:
        return Window(title='Settings',
                      message='Specify RSA key path',
                      default_text=rsa_path,
                      ok='Save',
                      cancel='Cancel',
                      dimensions=(300, 23))


__all__ = ['Windows']
