# coding:utf8

import os
from time import sleep
import sys

from kivy import platform
from kivy.logger import Logger
from kivy.config import Config
from kivy.lib import osc

import logging
logging.captureWarnings(True)

parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parent_path += '\\' if platform == 'win' else '/'
os.sys.path.append(parent_path)

import bot.utils
if platform != 'android':
    bot.utils.PATH = parent_path + bot.utils.PATH
bot.utils.DATA_PATH = parent_path + bot.utils.DATA_PATH

bot.utils.update_paths()

from bot.core import LongPollSession


def ping(*args):
    global session
    if session.running:
        osc.sendMsg('/pong', [], port=3002)

def send_text(text):
    osc.sendMsg('/text', [text, ], port=3002)

def send_status(status):
    osc.sendMsg('/status', [status, ], port=3002)

def send_error(error):
    error_text = unicode(error)
    osc.sendMsg('/error', [error_text, ], port=3002)
    Logger.info(error_text)

def send_answers_count():
    osc.sendMsg('/answers', [session.reply_count, ], port=3002)

def exit(*args):
    send_status('exiting')
    session.runtime_error = 1
    sys.exit()


if __name__ == '__main__':
    osc.init()
    oscid = osc.listen(ipAddr='0.0.0.0', port=3000)
    send_status('connected')

    osc.bind(oscid, ping, '/ping')
    osc.bind(oscid, exit, '/exit')

    session = LongPollSession()
    authorized, error = session.authorization()

    if error:
        send_error(error)
        exit()

    Config.read(bot.utils.PATH + '.vkbot.ini')
    appials = Config.get('General', 'appeals')
    activated = Config.get('General', 'bot_activated')
    use_custom_commands = Config.get('General', 'use_custom_commands')
    protect_custom_commands = Config.get('General', 'protect_cc')

    
    session.load_params(
    	            appials,
    	            activated=activated == 'True',
                use_custom_commands=use_custom_commands == 'True',
                protect_custom_commands=protect_custom_commands == 'True'
                )
    send_status('got params')
    session.launch_bot()

    while True:
        osc.readQueue(oscid)
        send_answers_count()
        if session.activated != activated:
            activated = session.activated
            osc.sendMsg('/activation_changed', [str(activated), ], port=3002)
        if session.runtime_error:
            send_error(session.runtime_error)
            break
        if not session.running:
            break
        sleep(1)
    exit()
