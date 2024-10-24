import configparser
from pathlib import Path

config = configparser.ConfigParser()
path_of_settings = Path(__file__).parent.parent.joinpath('settings.ini')
config.read(path_of_settings)


class DBConfig:
    def __init__(self):
        self.echo_mode: bool = self.str_to_bool(config['Database']['echo_mode'])

    @staticmethod
    def str_to_bool(arg):
        if arg in ('True', 'true', 'TRUE', '1', 'yes'):
            return True
        elif arg in ('False', 'false', 'FALSE', '0', 'no'):
            return False
        else:
            raise ValueError('Argument must be either True or False')


dbconf = DBConfig()
