from bot_core import Bot
from bot_core import LongPollSession

def main():
    session = LongPollSession(bot=Bot())
    while not session.authorization(token_path='data/token.txt'):
        continue

    session.process_updates()

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