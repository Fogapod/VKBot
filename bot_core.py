# -*- coding: utf-8 -*-
from threading import Thread
import time
import json
import re
import math

from utils import parse_input
import vkrequests as vkr

from __init__ import PATH
from __init__ import DATA_PATH

from __init__ import __version__
from __init__ import __author__
    
__help__ = '''
Версия: {ver}

Я умею:
*Говорить то, что вы попросите
(/say ... |/скажи ... )
*Производить математические операции
(/calculate ... |/посчитай ... ) =
*Проверять, простое ли число
(/prime ... |/простое ... ) %
*Вызывать помощь
(/help |/помощь ) ?

В конце моих сообщений ставится знак верхней кавычки'

Автор: {author}
'''.format(\
    ver = __version__, author = __author__
)


class Bot(object):
    def __init__(self):
        pass
    
    def help(self):
        return __help__
    
    def say(self, words):
        argument_required = self._argument_missing(words)
        if argument_required:
            return argument_required

        del words[0]
        text = ' '.join(words)
        return text
        
    def calculate(self, words):
        argument_required = self._argument_missing(words)
        if argument_required:
            return argument_required

        if words[0].startswith('='):
            words[0] = words[0][1:]
        else:
            del words[0]
        words = ''.join(words).lower()
        if not re.match(u'[^\d+\-*/:().,^√πe]', words) or re.match('(sqrt\(\d+\))|(pi)', words):
            words = ' ' + words + ' '
            words = re.sub(u'(sqrt)|√', 'math.sqrt', words)
            words = re.sub(u'(pi)|π', 'math.pi', words)
            words = re.sub('\^', '**', words)
            words = re.sub(',', '.', words)
            words = re.sub(':', '/', words)            
            while True:
                if '/' in words:
                    index = re.search('[^.\d]\d+[^.\de]', words)
                    if index:
                        index = index.end() - 1
                        words = words[:index] + '.' + words[index:]
                    else:
                        break
                else:
                    break
            try:
                result = str(eval(words))
            except SyntaxError:
                result = 'Ошибка [0]'
            except NameError:
                result = 'Ошибка [1]'
            except AttributeError:
                result = 'Ошибка [2]'        
            except ZeroDivisionError:
                result = 'Деление на 0'
            except OverflowError:
                result = 'Слишком большой результат'
        else:
            result = 'Не математическая операция'
        return result
            
    def prime(self, words):
        argument_required = self._argument_missing(words)
        if argument_required:
            return argument_required

        del words[0]
        input_number = ''.join(words)
        if re.match('^\d+$', input_number) and len(input_number)<=5:
            input_number = int(input_number)
            luc_number = 0
            last_luc_number = 0
            for i in range(input_number):
                if luc_number == 0:
                    luc_number = 1
                elif luc_number == 1:
                    last_luc_number = luc_number
                    luc_number = 3
                else:
                    luc_number, last_luc_number = last_luc_number + luc_number, luc_number
                            
            if input_number != 0:
                is_prime = True if (luc_number - 1) % input_number == 0 else False
                result = 'Является простым числом' if is_prime else 'Не является простым числом'
            else:
                result = '0 не является простым числом'
        else:
            result = 'Дано неверное или слишком большое значение'
        return result
        

    def _argument_missing(self, words):
        if len(words) == 1:
            return 'Команду необходимо использовать с аргументом'
        else:
            return False


