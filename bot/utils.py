# coding:utf8


import json
import re
import os
import time

from kivy import platform

from libs.toast import toast

# GLOBALS

PATH = '/sdcard/VKBot/' if platform == 'android' else ''
DATA_PATH = 'data/'

ERROR_FILE_PATH = ''
TOKEN_FILE_PATH = ''
SETTINGS_FILE_PATH = ''
WHITELIST_FILE_PATH = ''
BLACKLIST_FILE_PATH = ''
BOT_ERROR_FILE_PATH = ''
CUSTOM_COMMANDS_FILE_PATH = ''


def update_paths():
    global ERROR_FILE_PATH
    global TOKEN_FILE_PATH
    global SETTINGS_FILE_PATH
    global WHITELIST_FILE_PATH
    global BLACKLIST_FILE_PATH
    global BOT_ERROR_FILE_PATH
    global CUSTOM_COMMANDS_FILE_PATH

    ERROR_FILE_PATH = PATH + 'error.log'
    TOKEN_FILE_PATH = DATA_PATH + 'token.txt'
    SETTINGS_FILE_PATH = PATH + '.vkbot.ini'
    WHITELIST_FILE_PATH = PATH + 'whitelist.txt'
    BLACKLIST_FILE_PATH = PATH + 'blacklist.txt'
    BOT_ERROR_FILE_PATH = PATH + 'bot_error.log'
    CUSTOM_COMMANDS_FILE_PATH = PATH + 'custom_commands.txt'

update_paths()


CUSTOM_COMMAND_OPTIONS_COUNT = 5


def toast_notification(text, length_long=True):
    toast(text, length_long=length_long)


def load_token():
    token = None
    if not os.path.exists(TOKEN_FILE_PATH):
        open(TOKEN_FILE_PATH, 'w').close()
    else:
        try:
            with open(TOKEN_FILE_PATH, 'r') as f:
                token = f.readlines()[0][:-1]
        except:
            return token

    return token


def save_token(token):
    if not token:
        token = ''

    with open(TOKEN_FILE_PATH, 'w') as f:
        f.write('{}\n{}'.format(
            token, 'НИКОМУ НЕ ПОКАЗЫВАЙТЕ СОДЕРЖИМОЕ ЭТОГО ФАЙЛА')
        )


def load_custom_commands():
    if not os.path.exists(CUSTOM_COMMANDS_FILE_PATH):
        with open(CUSTOM_COMMANDS_FILE_PATH, 'w') as f:
            f.write('{\n\n}')
        return {}
    else:    
        with open(CUSTOM_COMMANDS_FILE_PATH, 'r') as f:
            try:
                content = json.load(f)
            except ValueError:
                return False

            if type(content) is dict:
                return content
            else:
                return False


def save_custom_commands(content):
    last_content = load_custom_commands()
    with open(CUSTOM_COMMANDS_FILE_PATH, 'w') as f:
        try:
            f.write(json.dumps(content, ensure_ascii=False).encode('utf8'))
        except (UnicodeEncodeError, UnicodeDecodeError):
            print('Error saving custom commands file. Reverting')
            f.truncate(0)
            f.write(
                json.dumps(last_content, ensure_ascii=False).encode('utf8')
            )
            f.close()

            return False

    return True


def load_whitelist():
    if not os.path.exists(WHITELIST_FILE_PATH):
        open(WHITELIST_FILE_PATH, 'w').close()
        return {}
    else:    
        with open(WHITELIST_FILE_PATH, 'r') as f:
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
    with open(WHITELIST_FILE_PATH, 'w') as f:
        f.write(str(whitelist))

    return True


def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE_PATH):
        open(BLACKLIST_FILE_PATH, 'w').close()
        return {}
    else:    
        with open(BLACKLIST_FILE_PATH, 'r') as f:
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
    with open(BLACKLIST_FILE_PATH, 'w') as f:
        f.write(str(blacklist))

    return True


def save_error(error_text, from_bot=False):
    if from_bot:
        try:
            with open(BOT_ERROR_FILE_PATH, 'w') as f:
                f.write(error_text.decode('utf8').encode('utf8'))
        except UnicodeEncodeError:
            with open(BOT_ERROR_FILE_PATH, 'w') as f:
                f.write(error_text.encode('utf8'))
    else:
        try:
            with open(ERROR_FILE_PATH, 'w') as f:
                f.write(error_text.decode('utf8').encode('utf8'))
        except UnicodeEncodeError:
            with open(ERROR_FILE_PATH, 'w') as f:
                f.write(error_text.encode('utf8'))
