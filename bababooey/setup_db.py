import os

def _check_or_create_data_dir():
    if not os.path.exists('data/'):
        os.makedirs('data/')

def setup_db():
    _check_or_create_data_dir()