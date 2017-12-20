import toml
from os import path as ospath

CONFIG = {}

def check_possible_path():
    config_path = 'config/backuprestore.example'
    paths = [
        "/etc/backuprestore.conf",
        ospath.expanduser("~/.config/backuprestore.conf"),
        ospath.expanduser("~/.backuprestorerc"),
        "backuprestore.conf"
    ]
    for path in paths:
        if ospath.exists(path):
            config_path = path
    return config_path

def init(path):
    global CONFIG
    CONFIG = toml.load(path)
