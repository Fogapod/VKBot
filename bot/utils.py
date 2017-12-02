# coding:utf8


import json
import os

from kivy import platform
from kivy.config import Config

from libs.toast import toast

IS_VERSION_DEV = True

__version__ = '0.1.1dev'


if platform == 'android':
    MAIN_DIR = '/sdcard/VKBot/'

    if IS_VERSION_DEV:
        ROOT = '/sdcard/org.fogaprod.vkbot.dev/'
    else:
        ROOT = '/data/user/0/org.fogaprod.vkbot/'
else:
    MAIN_DIR = ''
    ROOT = ''

DATA_DIR = ROOT + 'data/'

TOKEN_FILE                     = DATA_DIR + 'token'

OLD_TOKEN_FILE                 = DATA_DIR + 'token.txt'

PLUGIN_DIR                     = ROOT     + 'bot/plugins/'
CUSTOM_PLUGIN_DIR              = MAIN_DIR + 'plugins/'
SETTINGS_FILE                  = MAIN_DIR + '.vkbot.ini'
ERROR_FILE                     = MAIN_DIR + 'error.log'
BOT_ERROR_FILE                 = MAIN_DIR + 'bot_error.log'
WHITELIST_FILE                 = MAIN_DIR + 'whitelist.json'
BLACKLIST_FILE                 = MAIN_DIR + 'blacklist.json'
CUSTOM_COMMANDS_FILE           = MAIN_DIR + 'custom_commands.json'

OLD_WHITELIST_FILE             = MAIN_DIR + 'whitelist.txt'
OLD_BLACKLIST_FILE             = MAIN_DIR + 'blacklist.txt'
OLD_CUSTOM_COMMANDS_FILE       = MAIN_DIR + 'custom_commands.txt'

TEMP_IMAGE_FILE                = MAIN_DIR + '.temp.jpg'


CUSTOM_COMMAND_OPTIONS_COUNT = 5


def toast_notification(text, length_long=True):
    toast(text, length_long=length_long)


def safe_format(s, *args, **kwargs):
    '''
    https://stackoverflow.com/questions/9955715/python-missing-arguments-in-string-formatting-lazy-eval
    '''

    while True:
        try:
            return s.format(*args, **kwargs)
        except KeyError as e:
            e = e.args[0]
            kwargs[e] = '{%s}' % e
        except:
            return s


def load_token():
    if not os.path.exists(TOKEN_FILE):
        open(TOKEN_FILE, 'w').close()
        return None
    else:
        try:
            with open(TOKEN_FILE, 'r') as f:
                token = f.readlines()[0][:-1]
            return token
        except:
            return None


def save_token(token):
    if not token and token is not '':
        return

    with open(TOKEN_FILE, 'w') as f:
        f.write('{}\n{}'.format(
            token, 'НИКОМУ НЕ ПОКАЗЫВАЙТЕ СОДЕРЖИМОЕ ЭТОГО ФАЙЛА')
        )


def load_custom_commands():
    if not os.path.exists(CUSTOM_COMMANDS_FILE):
        with open(CUSTOM_COMMANDS_FILE, 'w') as f:
            f.write('{\n\n}')
        return {}
    else:
        with open(CUSTOM_COMMANDS_FILE, 'r') as f:
            try:
                content = json.load(f)
            except ValueError:
                return False

            if type(content) is dict:
                return content
            else:
                return False


def save_custom_commands(content):
    with open(CUSTOM_COMMANDS_FILE, 'w') as f:
        try:
            f.write(json.dumps(content, ensure_ascii=False).encode('utf8'))
        except (UnicodeEncodeError, UnicodeDecodeError):
            print('Error saving custom commands file. Reverting')
            f.truncate(0)
            f.write(
                json.dumps(
                    load_custom_commands(), ensure_ascii=False
                ).encode('utf8')
            )
            f.close()

            return False

    return True


def load_whitelist():
    if not os.path.exists(WHITELIST_FILE):
        open(WHITELIST_FILE, 'w').close()
        return {}
    else:
        with open(WHITELIST_FILE, 'r') as f:
            content = f.read()

        try:
            content = eval(content)
        except:
            content = {}

        if type(content) is not dict:
            return {}
        else:
            return content

    return whitelist


def save_whitelist(whitelist):
    with open(WHITELIST_FILE, 'w') as f:
        f.write(str(whitelist))

    return True


def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE):
        open(BLACKLIST_FILE, 'w').close()
        return {}
    else:
        with open(BLACKLIST_FILE, 'r') as f:
            content = f.read()

        try:
            content = eval(content)
        except:
            content = {}

        if type(content) is not dict:
            return {}
        else:
            return content


def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, 'w') as f:
        f.write(str(blacklist))

    return True


def save_error(error_text, from_bot=False):
    if from_bot:
        try:
            with open(BOT_ERROR_FILE, 'w') as f:
                f.write(error_text.decode('utf8').encode('utf8'))
        except UnicodeEncodeError:
            with open(BOT_ERROR_FILE, 'w') as f:
                f.write(error_text.encode('utf8'))
    else:
        try:
            with open(ERROR_FILE, 'w') as f:
                f.write(error_text.decode('utf8').encode('utf8'))
        except UnicodeEncodeError:
            with open(ERROR_FILE, 'w') as f:
                f.write(error_text.encode('utf8'))


def load_bot_settings():
    settings = {}
    Config.read(SETTINGS_FILE)

    appeals = []
    for appeal in Config.get('General', 'appeals').split(':'):
        if appeal:
            appeals.append(appeal.lower())

    settings['appeals'] = tuple(appeals)

    settings['bot_name'] = Config.get('General', 'bot_name')
    settings['mark_type'] = Config.get('General', 'mark_type')
    settings['use_custom_commands'] = \
        Config.get('General', 'use_custom_commands') == 'True'
    settings['stable_mode'] = Config.get('General', 'stable_mode') == 'True'
    settings['openweathermap_api_key'] = \
        Config.get('General', 'openweathermap_api_key')

    return settings


def save_bot_setting(section, key, value):
    Config.read(SETTINGS_FILE)
    Config.set(section, key, value)
    Config.write()