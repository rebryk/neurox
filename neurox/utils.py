def get_resource_dir():
    return 'resources'


def get_icon(name: str) -> str:
    return f'{get_resource_dir()}/{name}.png'
