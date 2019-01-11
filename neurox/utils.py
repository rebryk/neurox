import os
import stat
import sys


def get_icon(name: str) -> str:
    if getattr(sys, 'frozen', False):
        bundle = f'{sys.executable.rsplit("/", 3)[0]}/Contents/Resources/'
    else:
        bundle = f'{os.getcwd()}/resources/'
    return os.path.join(bundle, f'{name}.png')


def make_executable(path: str):
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)
