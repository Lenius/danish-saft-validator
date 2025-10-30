import configparser

from modules.conventions.text_lang import Language, Texts
from modules.conventions.file_system import FileSystem


def write_config(language):
    config = configparser.ConfigParser()

    config['Settings'] = {'language': language}
    with open(FileSystem.config, 'w') as configfile:
        config.write(configfile)


def load_config():
    config = configparser.ConfigParser()
    config.read(FileSystem.config)
    return config


def get_language():
    config = load_config()
    config.get('Settings', 'language')
    return [x for x in Language if x.value == config.get('Settings', 'language')][0]


def create_config():
    language = None
    print("Welcome to the language configuration setup.")
    while language not in [val.value for val in Language]:
        language = input("Enter your preferred language code (dk/en): ")
    write_config(language)
    language = get_language()
    print(Texts.config_completed[language])


if __name__ == '__main__':
    create_config()
