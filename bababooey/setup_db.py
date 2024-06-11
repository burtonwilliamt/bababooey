import os
import shelve


def _check_or_create_data_dir():
    if not os.path.exists("data/"):
        os.makedirs("data/")


def setup_db():
    _check_or_create_data_dir()
    with shelve.open("data/sfx_data") as s:
        if "data" not in s:
            s["data"] = []
