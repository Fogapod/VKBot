# coding:utf8


import traceback
import os

from program import VKBotApp
from bot.utils import PATH, DATA_PATH, save_error, ERROR_FILE_PATH


def main():
    app = None

    try:
        if not os.path.exists(PATH) and PATH:
            os.makedirs(PATH)
        if not os.path.exists(DATA_PATH):
            os.makedirs(DATA_PATH)

        app = VKBotApp()
        app.run()
    except Exception:
        error_text = traceback.format_exc()
        save_error(error_text)

        if app:
            try:
                app.stop()
            except AttributeError:
                pass

        from kivy.base import runTouchApp
        from uix.screens.exceptionscreen import ExceptionScreen

        error_text += u'\nОшибка записана в файл %s' % ERROR_FILE_PATH
        runTouchApp(ExceptionScreen(exception_text=error_text))

if __name__ == '__main__':
    main()
