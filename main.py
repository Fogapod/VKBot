#-*- coding: utf-8 -*-
#qpy:kivy
from program import ChatBot

import traceback

PATH = '/storage/emulated/0/Git/ChatBot_UI'

def main():
    try:
        ChatBot().run()
    except Exception:
        error_text = traceback.format_exc()
        open(PATH + 'error.log', 'w').write(error_text)
        print(error_text)

if __name__ == '__main__':
    main()
