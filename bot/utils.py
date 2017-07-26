# coding:utf8


import re
import time
import os
import json

from kivy import platform

from libs.toast import toast


PATH = '/sdcard/VKBot/' if platform == 'android' else ''
DATA_PATH = 'data/'


def update_paths():
    global SETTINGS_FILE_PATH
    global ERROR_FILE_PATH
    global BOT_ERROR_FILE_PATH
    global TOKEN_FILE_PATH
    global CUSTOM_COMMANDS_FILE_PATH
    global BLACKLIST_FILE_PATH

    SETTINGS_FILE_PATH = PATH + '.vkbot.ini'
    ERROR_FILE_PATH = PATH + 'error.log'
    BOT_ERROR_FILE_PATH = PATH + 'bot_error.log'
    TOKEN_FILE_PATH = DATA_PATH + 'token.txt'
    CUSTOM_COMMANDS_FILE_PATH = PATH + 'custom_commands.txt'
    BLACKLIST_FILE_PATH = PATH + 'blacklist.txt'

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
            f.write(json.dumps(content, indent=0, ensure_ascii=False).encode('utf8'))
        except (UnicodeEncodeError, UnicodeDecodeError):
            print('Error saving custom commands file. Reverting')
            f.truncate(0)
            f.write(json.dumps(last_content, indent=0, ensure_ascii=False).encode('utf8'))
            f.close()

            return False

    return True

def load_blacklist():
    blacklist = []
    if not os.path.exists(BLACKLIST_FILE_PATH):
        open(BLACKLIST_FILE_PATH, 'w').close()
    else:    
        with open(BLACKLIST_FILE_PATH, 'r') as f:
            for line in f.readlines():
                if line:
                    blacklist.append(line.split()[0])

    return blacklist

def save_blacklist(blacklist):
    with open(BLACKLIST_FILE_PATH, 'w') as f:
        f.write('\n'.join(blacklist))
    return True

def save_error(error_text, from_bot=False):
    if from_bot:
        open(BOT_ERROR_FILE_PATH, 'w').write(error_text.encode('utf8'))
    else:
        open(ERROR_FILE_PATH, 'w').write(error_text.encode('utf8'))
