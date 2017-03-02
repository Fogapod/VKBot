#-*- coding: utf-8 -*-
#qpy:kivy
import traceback
import os

from program import ChatBot
from __init__ import PATH

def main():
    try:
        if not os.path.exists(PATH):
            os.makedirs(PATH)    
        ChatBot().run()
    except Exception:
        error_text = traceback.format_exc()
        open(PATH + 'error.log', 'w').write(error_text)
        print(error_text)

if __name__ == '__main__':
    main()
