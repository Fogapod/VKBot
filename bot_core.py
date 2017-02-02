# -*- coding: utf-8 -*-
from threading import Thread
import requests
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
        return ' '.join(words)
        
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
        self.run_bot = True
        self.update_processing = None
        self.running = False

    def __exit__(self):
        self.run_message_long_poll_process = False
        self.message_long_poll_response = []
        exit()

    def authorization(self, login= '', password= '', logout=False):
        token_path = '/storage/emulated/0/Git/ChatBot_UI/data/token.txt'
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

    def _make_message_long_poll_url(self, keep_ts=False):
        """
        :keep_ts:
            использовать значение ts, полученное в результате события {ts: 12345, updates: []} 
            (предполагается, что все поля mlpd заполнены)
        Возвращает: готовый url для осуществления long poll запроса
        """
        if keep_ts:
            self.mlpd['ts'] = keep_ts
        else: 
            self.mlpd = vkr.get_message_long_poll_data()

        if self.mlpd:
            url_pattern = 'https://{server}?act={act}&key={key}&ts={ts}&wait={w}&mode={m}&version={v}'
            url = url_pattern.format(
                server = self.mlpd['server'],
                key = self.mlpd['key'],
                ts = self.mlpd['ts'],
                act = 'a_check',
                w = 100,
                m = 130,
                v = 1
            )
            return url

    def _listen_message_long_poll(self):
        """
        Позволяет получать новые события (нужно запускать отдельным потоком)
        При получении события меняет значение переменной message_long_poll_response с None на ответ сервера
        """
        print('{decor}{txt}{decor}'.format(decor='-'*6, txt='Listening long poll'))

        while self.run_message_long_poll_process:
            if not self.message_long_poll_response:
                self.message_long_poll_response = vkr.do_message_long_poll_request(url=self.message_long_poll_url)
            else:
                # прошлый ответ ещё не обработан
                time.sleep(0.01)
    
    def _process_updates(self):
        print (__help__)
        self.mlpd = None # message_long_poll_data
        #{
        #   server: str,
        #   key: int,
        #   ts: int
        #}
        self.message_long_poll_url = self._make_message_long_poll_url()
        self.message_long_poll_process = Thread(target=self._listen_message_long_poll)
        self.message_long_poll_response = None
        self.run_message_long_poll_process = True
        self.message_long_poll_process.start()
        self.running = True

        self.last_rnd_id = 0
        self.reply_count = 0

        while self.update_processing:
            if not self.message_long_poll_response:
                time.sleep(1)
                continue

            response = json.loads(self.message_long_poll_response.content)
            try:
                self.message_long_poll_url = self._make_message_long_poll_url(keep_ts=response['ts'])
            except KeyError:
                if 'failed' in response:
                    self.mlpd = None
                    self.message_long_poll_url = self._make_message_long_poll_url()
                    self.message_long_poll_response = None
                    continue

            self.message_long_poll_response = None

            print(response)

            for update in response['updates']:
                if  update[0] == 4 and\
                    update[8] != self.last_rnd_id and\
                    update[6]:
                # response == message
                # message != last_message
                # message != ''
                    text = update[6]
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

                    text = parse_input(text, replace_vkurl=False)
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
                        text = self.stop_bot_from_message(update)

                    else:
                        text = 'Неизвестная команда. Вы можете использовать /help для получения списка команд.'
                else:
                    continue
                
                if not text:
                    continue
                
                if update[5] != u' ... ':
                    message_to_resend = update[1]
                else:
                    message_to_resend = None

                self.last_rnd_id = update[8] + 9

                vkr.send_message(
                    uid = update[3],
                    text = text + "'" if mark_msg else text,
                    forward = message_to_resend,
                    rnd_id = self.last_rnd_id
                    )
                self.reply_count += 1

                if not self.run_bot:
                    self.__exit__()
                    self.running = False
            if not self.run_bot:
                self.__exit__()
                self.running = False

    def start_bot(self):
        self.update_processing = Thread(target=self._process_updates)
        self.update_processing.start()
        while not self.running: continue
        return True

    def stop_bot(self):
        self.run_bot = False
        self.update_processing = None
        while self.running: continue
        return True

    def stop_bot_from_message(self, response):
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