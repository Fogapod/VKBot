# -*- coding: utf-8 -*-


import re
import time
import os
import json

from kivy import platform

from libs.toast import toast


__all__ = (
    'PATH',
    'DATA_PATH',
    'parse_input',
    'load_custom_commands',
    'save_custom_commands',
    'toast_notification'
    )

PATH = '/sdcard/VKBot/' if platform == 'android' else ''
DATA_PATH = 'data/'


def parse_input(string, replace_vkurl=True, replace_url=True):
	new_string = string

	if replace_vkurl:
		new_string = re.sub(r'\b(https?://)?m\.?vk\.com/?.*\b',
			'__vkurl__', # поиск ссылок vk.com
			new_string
		)

	if replace_url:
		new_string = re.sub(
		r'''(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/?)(?:[^\s()<>]+|(([^\s()<>]+|(([^\s()<>]+)))*))+(?:(([^\s()<>]+|(([^\s()<>]+)))*)|[^\s`!()[]{};:'".,<>?«»“”‘’]))'''
		, '__url__', # поиск всех остальных ссылок
		new_string
	)

	return new_string

def toast_notification(text, length_long=True):
    toast(text, length_long=length_long)

def load_custom_commands():
    if not os.path.exists(PATH +  'presets.txt'):
        with open(PATH + 'presets.txt', 'w') as f:
            f.write('{\n\n}')
        return {}
    else:    
        with open(PATH + 'presets.txt', 'r') as f:
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
    with open(PATH + 'presets.txt', 'w') as f:
        try:
            f.write(json.dumps(content, sort_keys=True, indent=0, ensure_ascii=False).encode('utf8'))
        except (UnicodeEncodeError, UnicodeDecodeError):
            print('Error saving custom commands file. Reverting')
            f.truncate(0)
            f.write(json.dumps(last_content, sort_keys=True, indent=0, ensure_ascii=False).encode('utf8'))
            f.close()
            return False
    return True

def load_blacklist():
    blacklist = []
    if not os.path.exists(PATH +  'blacklist.txt'):
        with open(PATH + 'blacklist.txt', 'w') as f:
            pass
    else:    
        with open(PATH + 'blacklist.txt', 'r') as f:
            for line in f.readlines():
                if line:
                    blacklist.append(line)
    return blacklist

def save_blacklist(blacklist):
    with open(PATH + 'blacklist.txt', 'w') as f:
        f.write('\n'.join(blacklist))
    return True
