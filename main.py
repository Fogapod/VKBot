# coding:utf8


import traceback
import os

from program import VKBotApp
from bot import utils


def main():
    app = None

    try:
        if not os.path.exists(utils.PATH) and utils.PATH:
            os.makedirs(utils.PATH)
        if not os.path.exists(utils.DATA_PATH):
            os.makedirs(utils.DATA_PATH)

        app = VKBotApp()
        app.run()
    except Exception:
        error_text = traceback.format_exc()
        utils.save_error(error_text)

        if app:
            try:
                app.stop()
            except AttributeError:
                pass

        from kivy.base import runTouchApp
        from uix.screens.exceptionscreen import ExceptionScreen

        error_text += u'\nОшибка записана в файл %s' % utils.ERROR_FILE_PATH
        runTouchApp(ExceptionScreen(exception_text=error_text))

if __name__ == '__main__':
    main()
