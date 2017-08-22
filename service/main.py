# coding:utf8


import os
import sys
import logging
import traceback

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
    global stable_mode

    Config.read(utils.SETTINGS_FILE_PATH)

    appeals = Config.get('General', 'appeals')
    activated = Config.get('General', 'bot_activated') == 'True'
    bot_name = Config.get('General', 'bot_name')
    mark_type = Config.get('General', 'mark_type')
    use_custom_commands = Config.get('General', 'use_custom_commands') == 'True'
    stable_mode = Config.get('General', 'stable_mode') == 'True'
    openweathermap_api_key = Config.get('General', 'openweathermap_api_key')

    bot.load_params(appeals,
        activated=activated,
        bot_name=bot_name, mark_type=mark_type,
        use_custom_commands=use_custom_commands,
        openweathermap_api_key=openweathermap_api_key
    )


def pong(*args):
    global bot
    if bot.running:
        osc.sendMsg('/pong', [], port=3002)


def send_status(status):
    osc.sendMsg('/status', [status, ], port=3002)


def send_error(error):
    osc.sendMsg('/error', [error, ], port=3002)


def send_answers_count(*args):
    osc.sendMsg('/answers', [bot.reply_count, ], port=3002)


def send_log_line(line, log_importance):
    osc.sendMsg('/log', [str((line, log_importance)), ], port=3002)


def exit(*args):
    global bot
    bot.stop_bot()
    send_status('exiting')
    sys.exit()


if __name__ == '__main__':
    osc.init()
    oscid = osc.listen(ipAddr='0.0.0.0', port=3000)
    send_log_line(u'Служба OSC подключена', 0)

    osc.bind(oscid, pong, '/ping')
    osc.bind(oscid, exit, '/exit')
    osc.bind(oscid, send_answers_count, '/request answers count')

    try:
        bot = Bot()
        send_log_line(u'Попытка авторизации...', 0)
        authorized, error = bot.authorization()

        if error:
            send_log_line(u'Во время авторизации произошла ошибка', 2)
            send_error(error)
            exit()

        send_log_line(u'Авторизация прошла без ошибок', 1)

        send_log_line(u'Загрузка параметров...', 0)
        update_params()
        send_log_line(u'Загрузка параметров завершена', 1)

        send_log_line(u'Включение бота...', 0)
        bot.launch_bot()
        send_status('launched')

    except SystemExit:
        raise
    except:
        send_log_line(u'Обработка и отправка ошибки...', 0)
        error = traceback.format_exc()
        send_error(error)
        exit()

    while True:
        osc.readQueue(oscid)
        if bot.activated != activated:
            activated = bot.activated
            Config.read(utils.SETTINGS_FILE_PATH)
            Config.set('General', 'bot_activated', str(activated))
            send_log_line(u'Начинаю запись нового статуса активации', 0)
            Config.write()
            send_log_line(u'Записан новый статус активации', 1)

        if bot.openweathermap_api_key != openweathermap_api_key:
            openweathermap_api_key = bot.openweathermap_api_key
            Config.read(utils.SETTINGS_FILE_PATH)
            Config.set(
                'General', 'openweathermap_api_key', openweathermap_api_key
            )
            send_log_line(u'Начинаю запись нового ключа openweathermap (погода)', 0)
            Config.write()
            send_log_line(u'Записан новый ключ openweathermap (погода)', 1)

        if bot.runtime_error:
            if bot.runtime_error != 1:
                send_error(bot.runtime_error)
            if stable_mode:
                send_log_line(u'Активирован устойчивый режим. Сброс параметров и повторный запуск бота...', 1)
                bot.runtime_error = None
                bot.stop_bot()
                bot.launch_bot()
                send_log_line(u'Повторный запуск произведён', 0)
                continue
            else:
                break

        if bot.need_restart:
            send_log_line(u'Остановка бота для перезагрузки', 1)
            bot.stop_bot()
            send_log_line(u'Обновление параметров...', 0)
            update_params()
            bot.launch_bot()
            bot.need_restart = False
            send_log_line(u'Перезагрузка окончена', 2)

        elif not bot.running:
            break

        sleep(1)
    exit()