class LongPollSession(Bot):
    def __init__(self):
        self.update_processing = None
        self.run_bot = False
        self.running = False
        self.reply_count = 0

    def authorization(self, login= '', password= '', logout=False):
        token_path = PATH + DATA_PATH + 'token.txt'
        authorized = False
        token = None
        if logout:
            open(token_path, 'w').close()
            return

        if not (login and password):
            try:
                with open(token_path, 'r') as token_file:
                    lines = token_file.readlines()
                    if lines:
                        token = lines[0][:-1]
            except:
                token = None
                open(token_path, 'w').close()

            if token:
                if vkr.log_in(token=token):
                    self.SELF_ID = vkr.get_user_id()
                    authorized = True
                else:
                    open(token_path, 'w').close()
        else:
            new_token = vkr.log_in(login=login, password=password)
            if new_token:
                with open(token_path, 'w') as token_file:
                    token_file.write('{}\n{}'.format(\
                        new_token, 'НИКОМУ НЕ ПОКАЗЫВАЙТЕ СОДЕРЖИМОЕ ЭТОГО ФАЙЛА'
                        )
                    )
                self.SELF_ID = vkr.get_user_id()
                authorized = True

        return authorized
    
    def _process_updates(self):
        mlpd = vkr.get_message_long_poll_data()
        last_rnd_id = 0

        self.running = True
        print('launched')
        while self.run_bot:
            try:
                response = vkr.get_message_updates(ts=mlpd['ts'],pts=mlpd['pts'])
                if response[0]:
                    updates = response[0]
                    mlpd['pts'] = response[1]
                    messages = response[2]
                else:
                    time.sleep(2)
                    continue
                print(updates)

                for message in messages['items']:
                    if message['body'] and message['random_id'] != last_rnd_id:
                        text = message['body']
                        mark_msg = True
                    else:
                        continue

                    if  text.lower() == u'ершов' or\
                        text.lower() == u'женя' or\
                        text.lower() == u'жень' or\
                        text.lower() == u'женька' or\
                        text.lower() == u'жека' or\
                        text.lower() == u'евгений' or\
                        text.lower() == u'ерш' or\
                        text.lower() == u'евгеха' or\
                        text.lower() == u'жэка':
                        text = 'А'

                    elif text.lower() == u'how to praise the sun?' or\
                         text.lower() == u'🌞':
                        text = '\\[T]/\n..🌞\n...||\n'

                    elif re.sub('^( )*', '', text).startswith('/'): 
                        text = text[1:]
                        if text.startswith('/'):
                            mark_msg = False
                            text = text[1:]

                        text = parse_input(text)
                        words = text.split()

                        if not words: 
                            words = ' '

                        if  re.match(u'(^help)|(^помощь)|(^info)|(^инфо)|(^информация)|^\?$',\
                            words[0].lower()):
                            text = self.help()

                        elif re.match(u'(^скажи)|(^say)$', words[0].lower()):
                            text = self.say(words)

                        elif re.match(u'(^посчитай)|(^calculate)|$', words[0].lower()) or\
                             words[0].startswith('='):
                            text = self.calculate(words)    

                        elif re.match(u'(^простое)|(^prime)|%$', words[0].lower()):
                            text = self.prime(words)

                        elif re.match(u'(^stop)|(^выйти)|(^exit)|(^стоп)|(^terminate)|(^завершить)|(^close)|^!$',\
                    	     words[0].lower()):
                            text = self._stop_bot_from_message(update)
                        else:
                            text = 'Неизвестная команда. Вы можете использовать /help для получения списка команд.'
                    else:
                        continue
                
                    if not text:
                        continue
                
                    if message['title'] != u' ... ':
                        message_to_resend = message['id']
                    else:
                        message_to_resend = None

                    last_rnd_id = message['random_id'] + 9

                    vkr.send_message(
                        uid = message['user_id'] if not 'chat_id' in message.keys() else None,
                        gid = None if not 'chat_id' in message.keys() else message['chat_id'],
                        text = text + "'" if mark_msg else text,
                        forward = message_to_resend,
                        rnd_id = last_rnd_id
                    )
                    self.reply_count += 1

            except Exception as e:
                print 'Bot error: ' + str(e)
                self.run_bot = False

        self.running = False
        self.reply_count = 0
        print('stopped')

    def start_bot(self):
        self.run_bot = True
        self.update_processing = Thread(target=self._process_updates)
        self.update_processing.start()
        while not self.running: continue
        return True

    def stop_bot(self):
        self.run_bot = False
        self.reply_count = 0
        while self.running: continue
        self.update_processing = None
        return True

    def _stop_bot_from_message(self, response):
        is_refused = True
        denied_text = 'Отказано в доступе'
        allowed_text = 'Завершаю программу'
        message = denied_text

        if 'from' in response[7]:
            if int(response[7]['from']) == self.SELF_ID:
                message = allowed_text
                is_refused = False
        else:
            out = False
            sum_flags = response[2]
            for flag in [512,256,128,64,32,16,8,4]:
                if sum_flags == 3 or sum_flags == 2:
                    out = True
                    break
                if sum_flags - flag <= 0:
                    continue
                else:
                    if sum_flags - flag == 3 or sum_flags - flag == 2:
                        out = True
                        break
                    else:
                        sum_flags -= flag
            if out:
                message = allowed_text
                is_refused = False

        self.run_bot = is_refused
        return message