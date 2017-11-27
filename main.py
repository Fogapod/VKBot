# coding:utf8


import traceback
import os

from program import VKBotApp
from bot import utils


def main():
    app = None

    try:
        if not os.path.exists(utils.MAIN_DIR) and utils.MAIN_DIR:
            os.makedirs(utils.MAIN_DIR)

        app = VKBotApp()

        app.rename_old_files()  # TODO: remove after 0.1.1 release

        app.run()
    except:
        error_text = traceback.format_exc()
        utils.save_error(error_text)

        if app:
            try:
                app.stop()
            except AttributeError:
                pass

        from kivy.base import runTouchApp
        from uix.screens.exceptionscreen import ExceptionScreen

        error_text += u'\nОшибка записана в файл %s' % utils.ERROR_FILE
        runTouchApp(ExceptionScreen(exception_text=error_text))

if __name__ == '__main__':
    main()
