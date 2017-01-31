from program import ChatBot
from bot_core import Bot
from bot_core import LongPollSession

import sys
import traceback

PATH = '' # '/storage/emulated/0/Git/ChatBot_UI/'
DATA_PATH = 'data/'

def main():
    try:
        ChatBot().run()

        session = LongPollSession(bot=Bot())
        while not session.authorization(token_path=PATH + DATA_PATH + 'token.txt'):
            continue
        session.process_updates()

    except Exception:
        error_text = traceback.format_exc()
        open(PATH + 'error.log', 'w').write(error_text)
        print(error_text)

def bot_debug():
    bot = Bot()
    while True:
        command = raw_input('command: ').lower()
        args = ('command ' + raw_input('args: ')).split(' ')
        try: print eval('bot.' + command + '(' + str(args) + ')')
        except Exception as e: print 'error! ' + str(e)

if __name__ == '__main__':
    main()
    #bot_debug()
