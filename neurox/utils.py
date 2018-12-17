import os
import stat


def get_resource_dir():
    return 'resources'


def get_icon(name: str) -> str:
    return f'{get_resource_dir()}/{name}.png'


def make_executable(path: str):
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)
