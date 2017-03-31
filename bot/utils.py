# -*- coding: utf-8 -*-


import re
import time
import os
import json

from kivy import platform


__all__ = (
    'PATH',
    'DATA_PATH',
    'parse_input',
    'load_custom_commands',
    'save_custom_commands'
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

def load_custom_commands():
    if not os.path.exists(PATH +  'presets.txt'):
        with open(PATH + 'presets.txt', 'w') as p:
            p.write('{\n\n}')
        return {}
    else:    
        with open(PATH + 'presets.txt', 'r') as p:
            try:
                content = json.load(p)
            except ValueError:
                return False

            if type(content) is dict:
                return content
            else:
                return False

def save_custom_commands(content):
    with open(PATH + 'presets.txt', 'r+') as p:
        try:
            p.truncate(0)
            p.write(json.dumps(content, sort_keys=True, indent=0, ensure_ascii=False).encode('utf8'))
        except UnicodeEncodeError:
            p.close()
            return False