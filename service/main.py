# coding:utf8


import os
import sys
import logging

from time import sleep

from kivy import platform
from kivy.logger import Logger
from kivy.config import Config
from kivy.lib import osc

parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parent_path += '\\' if platform == 'win' else '/'
os.sys.path.append(parent_path)


from bot import utils
from bot.core import Bot

if platform != 'android':
    utils.PATH = parent_path + utils.PATH
utils.DATA_PATH = parent_path + utils.DATA_PATH

utils.update_paths()

logging.captureWarnings(True)


def update_params():
    global activated
    global openweathermap_api_key

    Config.read(utils.SETTINGS_FILE_PATH)
    appeals = Config.get('General', 'appeals')
    activated = Config.get('General', 'bot_activated')
    bot_name = Config.get('General', 'bot_name')
    mark_type = Config.get('General', 'mark_type')
    use_custom_commands = Config.get('General', 'use_custom_commands')
    openweathermap_api_key = Config.get('General', 'openweathermap_api_key')

    bot.load_params(appeals,
        activated=activated == 'True',
        bot_name=bot_name, mark_type=mark_type,
        use_custom_commands=use_custom_commands == 'True',
        openweathermap_api_key=openweathermap_api_key
    )
                        
def ping(*args):
    global bot
    if bot.running:
        osc.sendMsg('/pong', [], port=3002)

def send_status(status):
    osc.sendMsg('/status', [status, ], port=3002)

def send_error(error):
    osc.sendMsg('/error', [error, ], port=3002)

def send_answers_count():
    osc.sendMsg('/answers', [bot.reply_count, ], port=3002)

def exit(*args):
    global bot
    bot.stop_bot()
    send_status('exiting')
    sys.exit()


if __name__ == '__main__':
    osc.init()
    oscid = osc.listen(ipAddr='0.0.0.0', port=3000)
    send_status('connected')

    osc.bind(oscid, ping, '/ping')
    osc.bind(oscid, exit, '/exit')

    try:
        bot = Bot()
        authorized, error = bot.authorization()

        if error:
            send_error(error)
            exit()

        update_params()

        bot.launch_bot()

        send_status('launched')
    except SystemExit:
        raise
    except:
        import traceback
        error = traceback.format_exc()
        send_error(error)
        exit()

    while True:
        osc.readQueue(oscid)
        send_answers_count()
        if bot.activated != activated:
            activated = bot.activated
            Config.read(utils.SETTINGS_FILE_PATH)
            Config.set('General', 'bot_activated', str(activated))
            Config.write()
        if bot.openweathermap_api_key != openweathermap_api_key:
            openweathermap_api_key = bot.openweathermap_api_key
            Config.read(utils.SETTINGS_FILE_PATH)
            Config.set(
                'General', 'openweathermap_api_key', openweathermap_api_key
            )
            Config.write()
        if bot.runtime_error:
            if bot.runtime_error != 1:
                send_error(bot.runtime_error)
            break
        if bot.need_restart:
            bot.stop_bot()
            update_params()
            bot.launch_bot()
            bot.need_restart = False
        elif not bot.running:
            break
        sleep(1)
    exit()
