# -*- coding: utf-8 -*-


import re
import time
import os
import json

from kivy import platform

from plyer import notification
from libs.toast import toast


__all__ = (
    'PATH',
    'DATA_PATH',
    'parse_input',
    'load_custom_commands',
    'save_custom_commands',
    'statusbar_notification',
    'bot_launched_notification',
    'bot_stopped_notification',
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

def statusbar_notification(title='VKBot', message=''):
    notification.notify(title=title, message=message)

def bot_launched_notification():
    statusbar_notification(u'Бот запущен')

def bot_stopped_notification():
    statusbar_notification(u'Бот остановлен')

def toast_notification(text, length_long=False):
    toast(text, length_long=length_long)

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
        last_content = p.read()
        p.truncate(0)
        try:
            p.write(json.dumps(content, sort_keys=True, indent=0, ensure_ascii=False).encode('utf8'))
        except (UnicodeEncodeError, UnicodeDecodeError):
            p.truncate(0)
            p.write(last_content)
            p.close()
            return False