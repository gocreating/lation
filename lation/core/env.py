import os


def get_env(name:str) -> str:
    return os.environ.get(name)


IMAGE_TAG = get_env('IMAGE_TAG')
DEV = get_env('DEV')
